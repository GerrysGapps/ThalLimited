# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, models, _
from odoo.exceptions import Warning
import datetime
import decimal
from textwrap import wrap
from odoo.addons.dynamic_cheque_print.lang import num2words


class dynamic_cheque_print_template(models.AbstractModel):
    _name = 'report.dynamic_cheque_print.dynamic_cheque_print_template'

    def _get_date(self, date):
        return datetime.datetime.strptime(str(date), '%Y-%m-%d').strftime('%d%m%Y')

    def _is_pay_acc(self, data):
        if data.get('cheque_format_id'):
            config_id = self.env['dynamic.cheque.format.configuration'].browse([data.get('cheque_format_id')[0]])
            if config_id and config_id.is_ac_pay:
                return True

    def num2words(self, data, amount_total):
        cheque_amount = amount_total
        complete_str = ''
        cheque_obj = self.env['dynamic.cheque.format.configuration']
        if not data.get('label_preview'):
            br_rec = self.env['account.payment'].browse([self._context.get('active_id')])
        else:
            br_rec = self.env['wizard.cheque.preview'].browse([data.get('id')])
        amount_total = str(amount_total).split('.')
        str1 = num2words(int(amount_total[0]), lang='en_EN')
        if len(amount_total[1]) == 1:
            amount_total[1] = amount_total[1] + '0'
        str2 = num2words(int(amount_total[1]), lang='en_EN')
        if br_rec.currency_id.name == "PKR":
            if str1 and str2 and (decimal.Decimal(cheque_amount)).as_tuple().exponent < 0:
                complete_str = str1 + ' ' + str(amount_total[1]) + '/100'
            if str1 and str2 and (decimal.Decimal(cheque_amount)).as_tuple().exponent == 0:
                complete_str = str1
        elif br_rec.currency_id.name == "USD":
            if str1 and str2:
                complete_str = str1 + ' Dollar ' + str2 + ' Cent'
        else:
            complete_str = str1 + ' and ' + str2 + ' Cent'
        if complete_str:
            complete_str += ' only'
        if data and data.get('cheque_format_id'):
            cheque_format_id = cheque_obj.browse([data.get('cheque_format_id')[0]])
            if cheque_format_id and cheque_format_id.amount_word_type == 'standard':
                complete_str = complete_str.title()
            if cheque_format_id and cheque_format_id.amount_word_type == 'capital':
                complete_str = complete_str.upper()
            if cheque_format_id and cheque_format_id.amount_word_type == 'small':
                complete_str = complete_str.lower()
        return complete_str

    def _get_word_line(self, data, record):
        num_words_list = []
        num_words = self.num2words(data, record.amount)
        config_id = self.env['dynamic.cheque.format.configuration'].browse([data.get('cheque_format_id')[0]])
        if config_id:
            if config_id.currency_name:
                if config_id.currency_name_position == 'before':
                    num_words = record.currency_id.name + ' ' + num_words
                else:
                    num_words = num_words + ' ' + record.currency_id.name
            if config_id and config_id.amount_word_type == 'standard':
                num_words = num_words.title()
            if config_id and config_id.amount_word_type == 'capital':
                num_words = num_words.upper()
            if config_id and config_id.amount_word_type == 'small':
                num_words = num_words.lower()

            if config_id.first_line_words_count > 0:
                first_array_words = str(num_words[0:config_id.first_line_words_count]).split(',')
                last_index = 0
                if len(list(str(num_words))) > config_id.first_line_words_count:
                    last_index = first_array_words[len(first_array_words) - 1]
                    first_array_words = first_array_words[:-1]
                    num_words_list.append(','.join(map(str, first_array_words)) + ',')
                else:
                    num_words_list.append(','.join(map(str, first_array_words)))
            if config_id.second_line_words_count > 0:
                if last_index > 0:
                    num_words_list.append(str(last_index) + str(num_words[config_id.first_line_words_count:(
                            config_id.first_line_words_count + config_id.second_line_words_count)]))

        if num_words_list:
            return num_words_list

    def _get_amount(self, amount, display_currency):
        if display_currency:
            fmt = "%.{0}f".format(display_currency.decimal_places)
            lang = self.env['ir.qweb.field'].user_lang()
            amount = lang.format(fmt, display_currency.round(amount),
                                 grouping=True, monetary=True).replace(r' ', u'\N{NO-BREAK SPACE}')
        return amount

    def _get_currency_position(self, data):
        config_id = self.env['dynamic.cheque.format.configuration'].browse([data.get('cheque_format_id')[0]])
        if config_id and config_id.currency_symbol and config_id.currency_symbol_position:
            return config_id.currency_symbol_position

    def _get_signatory_one(self, data):
        cheque_format_id = self.env['dynamic.cheque.format.configuration'].browse(data.get('cheque_format_id')[0])
        return [cheque_format_id.first_signatory or '', cheque_format_id.second_signatory or '',
                cheque_format_id.third_signatory or '']

    def _get_company(self, data):
        cheque_format_id = self.env['dynamic.cheque.format.configuration'].browse(data.get('cheque_format_id')[0])
        if cheque_format_id.company_name:
            return self.env['res.users'].browse([self._uid]).company_id.name

    def _draw_style(self, data, field):
        config_id = False
        style = ''
        if data.get('cheque_format_id'):
            config_id = self.env['dynamic.cheque.format.configuration'].browse([data.get('cheque_format_id')[0]])
        if config_id:
            if field == 'ac_pay':
                if config_id.is_bold_ac_pay:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_ac_pay) + 'mm;top:' + str(config_id.ac_pay_top_margin) + 'mm;left:' + str(
                        config_id.ac_pay_left_margin) + 'mm;border-top:1px solid;border-bottom:1px solid;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_ac_pay) + 'mm;top:' + str(config_id.ac_pay_top_margin) + 'mm;left:' + str(
                        config_id.ac_pay_left_margin) + 'mm;border-top:1px solid;border-bottom:1px solid;'

            elif field == 'payee_name':
                if config_id.is_bold_party_name:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_party_name) + 'mm;top:' + str(
                        config_id.party_name_top_margin) + 'mm;left:' + str(
                        config_id.party_name_left_margin) + 'mm;width:' + str(config_id.party_name_width_area) + 'mm;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_party_name) + 'mm;top:' + str(
                        config_id.party_name_top_margin) + 'mm;left:' + str(
                        config_id.party_name_left_margin) + 'mm;width:' + str(config_id.party_name_width_area) + 'mm;'

            elif field == 'cheque_date':
                if config_id.is_bold_cheque_date:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_cheque_date) + 'mm;margin-top:' + str(
                        config_id.cheque_date_top_margin) + 'mm;margin-left:' + str(
                        config_id.cheque_date_left_margin) + 'mm;letter-spacing:' + str(
                        config_id.cheque_date_spacing) + 'mm;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_cheque_date) + 'mm;margin-top:' + str(
                        config_id.cheque_date_top_margin) + 'mm;margin-left:' + str(
                        config_id.cheque_date_left_margin) + 'mm;letter-spacing:' + str(
                        config_id.cheque_date_spacing) + 'mm;'

            elif field == 'first_amt_words':
                if config_id.is_bold_amt_word_first_line:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_amt_word) + 'mm;width:' + str(
                        config_id.amt_first_word_width_area) + 'mm;top:' + str(
                        config_id.amt_word_first_line_top_margin) + 'mm;left:' + str(
                        config_id.amt_word_first_line_left_margin) + 'mm;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_amt_word) + 'mm;width:' + str(
                        config_id.amt_first_word_width_area) + 'mm;top:' + str(
                        config_id.amt_word_first_line_top_margin) + 'mm;left:' + str(
                        config_id.amt_word_first_line_left_margin) + 'mm;'

            elif field == 'second_amt_words':
                if config_id.is_bold_amt_word_second_line:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_amt_word) + 'mm;width:' + str(
                        config_id.amt_second_word_width_area) + 'mm;top:' + str(
                        config_id.amt_word_second_line_top_margin) + 'mm;left:' + str(
                        config_id.amt_word_second_line_left_margin) + 'mm;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_amt_word) + 'mm;width:' + str(
                        config_id.amt_second_word_width_area) + 'mm;top:' + str(
                        config_id.amt_word_second_line_top_margin) + 'mm;left:' + str(
                        config_id.amt_word_second_line_left_margin) + 'mm;'

            elif field == 'amt_figure':
                if config_id.is_bold_amt_figure:
                    style = 'position:absolute;font-weight:bold;font-size:' + str(
                        config_id.font_size_amt_figure) + 'mm;top:' + str(
                        config_id.amt_figure_top_margin) + 'mm;left:' + str(
                        config_id.amt_figure_left_margin) + 'mm;width:' + str(config_id.amt_figure_width_area) + 'mm;'
                else:
                    style = 'position:absolute;font-size:' + str(
                        config_id.font_size_amt_figure) + 'mm;top:' + str(
                        config_id.amt_figure_top_margin) + 'mm;left:' + str(
                        config_id.amt_figure_left_margin) + 'mm;width:' + str(config_id.amt_figure_width_area) + 'mm;'

            elif field == 'signatory_box':
                style = 'position:absolute;top:' + str(config_id.cmp_signatory_top_margin) + 'mm;left:' + str(
                    config_id.cmp_signatory_left_margin) + 'mm;width:' + str(
                    config_id.cmp_signatory_width) + 'mm;height:' + str(config_id.cmp_signatory_height) + 'mm;'
            elif field == 'company_name':
                style = 'position:absolute;font-size:' + str(config_id.font_size_company_name) + 'mm;top:' + str(
                    config_id.company_name_top_margin) + 'mm;left:' + str(config_id.company_name_left_margin) + 'mm;'
            elif field == 'first_sign':
                style = 'position:absolute;font-size:' + str(config_id.font_size_first_signatory) + 'mm;top:' + str(
                    config_id.first_signatory_top_margin) + 'mm;left:' + str(
                    config_id.first_signatory_left_margin) + 'mm;'
            elif field == 'second_sign':
                style = 'position:absolute;font-size:' + str(config_id.font_size_second_signatory) + 'mm;top:' + str(
                    config_id.second_signatory_top_margin) + 'mm;left:' + str(
                    config_id.second_signatory_left_margin) + 'mm;'
            elif field == 'third_sign':
                style = 'position:absolute;font-size:' + str(config_id.font_size_third_signatory) + 'mm;top:' + str(
                    config_id.third_signatory_top_margin) + 'mm;left:' + str(
                    config_id.third_signatory_left_margin) + 'mm;'
            elif field == 'cheque_date_counter':
                style = 'position:absolute;font-size:' + str(
                    config_id.font_size_cheque_date_counter) + 'mm;margin-top:' + str(
                    config_id.cheque_date_top_margin_counter) + 'mm;margin-left:' + str(
                    config_id.cheque_date_left_margin_counter) + 'mm;letter-spacing:' + str(
                    config_id.cheque_date_spacing_counter) + 'mm;'
            elif field == 'payee_name_counter':
                style = 'position:absolute;font-size:' + str(config_id.font_size_party_name_counter) + 'mm;top:' + str(
                    config_id.party_name_top_margin_counter) + 'mm;left:' + str(
                    config_id.party_name_left_margin_counter) + 'mm;width:' + str(
                    config_id.party_name_width_area_counter) + 'mm;'
            elif field == 'amt_figure_counter':
                style = 'position:absolute;font-size:' + str(config_id.font_size_amt_figure_counter) + 'mm;top:' + str(
                    config_id.amt_figure_top_margin_counter) + 'mm;left:' + str(
                    config_id.amt_figure_left_margin_counter) + 'mm;width:' + str(
                    config_id.amt_figure_width_area_counter) + 'mm;'
            elif field == 'sequence_number_counter':
                style = 'position:absolute;font-size:' + str(
                    config_id.font_size_cheque_sequence_counter) + 'mm;margin-top:' + str(
                    config_id.cheque_sequence_top_margin_counter) + 'mm;margin-left:' + str(
                    config_id.cheque_sequence_left_margin_counter) + 'mm;width:' + str(
                    config_id.cheque_sequence_spacing_counter) + 'mm;'
            elif field == 'printed_date_counter':
                style = 'position:absolute;font-size:' + str(
                    config_id.font_size_cheque_printed_date_counter) + 'mm;margin-top:' + str(
                    config_id.cheque_printed_date_top_margin_counter) + 'mm;margin-left:' + str(
                    config_id.cheque_printed_date_left_margin_counter) + 'mm;width:' + str(
                    config_id.cheque_printed_date_spacing_counter) + 'mm;'
            elif field == 'is_journal_name':
                style = 'position:absolute;font-size:' + str(
                    config_id.font_size_journal_name) + 'mm;margin-top:' + str(
                    config_id.journal_name_top_margin) + 'mm;margin-left:' + str(
                    config_id.journal_name_left_margin) + 'mm;width:'
            elif field == 'is_employee_name':
                style = 'position:absolute;font-size:' + str(
                    config_id.font_size_employee_name) + 'mm;margin-top:' + str(
                    config_id.employee_name_top_margin) + 'mm;margin-left:' + str(
                    config_id.employee_name_left_margin) + 'mm;width:'
        return style

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form').get('label_preview'):
            records = self.env["account.payment"].browse(data["ids"])
        else:
            records = self.env['wizard.cheque.preview'].browse(data['ids'])
        return {
            'doc_model': self.env['account.payment'],
            'docs': records,
            'draw_style': self._draw_style,
            'get_date': self._get_date,
            'get_company': self._get_company,
            'get_signatory_one': self._get_signatory_one,
            'get_word_line': self._get_word_line,
            'get_currency_position': self._get_currency_position,
            'num2words': self.num2words,
            'is_pay_acc': self._is_pay_acc,
            'get_amount': self._get_amount,
            'data': data
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
