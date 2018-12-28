from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.one
    @api.depends('amount_total')
    def _get_amount_due(self):
        self.amount_due = self.amount_total

    @api.one
    def _get_amount_residual(self):
        advance_amount = 0.0
        for line in self.account_payment_ids:
            if line.state != 'draft':
                advance_amount += line.amount
        self.amount_resisual = self.amount_total - advance_amount

    account_payment_ids = fields.One2many('account.payment', 'sale_id',
                                          string="Pay sale advanced",
                                          readonly=True)
    amount_resisual = fields.Float('Residual amount', readonly=True,
                                   compute="_get_amount_residual")
    amount_due = fields.Float('Remaining Amount', compute="_get_amount_due", store=True)

    payment_entry_ref = fields.One2many('account.payment', 'sale_id', string='Payment Reference')