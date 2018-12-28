# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models, _, fields
from odoo.exceptions import ValidationError, UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_option = fields.Selection(
        [('full', 'Full Payment without Deduction'), ('partial', 'Full Payment with Deduction')], default='full',
        required=True, string='Payment Option')
    post_diff_acc = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')],
                                     default='multi', string='Post Difference In To')
    payslip_batches = fields.Many2one('hr.payslip.run', 'Payslip Batches', store=True)
    payslip = fields.Many2one('hr.payslip', 'Payslips', store=True)
    deductions = fields.One2many('deduction.payment.line', 'payment_id')
    pay_ref = fields.Char('Ref', store=True)
    has_deduction = fields.Boolean('Deduction')
    sale_id = fields.Many2one('sale.order', "Sale", readonly=True,
                              states={'draft': [('readonly', False)]})

    purchase_id = fields.Many2one('purchase.order', "Purchase", readonly=True,
                                  states={'draft': [('readonly', False)]})
    advance_ref = fields.Boolean('Advance Ref', store=True)
    state = fields.Selection(
        selection_add=[('cancelled', _('Cancelled'))],
        help="When the payment is cancel the status id 'Cancelled'.")
    is_alternative_account_head = fields.Boolean('Alternative Head')
    account_id = fields.Many2one('account.account', string='Account Head')

    @api.multi
    def button_invoices(self):
        if self.has_deduction:
            return {
                'name': _('Paid Invoices'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', [x.invoice_id.id for x in self.deductions])],
            }
        else:
            return {
                'name': _('Paid Invoices'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', [x.id for x in self.invoice_ids])],
            }

    @api.multi
    def button_deductions(self):
        if self.has_deduction:
            view_id = self.env.ref('ga_payments_enhancement.invoice_deductions_tree_view')
        else:
            view_id = self.env.ref('ga_payments_enhancement.invoice_deductions_duplicate_tree_view')
        return {
                'name': _('Invoice Deductions'),
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'deduction.payment.line',
                'view_id': view_id.id,
                'type': 'ir.actions.act_window',
                'domain': [('payment_id', 'in', [x.payment_id.id for x in self.deductions])],
        }

    def get_atlernative_account_head(self, move_lines):
        move_lines['account_id'] = self.account_id.id
        return move_lines

    @api.multi
    def post(self):
        for rec in self:

            if rec.state != 'draft':
                raise UserError(
                    _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            if self.name == 'Draft Payment' or self.name == False:
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
            else:
                rec.name = self.name

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})

        return super(AccountPayment, self)

    # @api.multi
    # def reset_invoice_amount(self):
    #     inv_obj = self.env['account.invoice']
    #     if len(self.deductions)>0:
    #         for deduction in self.deductions:
    #             if deduction.invoice_id:
    #                 curr_inv = inv_obj.browse(deduction.invoice_id.id)
    #                 inv_obj.browse(deduction.invoice_id.id).write({'amount_paid': curr_inv.amount_paid - self.amount})
    #     return True

    @api.multi
    def cancel(self):
        if self.state=='draft':
            self.state = 'cancelled'
        else:
            super(AccountPayment, self).cancel()
            self.state = 'cancelled'
            self.name = self.name

    @api.multi
    def reset_to_draft(self):
        self.write({'state': 'draft'})
        return

    @api.multi
    def generate_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'model': 'account.payment',
            'name': 'Deductions',
            'report_type': 'qweb-pdf',
            'report_name': 'ga_payments_enhancement.report_payment_deduction',
            'report_file': 'ga_payments_enhancement.report_payment_deduction'
        }

    @api.onchange('payslip_batches')
    def fetch_total_amount_batch(self):
        amount = 0
        if self.payslip_batches:
            for payslip in self.payslip_batches.slip_ids:
                for line in payslip.line_ids:
                    if line.employee_id.address_home_id:
                        if payslip.state == 'done':
                            if (line.category_id.name).capitalize() == 'Net':
                                if line.salary_rule_id.account_credit:
                                    amount += (line.total)
                                else:
                                    raise ValidationError("Kindly define account head of this salary rule %s" % (
                                        line.salary_rule_id.name))
                        else:
                            raise ValidationError("Kindly confirm payslip inside this batch of an employee of %s" % (
                                line.employee_id.name))
                    else:
                        raise ValidationError("You must define related partner of %s" % (line.employee_id.name))
        self.amount = amount

    @api.onchange('payslip')
    def fetch_total_amount_payslip(self):
        amount = 0
        if self.payslip:
            if self.payslip.employee_id.address_home_id.id:
                self.partner_id = self.payslip.employee_id.address_home_id.id
                self.partner_type = 'supplier'
            else:
                raise ValidationError("You must define related partner of %s" % (self.payslip.employee_id.name))

            for line in self.payslip.line_ids:
                if self.payslip.state == 'done':
                    if (line.category_id.name).capitalize() == 'Net':
                        if line.salary_rule_id.account_credit:
                            amount += (line.total)
                        else:
                            raise ValidationError(
                                "Kindly define account head of this salary rule %s" % (line.salary_rule_id.name))
                else:
                    raise ValidationError("Kindly confirm payslip of this employee of")
        self.amount = amount

    def pay_payslip_batch(self, move_lines, payslip):
        hr_payslip = self.env['hr.payslip']
        hr_payslip_run = self.env['hr.payslip.run']
        for line in payslip.line_ids:
            if line.employee_id.address_home_id and payslip.state == 'done' and (
                    line.category_id.name).capitalize() == 'Net':
                if line.salary_rule_id.account_credit:
                    move_lines['account_id'] = (line.salary_rule_id.account_credit.id or '')
                    move_lines['debit'] = (line.total or '')
                    move_lines['partner_id'] = (line.employee_id.address_home_id.id)
                    hr_payslip.browse(payslip.id).write({'payslip_status': 'Paid', 'payment_ref': self.id})
                    hr_payslip_run.browse(self.payslip_batches.id).write(
                        {'batch_status': 'Paid', 'payment_ref': self.id})
                    return move_lines
                else:
                    raise ValidationError(
                        "Kindly define account head of this salary rule %s" % (line.salary_rule_id.name))

    def pay_individual_payslip(self, move_lines):
        hr_payslip = self.env['hr.payslip']
        for line in self.payslip.line_ids:
            if line.employee_id.address_home_id:
                if (line.category_id.name).capitalize() == 'Net':
                    if line.salary_rule_id.account_credit:
                        account_id = line.salary_rule_id.account_credit.id
                        move_lines['account_id'] = account_id
                        hr_payslip.browse(self.payslip.id).write({'payslip_status': 'Paid', 'payment_ref': self.id})
                        return move_lines
                    else:
                        raise ValidationError(
                            "Kindly define account head of this salary rule %s" % (line.salary_rule_id.name))

    # def pay_loan(self, move_lines, loan_id):
    #     loan_account_id = self.env['employee.loan.details'].search([('id', '=', loan_id)])[0]
    #     if loan_account_id:
    #         move_lines['account_id'] = loan_account_id.employee_loan_account.id
    #         return move_lines
    #     else:
    #         raise ValidationError("Kindly define account head of this Loan")

    @api.multi
    def make_group_data(self):
        vals = {}
        for deduction in self.deductions:
            writeoff = []
            for line in deduction.writeoff_account_id_.writeoff_line:
                writeoff.append({'account_id': line.account_id.id,
                                 'description': line.description or '',
                                 'amount_in_percent': line.amount_in_percent or '',
                                 'amount_payment': line.amount_payment or '',
                                 'currency_id': line.currency_id and line.currency_id.id or '',
                                 'type': line.type,
                                 'taxes': line.taxes.id,
                                 'taxable_income': line.taxable_income})

            vals.update({
                str(deduction.invoice_id.id): {'receiving_amt': deduction.receiving_amt,
                                               'handling': 'reconcile',
                                               'writeoff_account_id': writeoff,
                                               'payment_difference': deduction.payment_difference}
            })
        data = {
            str(self.partner_id.id): {
                'partner_type': 'customer' if self.payment_type == 'inbound' else 'supplier',
                'inv_val': vals,
                'memo': self.communication,
                'total': self.amount,
                'partner_id': self.partner_id.id,
                'payment_method_id': False

            }
        }
        return data

    @api.onchange('payment_option')
    def onchange_payment_option(self):
        if self.payment_option == 'full':
            self.payment_difference_handling = 'open'
            self.post_diff_acc = 'single'
        else:
            self.payment_difference_handling = 'reconcile'
            self.post_diff_acc = 'multi'

    @api.onchange('writeoff_multi_acc_ids')
    @api.multi
    def onchange_writeoff_multi_accounts(self):
        if self.writeoff_multi_acc_ids:
            diff_amount = sum([line.amount for line in self.writeoff_multi_acc_ids])
            self.amount = self.invoice_ids and self.invoice_ids[0].residual - diff_amount

    @api.multi
    def _create_payment_entry(self, amount):
        group_data = {}
        """ Create a journal entry corresponding to a payment, if the payment
            references invoice(s) they are reconciled.
            Return the journal entry.
        """
        # If group data
        if len(self.deductions) > 0 and self.advance_ref!=True:
            group_data = {'group_data': self.make_group_data()}
        context = dict(self._context)
        context.update(group_data)

        if 'group_data' in context:
            aml_obj = self.env['account.move.line']. \
                with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and \
                    all([x.currency_id == self.invoice_ids[0].currency_id
                         for x in self.invoice_ids]):
                # If all the invoices selected share the same currency,
                # record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id
            move = self.env['account.move'].create(self._get_move_vals())
            p_id = str(self.partner_id.id)
            for inv in context.get('group_data')[p_id]['inv_val']:
                current_invoice = {}
                amt = 0
                if ('is_customer' in context and context.get('is_customer')) or context.get('group_data')[p_id][
                    'partner_type'] == 'customer':
                    amt = -(context.get('group_data')[p_id]['inv_val'][inv]['receiving_amt'])
                else:
                    amt = context.get('group_data')[p_id]['inv_val'][inv]['receiving_amt']

                debit, credit, amount_currency, currency_id = \
                    aml_obj.with_context(date=self.payment_date). \
                        _compute_amount_fields(amt, self.currency_id,
                                               self.company_id.currency_id)
                # Write line corresponding to invoice payment
                counterpart_aml_dict = \
                    self._get_shared_move_line_vals(debit,
                                                    credit, amount_currency,
                                                    move.id, False)

                current_invoice = self.env['account.invoice'].browse(int(inv))
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(current_invoice))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                counterpart_aml_dict['name'] += ' ' + (self.pay_ref or '')
                # Reconcile with the invoices and write off
                if 'is_customer' in context and context.get('is_customer') or context.get('group_data')[p_id][
                    'partner_type'] == 'customer':
                    handling = context.get('group_data')[p_id]['inv_val'][inv]['handling']  # noqa
                    payment_difference = context.get('group_data')[p_id]['inv_val'][inv][
                        'payment_difference']  # noqa
                    writeoff_account_id = context.get('group_data')[p_id]['inv_val'][inv][
                        'writeoff_account_id']  # noqa
                    if handling == 'reconcile' and payment_difference:
                        for writeoff_account in writeoff_account_id:
                            writeoff_line = \
                                self._get_shared_move_line_vals(0, 0, 0, move.id,
                                                                False)
                            debit_wo, credit_wo, amount_currency_wo, currency_id = \
                                aml_obj.with_context(date=self.payment_date)._compute_amount_fields(
                                    writeoff_account['amount_payment'], self.currency_id,
                                    self.company_id.currency_id)
                            writeoff_line['name'] = writeoff_account['description']
                            writeoff_line['account_id'] = writeoff_account['account_id']
                            writeoff_line['debit'] = writeoff_account['amount_payment']
                            writeoff_line['credit'] = 0
                            writeoff_line['amount_currency'] = amount_currency_wo
                            writeoff_line['currency_id'] = currency_id
                            writeoff_line = aml_obj.create(writeoff_line)
                            if counterpart_aml['debit']:
                                counterpart_aml['debit'] += credit_wo - debit_wo
                            if counterpart_aml['credit']:
                                counterpart_aml['credit'] += debit_wo - credit_wo
                            counterpart_aml['amount_currency'] -= \
                                amount_currency_wo
                else:
                    handling = context.get('group_data')[p_id]['inv_val'][inv]['handling']  # noqa
                    payment_difference = context.get('group_data')[p_id]['inv_val'][inv][
                        'payment_difference']  # noqa
                    writeoff_account_id = context.get('group_data')[p_id]['inv_val'][inv][
                        'writeoff_account_id']  # noqa
                    if handling == 'reconcile' and payment_difference:
                        for writeoff_account in writeoff_account_id:
                            writeoff_line = \
                                self._get_shared_move_line_vals(0, 0, 0, move.id,
                                                                False)
                            debit_wo, credit_wo, amount_currency_wo, currency_id = \
                                aml_obj.with_context(date=self.payment_date)._compute_amount_fields(writeoff_account['amount_payment'], self.currency_id,
                                               self.company_id.currency_id)
                            writeoff_line['name'] = writeoff_account['description']
                            writeoff_line['account_id'] = writeoff_account['account_id']
                            writeoff_line['debit'] = 0
                            writeoff_line['credit'] = writeoff_account['amount_payment']
                            writeoff_line['amount_currency'] = amount_currency_wo
                            writeoff_line['currency_id'] = currency_id
                            writeoff_line = aml_obj.create(writeoff_line)
                            if counterpart_aml['credit']:
                                counterpart_aml['credit'] += credit_wo - debit_wo
                            if counterpart_aml['debit']:
                                counterpart_aml['debit'] += debit_wo - credit_wo
                            counterpart_aml['amount_currency'] -= \
                                amount_currency_wo

                current_invoice.register_payment(counterpart_aml)
                # Write counterpart lines
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict = \
                    self._get_shared_move_line_vals(credit, debit,
                                                    -amount_currency, move.id,
                                                    False)
                liquidity_aml_dict.update(
                    self._get_liquidity_move_line_vals(-amount))
                aml_obj.create(liquidity_aml_dict)

            move.post()
            return move

        elif self.payslip or self.payslip_batches or self.advance_ref:
            counterpart_aml = {}
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            invoice_currency = False

            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(amount, self.currency_id,
                                               self.company_id.currency_id)

            move = self.env['account.move'].create(self._get_move_vals())

            # Write line corresponding to invoice payment
            counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml_dict['name'] += ' ' + (self.pay_ref or '')

            if self.payslip_batches:
                for payslip in self.payslip_batches.slip_ids:
                    counterpart_aml_dict = self.pay_payslip_batch(counterpart_aml_dict, payslip)
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)

            elif self.payslip:
                counterpart_aml_dict = self.pay_individual_payslip(counterpart_aml_dict)
                counterpart_aml = aml_obj.create(counterpart_aml_dict)

            # elif self.loan_id:
            #     counterpart_aml_dict = self.pay_loan(counterpart_aml_dict, self.loan_id.id)
            #     counterpart_aml = aml_obj.create(counterpart_aml_dict)

            elif self.is_alternative_account_head and self.account_id:
                counterpart_aml_dict = self.get_atlernative_account_head(counterpart_aml_dict)
                counterpart_aml = aml_obj.create(counterpart_aml_dict)

            else:
                counterpart_aml = aml_obj.create(counterpart_aml_dict)

            if self.advance_ref:
                for deduction in self.deductions:
                    if self.payment_type == 'inbound':
                        woff_amount = deduction.receiving_amt
                    else:
                        woff_amount = - deduction.receiving_amt
                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                        date=self.payment_date)._compute_amount_fields(woff_amount, self.currency_id,
                                               self.company_id.currency_id)
                    writeoff_line['name'] = deduction.description
                    writeoff_line['account_id'] = deduction.writeoff_account_id.id
                    writeoff_line['debit'] = debit_wo
                    writeoff_line['credit'] = credit_wo
                    writeoff_line['amount_currency'] = amount_currency_wo
                    writeoff_line['currency_id'] = currency_id
                    writeoff_line = aml_obj.create(writeoff_line)
                    if counterpart_aml['debit']:
                        counterpart_aml['debit'] += credit_wo - debit_wo
                    if counterpart_aml['credit']:
                        counterpart_aml['credit'] += debit_wo - credit_wo
                    counterpart_aml['amount_currency'] -= amount_currency_wo

            # Write counterpart lines
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

            move.post()
            return move
        else:
            return super(AccountPayment, self)._create_payment_entry(amount)
