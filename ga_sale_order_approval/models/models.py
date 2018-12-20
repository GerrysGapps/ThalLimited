# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning


class InheritProducttemplate(models.Model):
    _inherit = 'product.template'

    min_sale_price = fields.Float('Minimum Sale Price')
    max_sale_price = fields.Float('Maximum Sale Price')

class InheritSaleOrder(models.Model):
    _inherit = "sale.order"
    management_approved = fields.Boolean(default=True)

    @api.multi
    def action_management_approved(self):
        if self.env.user.has_group('ga_sale_order_approval.so_approval') == True:
            self.write ({'management_approved':True})
        else:
            raise Warning(_('You are not authorize to approve this quotation'))

    @api.multi
    def _check_approval_need(self):
        for line in self.order_line:
            if (line.price_unit < line.product_id.product_tmpl_id.min_sale_price or
                    line.price_unit > line.product_id.product_tmpl_id.max_sale_price):
                return True
        return False
    @api.multi
    def _check_approval_need_created(self,lines):
        for line in lines:
            product_product = self.env['product.product'].search([('id','=',line[2]['product_id'])])
            product_tempate = self.env['product.template'].search([('id','=',product_product.product_tmpl_id.id)])
            if (line[2]['price_unit'] < product_tempate.min_sale_price or
                    line[2]['price_unit'] > product_tempate.max_sale_price):
                return True
            # return 'You can only sale' + str(line.product_id.name) + ' within this price range ' +str(line.product_id.product_tmpl_id.min_sale_price)
            # + '-' + str(line.product_id.product_tmpl_id.max_sale_price)

    @api.multi
    def _action_confirm(self):
        if not self.management_approved:
            raise Warning(_('Management Approval Needed'))
        res = super(InheritSaleOrder, self)._action_confirm()
        return res

    @api.model
    def create(self, vals):
        if 'order_line' in vals:
            if self._check_approval_need_created(vals['order_line']):
                vals['management_approved']= False
            else:
                vals['management_approved'] = True
        created_id = super(InheritSaleOrder, self).create(vals)
        return created_id

    @api.multi
    def write(self, vals):
        write_id = super(InheritSaleOrder, self).write(vals)
        if 'order_line' in vals:
            if self._check_approval_need():
                vals['management_approved']=False
                self.write({'management_approved':False})
            else:
                self.write({'management_approved': True})
        return write_id
