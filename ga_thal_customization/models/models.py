# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning
import datetime

class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char('Customer Code')
    customer_category = fields.Many2one('customer.category',string='Customer Category')
    sales_office = fields.Many2one('sale.office', string='Sales Office')
    distribution_channel = fields.Many2one('distribution.channel',string='Distribution Channel')
    fax_no = fields.Char ('Fax No')
    ntn_no = fields.Char ('NTN No')
    srtn = fields.Char('SRTN No')
    cnic_no = fields.Char('CNIC No')
    credit_limit = fields.Float('Credit Limits')
    credit_days = fields.Integer('Credit Days')
    year_in_bussiness = fields.Integer('Years in Business')
    sales_history = fields.Char('Sales History')
    sales_projections = fields.Char('Sales Projections')
    comment_on_credit_performance = fields.Text('Comment on credit performance including overdue history:')
    rationale_for_credit_request = fields.Text('Rationale for credit request:')

class CustomerCategory(models.Model):
    _name = 'customer.category'

    name = fields.Char ('Description')

class DistributionChannel(models.Model):
    _name = 'distribution.channel'

    name =fields.Char('Distribution Channel')


class SalesOffice(models.Model):
    _name = 'sale.office'

    name = fields.Char('Description')


class InheritProducttemplate(models.Model):
    _inherit = 'product.template'

    old_material_no = fields.Char('Old Material No')
    default_code = fields.Char('Product Code', index=True)


class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    conversion_rate = fields.Float('Conversion Rate')
    type = fields.Char('Type')
    credit_limit = fields.Boolean('Credit Limit')

    @api.one
    def _check_customer_validations(self):
        if not self.partner_id.sales_office:
            raise Warning(_('Please Provide Customr Sales Office'))
        if not self.partner_id.customer_category:
            raise Warning(_('Please Provide Customr Category'))
        if not self.partner_id.distribution_channel:
            raise Warning(_('Please Provide Customer Distribution Channel'))
        if not self.partner_id.cnic_no:
            raise Warning(_('Please Provide Customer CNIC No'))
        if not self.partner_id.credit_limit:
            raise Warning(_('Please Provide Customer Credit Limit'))
        if not self.partner_id.credit_days:
            raise Warning(_('Please Provide Customer Credit Days'))
        if not self.partner_id.year_in_bussiness:
            raise Warning(_('Please Provide Customer Year in Business'))
        if not self.partner_id.sales_history:
            raise Warning(_('Please Provide Customer Sales History'))
        if not self.partner_id.sales_projections:
            raise Warning(_('Please Provide Customer Sales Projection'))
        if not (self.partner_id.street or self.partner_id.street2) :
            raise Warning(_('Please Provide Customer Address'))

    @api.multi
    def _action_confirm(self):
        self._check_customer_validations()
        if not self.management_approved:
            raise Warning(_('Management Approval Needed'))
        res = super(InheritSaleOrder, self)._action_confirm()
        return res

    @api.multi
    def action_cancel(self):
        if self.opportunity_id:
            res = super(InheritSaleOrder, self).action_cancel()
            if self.type == 'Revised':
                sale_order_object_actual = self.env['sale.order'].search(
                    [('opportunity_id', '=', self.opportunity_id.id),
                     ('state', '!=', 'cancel'), ('type', '=', 'Revised')], order='write_date DESC', limit=1)
                self.env["crm.lead"].browse(self.opportunity_id.id).write(
                    {'actual_revenue': sale_order_object_actual.amount_total})
        return res

    # @api.onchange('opportunity_id')
    # def on_change_opp(self):
    #     if self.env.context.get('default_type', False) =='Expected Quotation':
    #         self.type = 'Expected Quotation'
    #     else:
    #         self.type = 'Revised'


    @api.model
    def create(self, vals):
        if self.env.context.get('default_type', False) == 'Expected Quotation':
            sale_order = self.env['sale.order'].search([('opportunity_id', '=', vals['opportunity_id']),('type', '=', 'Expected Quotation')])
            if len(sale_order)>0:
                raise Warning(_('Quotation For Expected Revenue is already exit'))
            else:
                created_id = super(InheritSaleOrder, self).create(vals)
                return created_id
        else:
            created_id = super(InheritSaleOrder, self).create(vals)
        if vals['pricelist_id']:
            price_list_object = self.env['product.pricelist'].search([('id','=',vals['pricelist_id'])])
            if vals['conversion_rate'] and 'PKR' not in price_list_object.currency_id:
                self.env['res.currency.rate'].sudo().create({'name': datetime.datetime.now().date(), 'currency_id':
                    price_list_object.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
            return created_id


    @api.multi
    def write(self, vals):
        write_id = super(InheritSaleOrder, self).write(vals)
        if 'pricelist_id' in vals:
            price_list_object = self.env['product.pricelist'].search([('id','=',vals['pricelist_id'])])
            if vals['conversion_rate'] and 'PKR' not in price_list_object.currency_id:
                self.env['res.currency.rate'].sudo().create({'name': datetime.datetime.now().date(), 'currency_id':
                    price_list_object.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
        return write_id



