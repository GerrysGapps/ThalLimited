from odoo import api, models, _, fields


class Writeoff(models.Model):
    _name = "write.off_"
    _rec_name = 'total_writeoff_amount'

    invoice_balance = fields.Float(string="Invoice Balance")
    receive_amount = fields.Float(string="Receive Amount")
    diff_amount = fields.Float(string="Difference Amount")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    total_writeoff_amount = fields.Float(string="Write-Off Total", compute='cal_total_writeoff_amount')
    writeoff_line = fields.One2many('write.off.lines_', 'write_off_id', string='Write-Off Accounts')

    @api.one
    @api.depends('writeoff_line.amount_payment')
    def cal_total_writeoff_amount(self):
        sales_wht = 0.0
        amount = 0.0
        for line in self.writeoff_line:
            amount += line.amount_payment
        self.total_writeoff_amount = amount
        self.total_sales_wht_amount = sales_wht


class WriteoffLines(models.Model):
    _name = 'write.off.lines_'
    _rec_name = 'description'

    write_off_id = fields.Many2one('write.off_', string='Write-Offs')
    account_id = fields.Many2one('account.account', string="Difference Account",
                                 domain=[('deprecated', '=', False)], copy=False, required="1")
    description = fields.Char('Description')
    amount_in_percent = fields.Float(string='Amount(%)', digits=(16, 2))
    amount_payment = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    type = fields.Selection(
        [('sales_WHT', 'Sales Tax Withheld'), ('income_WHT', 'Income Tax Withheld'), ('other', 'Other')], string='Type')
    taxes = fields.Many2one('account.tax', string='Taxes')
    taxable_income = fields.Float('Taxable Income')


class DeductionsPaymentLine(models.Model):
    _name = "deduction.payment.line"
    _rec_name = 'invoice_id'

    payment_id = fields.Many2one('account.payment', string="Payment",
                                 required=True)
    invoice_id = fields.Many2one('account.invoice', string="Customer Invoice",
                                 )
    balance_amt = fields.Float("Invoice Balance")
    receiving_amt = fields.Float("Receive Amount")
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Payment Type')
    payment_difference = fields.Float(string='Difference Amount',readonly=True)
    writeoff_account_id_ = fields.Many2one('write.off_', string="Post Difference In", copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Account",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)
    description = fields.Char('Description')
    amount_in_percent = fields.Float(string='Amount(%)', digits=(16, 2))


class writeoff_accounts(models.Model):
    _name = 'writeoff.accounts'

    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False, required="1")
    name = fields.Char('Description')
    amt_percent = fields.Float(string='Amount(%)', digits=(16, 2))
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_id = fields.Many2one('account.payment', string='Payment Record')


