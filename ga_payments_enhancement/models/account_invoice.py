from odoo import api, models, _, fields
from odoo.exceptions import ValidationError, UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    amount_paid = fields.Float('Amount Paid', default=0.0, compute='compute_paid_amount', store=True)

    @api.model
    def delete_actwindow(self):
        aw = self.env.ref('account.action_account_payment_from_invoices')
        aw.unlink()

    @api.one
    @api.depends('residual')
    def compute_paid_amount(self):
        self.amount_paid += self.residual
