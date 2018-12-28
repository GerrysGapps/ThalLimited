# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import math
from odoo import api, fields, models, _
from odoo.tools import float_round, float_compare
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from . import amount_to_text_en

INV_TO_PARTN = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or
# goes out
INV_TO_PAYM_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}

clear_count = 0


class InvoiceCustomerPaymentLine(models.TransientModel):
    _name = "invoice.customer.payment.line"
    _rec_name = 'invoice_id'

    invoice_id = fields.Many2one('account.invoice', string="Customer Invoice",
                                 required=True)
    partner_id = fields.Many2one('res.partner', string="Customer Name",
                                 required=True)
    balance_amt = fields.Float("Invoice Balance", required=True)
    wizard_id = fields.Many2one('account.register.payments', string="Wizard")
    receiving_amt = fields.Float("Receive Amount", required=True)
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Payment Type')
    payment_difference = fields.Float(string='Difference Amount',
                                      readonly=True)
    handling = fields.Selection([('FPWOD', 'Full Payment Without Deductions'),
                                 ('PPWOD', 'Partial Payment Without Deductions'),
                                 ('FPWD', 'Full Payment With Deductions'),
                                 ('PPWD', 'Partial Payment With Deductions'),
                                 ],
                                string="Action",
                                copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Account",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)
    writeoff_account_id_ = fields.Many2one('write.off', string="Account", copy=False)

    @api.onchange('receiving_amt')
    def _onchange_amount(self):
        self.check_amount_in_words = AmountToTextFractional(self.receiving_amt)
        self.payment_difference = self.balance_amt - self.receiving_amt

    @api.onchange('handling')
    def get_receive_amount(self):
        self.env.cr.execute("""Delete from write_off where invoice_id=%s"""%(self.invoice_id.id))
        if self.handling == 'FPWOD':
            self.receiving_amt = self.balance_amt
        else:
            self.receiving_amt = 0.0


class InvoicePaymentLine(models.TransientModel):
    _name = "invoice.vendor.payment.line"
    _rec_name = 'invoice_id'

    handling = fields.Selection([('FPWOD', 'Full Payment Without Deductions'),
                                 ('PPWOD', 'Partial Payment Without Deductions'),
                                 ('FPWD', 'Full Payment With Deductions'),
                                 ('PPWD', 'Partial Payment With Deductions'),
                                 ],
                                default='open',
                                string="Action",
                                copy=False)
    invoice_id = fields.Many2one('account.invoice', string="Supplier Invoice",
                                 )
    partner_id = fields.Many2one('res.partner', string="Supplier Name",
                                 required=True)
    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Payment Type')
    balance_amt = fields.Float("Balance Amount", required=True)
    wizard_id = fields.Many2one('account.register.payments', string="Wizard")
    paying_amt = fields.Float("Pay Amount", required=True)
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_difference = fields.Float(string='Difference Amount')
    writeoff_account_id_ = fields.Many2one('write.off', string="Account", copy=False)

    @api.onchange('paying_amt')
    def _onchange_amount(self):
        self.check_amount_in_words = AmountToTextFractional(self.paying_amt)
        self.payment_difference = self.balance_amt - self.paying_amt

    @api.onchange('handling')
    def get_receive_amount(self):
        self.env.cr.execute("""Delete from write_off where invoice_id=%s""" % (self.invoice_id.id))
        if self.handling == 'FPWOD':
            self.receiving_amt = self.balance_amt
        else:
            self.receiving_amt = 0.0


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    ref = fields.Char(string='Reference')

    @api.depends('invoice_customer_payments.receiving_amt')
    def _compute_customer_pay_total(self):
        self.total_customer_pay_amount = sum(line.receiving_amt for line in
                                             self.invoice_customer_payments)

    @api.depends('invoice_payments.paying_amt')
    def _compute_pay_total(self):
        self.total_pay_amount = sum(line.paying_amt for line in
                                    self.invoice_payments)

    is_auto_fill = fields.Char(string="Auto-Fill Pay Amount")
    invoice_payments = fields.One2many('invoice.vendor.payment.line', 'wizard_id',
                                       string='Payments')
    is_customer = fields.Boolean(string="Is Customer?")
    invoice_customer_payments = \
        fields.One2many('invoice.customer.payment.line',
                        'wizard_id', string='Receipts')
    cheque_amount = fields.Float("Check Amount")
    total_pay_amount = fields.Float("Total Invoices",
                                    compute='_compute_pay_total')
    total_customer_pay_amount = fields.Float("Total Invoices", compute='_compute_customer_pay_total')
    show_communication_field = fields.Boolean(compute='show_communication_field_')

    @api.one
    @api.depends('cheque_amount')
    def show_communication_field_(self):
       self.show_communication_field = True

    @api.multi
    def check_invoice_payments(self, invoice_id):
        payment_obj = self.env['account.payment']
        self.env.cr.execute("""select payment_id from account_invoice_payment_rel where invoice_id=%s"""%(invoice_id))
        payments =  self.env.cr.dictfetchall()
        if len(payments)>0:
            for payment in payments:
                curr_payment = payment_obj.search([('id','=',payment['payment_id']),('state','=', 'draft')])
                if len(curr_payment)>0:
                    return False
                else:
                    return True
        else:
            return True


    @api.multi
    def update_receive_amount(self):
        ctx = self._context.copy()
        if self.is_customer:
            for line in self.invoice_customer_payments:
                payment_diff = line.balance_amt - (line.balance_amt - line.writeoff_account_id_.total_writeoff_amount)
                if line.handling == 'FPWD':
                    line.write({'receiving_amt': line.balance_amt - line.writeoff_account_id_.total_writeoff_amount,
                                'payment_difference': payment_diff})
                if line.handling == 'FPWOD':
                    line.write({'receiving_amt': line.balance_amt - line.writeoff_account_id_.total_writeoff_amount,
                                'payment_difference': payment_diff})
            self.write({'cheque_amount': self.total_customer_pay_amount})
        else:
            for line in self.invoice_payments:
                payment_diff = line.balance_amt - (line.balance_amt - line.writeoff_account_id_.total_writeoff_amount)
                if line.handling == 'FPWD':
                    line.write({'paying_amt': line.balance_amt - line.writeoff_account_id_.total_writeoff_amount,
                                'payment_difference': payment_diff})
                if line.handling == 'FPWOD':
                    line.write({'paying_amt': line.balance_amt - line.writeoff_account_id_.total_writeoff_amount,
                                'payment_difference': payment_diff})
            self.write({'cheque_amount': self.total_pay_amount})
        return {
            'name': _("Batch Payments"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_id': self.id,
            'res_model': 'account.register.payments',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(_("Program error: wizard action executed without"
                              " active_model or active_ids in context."))
        if active_model != 'account.invoice':
            raise UserError(_("Program error: the expected model for this"
                              " action is 'account.invoice'. The provided one"
                              " is '%d'.") % active_model)

        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register payments for open"
                              " invoices"))
        for rec in invoices:
            if any([inv.partner_id != rec.partner_id for inv in invoices if rec != inv]):
                if rec.type == 'out_invoice':
                    raise UserError(_("You can only register payments of same customers"))
                elif rec.type == 'in_invoice':
                    raise UserError(_("You can only register payments of same vendors"))
        if any(INV_TO_PARTN[inv.type] != INV_TO_PARTN[invoices[0].type]
               for inv in invoices):
            raise UserError(_("You cannot mix customer invoices and vendor"
                              " bills in a single payment."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they"
                              " must use the same currency."))

        rec = {}
        if 'batch' in context and context.get('batch'):
            lines = []
            if INV_TO_PARTN[invoices[0].type] == 'customer':
                for inv in invoices:
                    if self.check_invoice_payments(inv.id):
                        lines.append((0, 0, {'partner_id': inv.partner_id.id,
                                             'invoice_id': inv.id,
                                             'balance_amt': inv.residual or inv.amount_paid or 0.0 ,
                                             'receiving_amt': inv.residual or inv.amount_paid or 0.0 ,
                                             'payment_difference': inv.residual or inv.amount_paid or 0.0,
                                             'handling': 'FPWOD'
                                             }))
                    else:
                        raise UserError(_("Payment already created of this %s invoice in draft state"%(inv.number or inv.name)))
                rec.update({'invoice_customer_payments': lines,
                            'is_customer': True,
                            'show_communication_field': True})
            else:
                for inv in invoices:
                    if self.check_invoice_payments(inv.id):
                        lines.append((0, 0, {'partner_id': inv.partner_id.id,
                                             'invoice_id': inv.id,
                                             'balance_amt': inv.residual or inv.amount_paid or 0.0,
                                             'paying_amt': inv.residual or inv.amount_paid or 0.0,
                                             'payment_difference': inv.residual or inv.amount_paid or 0.0,
                                             'handling': 'FPWOD'
                                             }))
                    else:
                        raise UserError(_("Payment already created of this %s bill in draft state" % (inv.number or inv.name)))
                rec.update({'invoice_payments': lines, 'is_customer': False,'show_communication_field': True})
        else:
            # Checks on received invoice records
            if any(INV_TO_PARTN[inv.type] != INV_TO_PARTN[invoices[0].type]
                   for inv in invoices):
                raise UserError(_("You cannot mix customer invoices and vendor"
                                  " bills in a single payment."))

        total_amount = sum(inv.residual *
                           INV_TO_PAYM_SIGN[inv.type]
                           for inv in invoices)
        rec.update({
            'amount': abs(total_amount),
            'currency_id': invoices[0].currency_id.id,
            'payment_type': total_amount > 0 and 'inbound' or 'outbound',
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': INV_TO_PARTN[invoices[0].type],
        })
        return rec

    def get_payment_batch_vals(self, inv_payment=False, group_data=None):
        if group_data:
            res = {
                'journal_id': self.journal_id.id,
                'payment_method_id': 'payment_method_id' in group_data and group_data[
                    'payment_method_id'] or self.payment_method_id.id,  # noqa
                'payment_date': self.payment_date,
                'communication': group_data['memo'],
                'pay_ref': group_data['pay_ref'],
                'invoice_ids': [(4, int(inv), None)
                                for inv in list(group_data['inv_val'])],
                'payment_type': self.payment_type,
                'amount': group_data['total'],
                'currency_id': self.currency_id.id,
                'partner_id': int(group_data['partner_id']),
                'partner_type': group_data['partner_type'],
                'deductions': group_data['deductions'],
                'has_deduction': True if len(group_data['deductions'])>0 else False
            }
            if self.payment_method_id == \
                    self.env.ref('account_check_printing.'
                                 'account_payment_method_check'):
                res.update({
                    'check_amount_in_words': group_data['total_check_amount_in_words'] or '',  # noqa
                })
            return res

    def get_multi_accounts_and_writoff_lines(self, writeoff_lines):
        multi_accounts = []
        writeoff_lines_ = []

        for line in writeoff_lines:
            vals = {'account_id': line.account_id.id,
                    'description': line.description or '',
                    'amount_in_percent': line.amount_in_percent or '',
                    'amount_payment': line.amount_payment or '',
                    'currency_id': line.currency_id and line.currency_id.id or '',
                    'type': line.type,
                    'taxes': line.taxes.id,
                    'taxable_income': line.taxable_income}
            writeoff_lines_.append((0, 0, vals))
            multi_accounts.append(vals)

        return multi_accounts, writeoff_lines_

    def create_writeoff(self, invoice_id, balance_amount, receiving_amount, payment_difference, total_writeoff_amount,
                        writeoff_lines):
        rec_id = self.env['write.off_'].create({'invoice_id': invoice_id,
                                                'invoice_balance': balance_amount,
                                                'receive_amount': receiving_amount,
                                                'diff_amount': payment_difference,
                                                'writeoff_line': writeoff_lines,
                                                'total_writeoff_amount': total_writeoff_amount,
                                                })
        return rec_id.id

    @api.multi
    def make_payments(self):
        ref = ''
        # Make group data either for Customers or Vendors
        precision = self.env['decimal.precision'].precision_get('Account')
        context = dict(self._context or {})
        data = {}
        deductions = []
        if self.is_customer:
            context.update({'is_customer': True})
            if float_compare(
                    self.total_customer_pay_amount,
                    self.cheque_amount,
                    precision_digits=precision) != 0:
                raise ValidationError(_('Verification Failed! Total Invoices'
                                        ' Amount and Check amount does not'
                                        ' match!'))
            for paym in self.invoice_customer_payments:

                if paym.receiving_amt > 0:
                    paym.payment_difference = paym.balance_amt - paym.receiving_amt  # noqa
                    partner_id = str(paym.invoice_id.partner_id.id)
                    if partner_id in data:
                        old_total = data[partner_id]['total']
                        memo = self.communication

                        # Build memo value
                        if self.ref:
                            ref += self.ref + '-' + \
                                  str(paym.invoice_id.number)
                        else:
                            ref += str(paym.invoice_id.number)
                        # Calculate amount in words
                        amount_total = old_total + paym.receiving_amt
                        amount_word = AmountToTextFractional(amount_total)

                        res = self.get_multi_accounts_and_writoff_lines(paym.writeoff_account_id_.writeoff_line)

                        rec_id = self.create_writeoff(paym.invoice_id.id, paym.balance_amt, paym.receiving_amt,
                                                      paym.payment_difference,
                                                      paym.writeoff_account_id_.total_writeoff_amount, res[1])
                        deductions.append((0, 0, {'invoice_id': paym.invoice_id.id,
                                                  'balance_amt': paym.balance_amt,
                                                  'receiving_amt': paym.receiving_amt,
                                                  'payment_difference': paym.payment_difference,
                                                  'writeoff_account_id_': rec_id
                                                  }))

                        data[partner_id].update({
                            'partner_id': partner_id,
                            'partner_type': INV_TO_PARTN[paym.invoice_id.type],
                            'total': amount_total,
                            'memo': memo,
                            'pay_ref': ref,
                            'deductions': deductions,
                            'payment_method_id': paym.payment_method_id and
                                                 paym.payment_method_id.id or False,
                            'total_check_amount_in_words': amount_word
                        })
                        data[partner_id]['inv_val'].update({
                            str(paym.invoice_id.id): {
                                'receiving_amt': paym.receiving_amt,
                                'handling': 'reconcile' if (
                                        paym.handling == 'FPWD' or paym.handling == 'FPWOD') else 'open',
                                'payment_difference': paym.payment_difference,
                                'writeoff_account_id': res[0]
                            }
                        })
                    else:
                        # Build memo value
                        res = self.get_multi_accounts_and_writoff_lines(paym.writeoff_account_id_.writeoff_line)

                        rec_id = self.create_writeoff(paym.invoice_id.id, paym.balance_amt, paym.receiving_amt,
                                                      paym.payment_difference,
                                                      paym.writeoff_account_id_.total_writeoff_amount, res[1])
                        deductions.append((0, 0, {'invoice_id': paym.invoice_id.id,
                                                  'balance_amt': paym.balance_amt,
                                                  'receiving_amt': paym.receiving_amt,
                                                  'payment_difference': paym.payment_difference,
                                                  'writeoff_account_id_': rec_id
                                                  }))

                        memo = self.communication

                        # Build memo value
                        if self.ref:
                            ref += self.ref + '-' + \
                                  str(paym.invoice_id.number)+' '
                        else:
                            ref += str(paym.invoice_id.number)+' '
                        # Calculate amount in words
                        amount_word = AmountToTextFractional(
                            paym.receiving_amt)
                        data.update({
                            partner_id: {
                                'partner_id': partner_id,
                                'partner_type': INV_TO_PARTN[
                                    paym.invoice_id.type],
                                'total': paym.receiving_amt,
                                'payment_method_id':
                                    paym.payment_method_id and
                                    paym.payment_method_id.id or False,
                                'total_check_amount_in_words': amount_word,
                                'memo': memo,
                                'pay_ref': ref,
                                'deductions': deductions,
                                'inv_val': {str(paym.invoice_id.id): {
                                    'receiving_amt': paym.receiving_amt,
                                    'handling': 'reconcile' if (
                                            paym.handling == 'FPWD' or paym.handling == 'FPWOD') else 'open',
                                    'payment_difference':
                                        paym.payment_difference,
                                    'writeoff_account_id': res[0]
                                }
                                }
                            }
                        })
        else:
            context.update({'is_customer': False})
            if float_compare(
                    self.total_pay_amount,
                    self.cheque_amount,
                    precision_digits=precision) != 0:
                raise ValidationError(_('Verification Failed! Total Invoices'
                                        ' Amount and Check amount does not'
                                        ' match!'))
            for paym in self.invoice_payments:
                if paym.paying_amt > 0:
                    partner_id = str(paym.invoice_id.partner_id.id)
                    if partner_id in data:
                        res = self.get_multi_accounts_and_writoff_lines(paym.writeoff_account_id_.writeoff_line)

                        rec_id = self.create_writeoff(paym.invoice_id.id, paym.balance_amt, paym.paying_amt,
                                                      paym.payment_difference,
                                                      paym.writeoff_account_id_.total_writeoff_amount, res[1])
                        deductions.append((0, 0, {'invoice_id': paym.invoice_id.id,
                                                  'balance_amt': paym.balance_amt,
                                                  'receiving_amt': paym.paying_amt,
                                                  'payment_difference': paym.payment_difference,
                                                  'writeoff_account_id_': rec_id
                                                  }))
                        old_total = data[partner_id]['total']
                        # Build memo value
                        memo = self.communication

                        # Build memo value
                        if self.ref:
                            ref += self.ref + '-' + \
                                  str(paym.invoice_id.number)
                        else:
                            ref += str(paym.invoice_id.number)
                        # Calculate amount in words
                        amount_total = old_total + paym.paying_amt
                        amount_word = AmountToTextFractional(amount_total)
                        data[partner_id].update({'partner_id': partner_id,
                                                 'partner_type': INV_TO_PARTN[paym.invoice_id.type],  # noqa
                                                 'total': amount_total,
                                                 'memo': memo,
                                                 'pay_ref': ref,
                                                 'deductions': deductions,
                                                 'total_check_amount_in_words':
                                                     amount_word,
                                                 'inv_val': {str(paym.invoice_id.id): {
                                                     'paying_amt': paym.paying_amt,
                                                     'handling': 'reconcile' if (
                                                             paym.handling == 'FPWD' or paym.handling == 'FPWOD') else 'open',
                                                     'payment_difference':
                                                         paym.payment_difference,
                                                     'writeoff_account_id': res[0]
                                                 }
                                                 }})
                    else:
                        # Build memo value
                        memo = self.communication

                        # Build memo value
                        if self.ref:
                            ref = self.ref + '-' + \
                                  str(paym.invoice_id.number)
                        else:
                            ref = str(paym.invoice_id.number)
                        # Calculate amount in words
                        res = self.get_multi_accounts_and_writoff_lines(paym.writeoff_account_id_.writeoff_line)

                        rec_id = self.create_writeoff(paym.invoice_id.id, paym.balance_amt, paym.paying_amt,
                                                      paym.payment_difference,
                                                      paym.writeoff_account_id_.total_writeoff_amount, res[1])
                        deductions.append((0, 0, {'invoice_id': paym.invoice_id.id,
                                                  'balance_amt': paym.balance_amt,
                                                  'receiving_amt': paym.paying_amt,
                                                  'payment_difference': paym.payment_difference,
                                                  'writeoff_account_id_': rec_id
                                                  }))
                        amount_word = AmountToTextFractional(paym.paying_amt)
                        data.update({
                            partner_id:
                                {'partner_id': partner_id,
                                 'partner_type': INV_TO_PARTN[paym.invoice_id.type],  # noqa
                                 'total': paym.paying_amt,
                                 'total_check_amount_in_words': amount_word,
                                 'memo': memo,
                                 'pay_ref': ref,
                                 'deductions': deductions,
                                 'inv_val': {str(paym.invoice_id.id): {
                                     'paying_amt': paym.paying_amt,
                                     'handling': 'reconcile' if (
                                             paym.handling == 'FPWD' or paym.handling == 'FPWOD') else 'open',
                                     'payment_difference':
                                         paym.payment_difference,
                                     'writeoff_account_id': res[0]
                                 }
                                 }
                                 }
                        })
        # Update context
        context.update({'group_data': data})
        # Making partner wise payment
        payment_ids = []
        for p in list(data):
            payment = self.env['account.payment'].with_context(context). \
                create(self.get_payment_batch_vals(group_data=data[p]))
            payment_ids.append(payment.id)
            # payment.post()

        view_id = self.env['ir.model.data'].get_object_reference(
            'ga_payments_enhancement',
            'view_account_supplier_payment_tree_nocreate')[1]
        return {
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('id','in',%s)]" % (payment_ids),
            'context': {'group_by': 'partner_id'}
        }

    @api.multi
    def auto_fill_payments(self):
        ctx = self._context.copy()
        for wiz in self:
            if wiz.is_customer:
                if wiz.invoice_customer_payments:
                    for payline in wiz.invoice_customer_payments:
                        payline.write({'receiving_amt': payline.balance_amt,
                                       'payment_difference': 0.0})
                ctx.update({'reference': wiz.communication or '',
                            'journal_id': wiz.journal_id.id})
            else:
                if wiz.invoice_payments:
                    for payline in wiz.invoice_payments:
                        payline.write({'paying_amt': payline.balance_amt})
                ctx.update({'reference': wiz.communication or '',
                            'journal_id': wiz.journal_id.id})

        return {
            'name': _("Batch Payments"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_id': self.id,
            'res_model': 'account.register.payments',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }


# amountInt: int value
# returns: string of amountInt converted to english text,
#           with decimals converted to cent fractional
def AmountToTextFractional(amountInt):
    amount_word = amount_to_text_en.amount_to_text(
        math.floor(amountInt), lang='en', currency='')
    amount_word = amount_word.replace(' and Zero Cent', '')
    decimals = amountInt % 1
    if decimals >= 10 ** -2:
        amount_word += _(' and %s/100') % str(int(round(
            float_round(decimals * 100, precision_rounding=1))))
    return amount_word
