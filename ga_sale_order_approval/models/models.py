# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning
from odoo.addons import decimal_precision as dp

class QuotationReject(models.TransientModel):
    _name = 'quotation.rejection'
    _description = 'Get Quotation Rejection Reason'

    description = fields.Text('Reject Reason')

    @api.multi
    def action_reject_reason_apply(self):
        leads = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        leads.write({'rejection_reason': self.description,'approval_status': 'Rejected','approval_level':0})

class inheritCompany(models.Model):

    _inherit = 'res.company'
    approval_groups = fields.One2many('approval.groups','company_id',string='Approval Groups')

class approvallist(models.Model):
    _name = 'approval.groups'

    group = fields.Many2one('res.groups', 'Group')
    company_id = fields.Many2one('res.company', ondelete='cascade')
    sequence= fields.Integer('Sequence')


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    min_price = fields.Float('Min Price', digits=dp.get_precision('Product Price'))
    max_price = fields.Float('Max Price', digits=dp.get_precision('Product Price'))
    fixed_price = fields.Float('Fixed Price', digits=dp.get_precision('Product Price'))


class InheritProducttemplate(models.Model):
    _inherit = 'product.template'

    min_sale_price = fields.Float('Minimum Sale Price')
    max_sale_price = fields.Float('Maximum Sale Price')


class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    rejection_reason = fields.Text('Rejection Reason', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    approval_level = fields.Integer('Approval Level',track_visibility='onchange')
    approval_required = fields.Integer('Required Approval(s)', compute='_compute_approval_required')
    approval_level_temp = fields.Integer('Done Approval(s)',compute='_compute_approval_temp')
    approval_status = fields.Selection([
        ('Rejected', 'Rejected'),
        ('Sale', 'Sale Order'),
        ('Ready To Send', 'Ready To Send'),
        ('Waiting For Approval', 'Waiting For Approval'),
        ('draft', 'Quotation'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    management_approved = fields.Boolean(default=True)

    @api.one
    @api.depends('approval_status')
    def _compute_approval_required(self):
        if self.approval_status =='Waiting For Approval':
            # compute approval required.
            self.approval_required = self.check_approval_limit(self.env.user.company_id.id)[0]+1
        if self.approval_status =='draft':
            self.approval_required = 0

    @api.one
    @api.depends('approval_level')
    def _compute_approval_temp(self):
        if self.approval_level:
            self.approval_level_temp = self.approval_level
        else:
            self.approval_level_temp = 0

    @api.multi
    def reject_quotation(self):
        if not self. _check_already_approve():
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'quotation.rejection',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            raise Warning(_('Quotation has already approved now you can not reject it'))

    @api.multi
    def action_send_for_approval(self):
        self.write({'approval_status': 'Waiting For Approval'})


    @api.one
    def check_approval_limit(self,company_id):
        self.env.cr.execute("""select max(sequence) as max_limit from approval_groups where company_id=%s"""%(company_id))
        max_limit = self.env.cr.dictfetchall()[0]['max_limit']
        return max_limit


    @api.multi
    def _check_already_approve(self):
        for group in self.env.user.company_id.approval_groups:
            user_group = self.env['res.groups'].search([('users.id', '=', self.env.uid)])
            if user_group:
                for val in user_group:
                    if val.id == group.group.id and self.approval_level == group.sequence+1:
                        return True
        return False

    @api.multi
    def action_management_approved(self):
        user_belong_gorups = False
        print(self._check_already_approve())
        if not self._check_already_approve():
            if self.env.user.company_id.approval_groups:
                for group in self.env.user.company_id.approval_groups:
                    user_group = self.env['res.groups'].search([('users.id', '=', self.env.uid)])
                    if user_group:
                        for val in user_group:
                            if val.id == group.group.id and self.approval_level == group.sequence:
                                self.write({'approval_level': self.approval_level+1})
                                user_belong_gorups =True
            if user_belong_gorups == True:
                if self.check_approval_limit(self.env.user.company_id.id)[0] == self.approval_level-1:
                    self.write({'management_approved': True, 'approval_status': 'Ready To Send'})
            else:
                raise Warning(_('You are not authorize to approve this quotation'))

        else:
            raise Warning(_('Qoutation Already Aprroved'))

    @api.multi
    def _check_approval_need(self):
        status =False
        for line in self.order_line:
            if self.pricelist_id:
                product_pricelist_records = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', self.pricelist_id.id),
                     ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                if len(product_pricelist_records)>0:
                    for product_obj in product_pricelist_records:
                        if (line.price_unit < product_obj.min_price or
                                line.price_unit > product_obj.max_price):
                           status = True
                else:
                    raise Warning(_('Please Define '+ str(line.product_id.product_tmpl_id.name) + ' in Pricelist'))
        return status

    @api.multi
    def _check_approval_need_created(self,pricelist_id ,lines):
        status = False
        for line in lines:
            if pricelist_id:
                product_product = self.env['product.product'].search([('id','=',line[2]['product_id'])])
                product_template = self.env['product.template'].search([('id','=',product_product.product_tmpl_id.id)])
                product_pricelist_records = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', pricelist_id),
                     ('product_tmpl_id', '=',  product_template.id)])
                if product_pricelist_records:
                    for product_obj in product_pricelist_records:
                        if (line[2]['price_unit'] < product_obj.fixed_price or
                                line[2]['price_unit'] > product_obj.max_price):
                           status =True
                else:
                    raise Warning( _('Please Define ' +product_template.name + ' in Pricelist'))
        return status

    @api.model
    def create(self, vals):
        if 'order_line' in vals:
            if self._check_approval_need_created(vals['pricelist_id'],vals['order_line']):
                vals['management_approved'] = False
                vals['approval_level'] = 0
            else:
                vals['management_approved'] = True
                vals['approval_status'] = 'Ready To Send'
        created_id = super(InheritSaleOrder, self).create(vals)
        return created_id

    @api.multi
    def write(self, vals):
        write_id = super(InheritSaleOrder, self).write(vals)
        if 'order_line' in vals or 'pricelist_id' in vals:
            if self._check_approval_need():
                self.write({'management_approved':False,'approval_level':0,'approval_status': 'draft'})
            else:
                self.write({'management_approved': True,'approval_level':0,'approval_status': 'Ready To Send'})
        return write_id
