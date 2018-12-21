from odoo import api, fields, models, _


class field_account_payment(models.Model):
    _inherit = 'account.payment'
    
    check_cash = fields.Boolean(string="Cash Cheque")
    company_bank_cheque = fields.Boolean(string="Bank/Company Cheque")
    to_journal = fields.Boolean(string='To Journal', default=True)