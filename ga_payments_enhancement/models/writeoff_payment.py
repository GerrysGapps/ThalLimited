import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class Writeoff(models.TransientModel):
    _name = "write.off"
    _rec_name = 'total_writeoff_amount'

    invoice_balance = fields.Float(string="Invoice Balance")
    cheque_amount = fields.Float(string='Cheque Amount')
    receive_amount = fields.Float(string="Receive Amount", compute='cal_receive_amount')
    actual_receive_amount = fields.Float(string="Actual Receive Amount")
    diff_amount = fields.Float(string="Difference Amount")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    total_writeoff_amount = fields.Float(string="Write-Off Total", compute='cal_total_writeoff_amount', default=0.0)
    total_sales_wht_amount = fields.Float(string="Total Sales WHT", compute='cal_total_writeoff_amount', default=0.0)
    context_used = fields.Boolean('Context Used')
    handling = fields.Selection([('FPWOD', 'Full Payment Without Deductions'),
                                 ('PPWOD', 'Partial Payment Without Deductions'),
                                 ('FPWD', 'Full Payment With Deductions'),
                                 ('PPWD', 'Partial Payment With Deductions'),
                                 ],
                                default='open',
                                string="Action",
                                copy=False)
    writeoff_line = fields.One2many('write.off.lines', 'write_off_id', string='Write-Off Accounts')

    @api.depends('total_writeoff_amount')
    @api.multi
    def cal_receive_amount(self):
        self.receive_amount = self.invoice_balance - self.total_writeoff_amount

    @api.model
    def default_get(self, fields):
        context = self.env.context.get('details')
        res = super(Writeoff, self).default_get(fields)
        writeoff_lines = []
        res.update({'invoice_balance': context['balance_amount'],
                    'diff_amount': context['diff_amount'],
                    'invoice_id': context['invoice_id'],
                    'cheque_amount': context['cheque_amount'],
                    'handling': context['handling'],
                    'actual_receive_amount': context['receive_amount']
                    })

        partner_obj = self.env['res.partner'].search([('id', '=', context['partner_id'])])

        if self.receive_amount < context['balance_amount']:
            if str(partner_obj.till_date) < str(datetime.now().date()):
                amount_pay_total = context['receive_amount'] / (
                        100 - partner_obj.use_after_expiry.amount) * 100
                writeoff_lines.append((0, 0, {'account_id': partner_obj.use_after_expiry.account_id.id,
                                              'description': partner_obj.use_after_expiry.account_id.name,
                                              'amount_in_percent': partner_obj.use_after_expiry.amount,
                                              'amount_payment': amount_pay_total or 0.0,
                                              }))

            else:
                amount_pay_total = self.receive_amount / (
                        100 - self.invoice_id.partner_id.income_tax_withheld.amount) * 100
                writeoff_lines.append(
                    (0, 0, {'account_id': partner_obj.income_tax_withheld.account_id.id,
                            'description': partner_obj.income_tax_withheld.account_id.name,
                            'amount_in_percent': partner_obj.income_tax_withheld.amount,
                            'amount_payment': amount_pay_total or 0.0,
                            }))

        res.update({'writeoff_line': writeoff_lines})
        return res

    @api.one
    @api.depends('writeoff_line.amount_payment')
    def cal_total_writeoff_amount(self):
        sales_wht = 0.0
        amount = 0
        for line in self.writeoff_line:
            if line.type == 'sales_WHT':
                sales_wht += line.amount_payment
            amount += line.amount_payment
        self.total_writeoff_amount = amount
        self.receive_amount = self.invoice_balance - amount
        self.total_sales_wht_amount = sales_wht

    @api.constrains('diff_amount')
    def check_writeoff_total(self):
        if self.total_writeoff_amount > self.diff_amount:
            raise ValidationError(_("Difference amount must be less than or equal to total of write-off amount"))
        return True


class WriteoffLines(models.TransientModel):
    _name = 'write.off.lines'
    _rec_name = 'description'

    write_off_id = fields.Many2one('write.off', string='Write-Offs')
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

    @api.onchange('taxable_income','amount_in_percent')
    def calc_taxable_income(self):
        if self.taxable_income:
            self.amount_payment = self.taxable_income * (self.amount_in_percent / 100)

    @api.onchange('type')
    def get_tax_id(self):
        if self.type:
            if self.type == 'income_WHT':
                if str(self.write_off_id.invoice_id.partner_id.till_date) < str(datetime.now().date()):
                    self.taxes = self.write_off_id.invoice_id.partner_id.use_after_expiry.id
                else:
                    self.taxes = self.write_off_id.invoice_id.partner_id.income_tax_withheld.id

    @api.onchange('taxes')
    def cal_amount_in_percent(self):
        if self.taxes:
            record = self.env['account.tax'].search([('id', '=', self.taxes.id)])
            self.description = record.name
            self.amount_in_percent = record.amount
            self.account_id = record.account_id

    @api.onchange('amount_in_percent')
    @api.multi
    def _onchange_amount_in_percent(self):
        if self.amount_in_percent and self.amount_in_percent > 0:
            if self.type == 'sales_WHT':
                if self.write_off_id.handling == 'FPWD':
                    tax_amount = self.write_off_id.invoice_id.amount_tax
                    self.amount_payment = math.ceil(tax_amount * self.amount_in_percent / 100)

                elif self.write_off_id.handling == 'PPWD':
                    net_amount = (self.write_off_id.actual_receive_amount / self.write_off_id.invoice_id.amount_untaxed) * (
                            self.write_off_id.invoice_id.amount_tax * self.amount_in_percent / 100)
                    self.amount_payment = math.ceil(net_amount)

            elif self.type == 'income_WHT':
                if self.write_off_id.receive_amount:
                    if self.write_off_id.handling == 'FPWD':
                        self.amount_payment = math.ceil(
                            self.write_off_id.invoice_balance * self.amount_in_percent / 100)
                    elif self.write_off_id.handling == 'PPWD':
                        net_amount = ((self.write_off_id.actual_receive_amount +self.write_off_id.total_sales_wht_amount )/ (100 - self.amount_in_percent)* 100)
                        self.amount_payment = math.ceil(net_amount * (self.amount_in_percent / 100))
