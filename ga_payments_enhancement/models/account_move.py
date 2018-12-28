from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one('sale.order', readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', readonly=True)
