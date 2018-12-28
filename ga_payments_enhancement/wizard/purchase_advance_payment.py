# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, exceptions, _
from odoo import http
import odoo.addons.decimal_precision as dp
import math
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class PurchaseAdvancePaymentWizard(models.TransientModel):
    _name = "purchase.advance.payment.wiz"

    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    amount_total = fields.Monetary('Amount Total', readonly=True)
    tax = fields.Float('Tax Amount', readonly=True)
    amount_advance = fields.Monetary('Amount advanced', required=True,
                                  digits=dp.get_precision('Product Price'))
    date = fields.Date("Date", required=True,
                       default=fields.Date.context_today)
    exchange_rate = fields.Float("Exchange rate", digits=(16, 6), default=1.0,
                                 readonly=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    currency_amount = fields.Float("Curr. amount", digits=(16, 2),
                                   readonly=True)
    payment_ref = fields.Char("Ref.")
    pay_date = fields.Date('Date', default=datetime.today())
    writeoff_option = fields.Boolean('Write-Off Into Multiple Account Heads')
    writeoff_multi_acc_ids = fields.One2many('purchase.multiple.writeoff', 'register_id', string='Write-Off Accounts')
    type = fields.Selection([('Full Payment Without Write-Off', 'Full Payment Without Write-Off'),
                             ('Full Payment With Write-Off', 'Full Payment With Write-Off'),
                             ('Partial Payment Without Write-Off', 'Partial Payment Without Write-Off'),
                             ('Partial Payment With Write-Off', 'Partial Payment With Write-Off'),
                             ], string='Type')
    writeoff_total = fields.Float(string='Write-Off Total')

    @api.constrains('amount_advance')
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))
        if self.env.context.get('active_id', False):
            order = self.env["purchase.order"]. \
                browse(self.env.context['active_id'])
            if self.amount_advance > order.amount_resisual:
                raise exceptions.ValidationError(_("Amount of advance is "
                                                   "greater than residual "
                                                   "amount on sale"))

    def cal_writeoff_sum(self):
        _sum = 0
        for line in self.writeoff_multi_acc_ids:
            _sum += line.amount_payment
        return _sum or 0

    @api.onchange('writeoff_multi_acc_ids')
    @api.multi
    def onchange_writeoff_multi_accounts(self):
        if self.writeoff_multi_acc_ids and self.type != 'Partial Payment With Write-Off':
            self.amount_advance = self.amount_total - self.cal_writeoff_sum()

    @api.model
    def default_get(self, fields):
        res = super(PurchaseAdvancePaymentWizard, self).default_get(fields)
        purchase_ids = self.env.context.get('active_ids', [])
        if not purchase_ids:
            return res
        purchase_id = purchase_ids[0]

        purchase = self.env['purchase.order'].browse(purchase_id)

        amount_total = purchase.amount_due
        tax = purchase.amount_tax

        if 'amount_total' in fields:
            res.update({'amount_total': amount_total,
                        'tax': tax,
                        'type': 'Full Payment Without Write-Off',
                        'amount_advance': amount_total})

        return res

    def create_payment_voucher(self,partner_id,journal_id,amount,ref,pay_date,writeoff_lines, purchase_id):
        sequence_code = 'account.payment.supplier.invoice'
        name = self.env['ir.sequence'].with_context(ir_sequence_date=pay_date).next_by_code(sequence_code)
        payment_obj = self.env['account.payment']
        payment_res = {
            'purchase_id': purchase_id,
            'advance_ref': True,
            'payment_type': 'outbound',
            'partner_id': partner_id.id,
            'partner_type': 'supplier',
            'journal_id': journal_id.id,
            'company_id': partner_id.company_id.id,
            'payment_date': fields.datetime.now(),
            'amount': amount,
            'name': name,
            'communication': ref,
            'state': 'draft',
            'payment_difference_handling': 'reconcile',
            'payment_method_id': self.env.
                ref('account.account_payment_method_manual_in').id,
            'deductions': writeoff_lines,
        }
        payment = payment_obj.create(payment_res)
        payment.post()

    @api.multi
    def make_advance_payment(self):
        """Create customer paylines and validates the payment"""
        if self.amount_advance > self.amount_total:
            raise ValidationError("You are not allowed to register payment more than PO amount.")
        purchase_obj = self.env['purchase.order']

        purchase_ids = self.env.context.get('active_ids', [])
        if purchase_ids:
            purchase_id = purchase_ids[0]
            purchase = purchase_obj.browse(purchase_id)
            writeoff_lines = []

            if self.type == 'Full Payment With Write-Off' or 'Partial Payment With Write-Off':
                for account in self.writeoff_multi_acc_ids:
                    writeoff_lines.append((0, 0, {
                        'description': account.name,
                        'amount_in_percent': account.amt_percent,
                        'receiving_amt': account.amount_payment,
                        'writeoff_account_id': account.writeoff_account_id.id
                    }))
                self.create_payment_voucher(purchase.partner_id, self.journal_id, self.amount_advance,
                                            self.payment_ref, self.pay_date, writeoff_lines,purchase.id)

                purchase.write({'amount_due': 0 if self.type == 'Full Payment With Write-Off' else self.amount_total - self.amount_advance-self.cal_writeoff_sum()})

            elif self.type == 'Full Payment Without Write-Off' or 'Partial Payment Without Write-Off':
                self.create_payment_voucher(purchase.partner_id, self.journal_id, self.amount_advance, self.payment_ref,
                                            self.pay_date, writeoff_lines,purchase.id)
                purchase.write({'amount_due': self.amount_total - self.amount_advance})

        return {
            'type': 'ir.actions.act_window_close',
        }


class writeoff(models.TransientModel):
    _name = 'purchase.multiple.writeoff'

    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False, required="1")
    name = fields.Char('Description')
    amt_percent = fields.Float(string='Amount(%)', digits=(16, 2))
    amount_payment = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    register_id = fields.Many2one('purchase.advance.payment.wiz', string='Register Record')
    type = fields.Selection(
        [('sales_WHT', 'Sales Tax Withheld'), ('income_WHT', 'Income Tax Withheld'), ('other', 'Other')], string='Type')
    taxes = fields.Many2one('account.tax', string='Taxes')

    @api.onchange('taxes')
    def calculate_amount_percent(self):
        if self.taxes:
            record = self.env['account.tax'].search([('id', '=', self.taxes.id)])
            self.name = record.name
            self.amt_percent = record.amount
            self.writeoff_account_id = record.account_id

    @api.onchange('amt_percent')
    @api.multi
    def _onchange_amt_percent(self):
        if self.amt_percent and self.amt_percent > 0:
            if self.register_id.type == 'Partial Payment With Write-Off':
                if self.type == 'sales_WHT':
                    tax_amount = self.register_id.tax
                    self.amount_payment = math.ceil(tax_amount * self.amt_percent / 100)

                elif self.type == 'income_WHT':
                    if self.register_id.amount_total:
                        net_amount = (self.register_id.amount_advance / (100 - self.amt_percent)) * self.amt_percent
                        self.amount_payment = math.ceil(net_amount)

            else:
                if self.type == 'sales_WHT':
                    tax_amount = self.register_id.tax
                    self.amount_payment = math.ceil(tax_amount * self.amt_percent / 100)

                elif self.type == 'income_WHT':
                    if self.register_id.amount_total:
                        net_amount = self.register_id.amount_total * self.amt_percent / 100
                        self.amount_payment = math.ceil(net_amount)
