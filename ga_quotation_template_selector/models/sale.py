from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def action_quotation_send(self):
        result = super(SaleOrder, self).action_quotation_send()
        template_id = self.env['mail.template'].search([('company_id_ga', '=', self.env.user.company_id.id),('model_id.model', '=', 'sale.order'),
                                                        ('name', 'ilike', 'Send quotation')])
        result['context']['default_template_id'] = template_id.id
        return result


class EmailTemplate(models.Model):
    _inherit = "mail.template"
    
    company_id_ga = fields.Many2one('res.company', 'Company')