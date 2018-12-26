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

from openerp import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
import base64
import os, glob
import os.path
import platform

if platform.system() != 'Windows':
    from wand.image import Image


class dynamic_cheque_format_configuration(models.Model):
    _name = 'dynamic.cheque.format.configuration'

    @api.model
    def _get_report_paperformat_id(self):
        xml_id = self.env['ir.actions.report'].search([('report_name', '=',
                                                            'dynamic_cheque_print.dynamic_cheque_print_template')])
        if not xml_id or not xml_id.paperformat_id:
            raise Warning('Someone has deleted the reference paperformat of report.Please Update the module!')
        return xml_id.paperformat_id.id

    paper_format_id = fields.Many2one('report.paperformat', string="Paper Format", default=_get_report_paperformat_id)
    name = fields.Char(string="Cheque Format")
    # cheque Height-Width Configuration
    cheque_height = fields.Float(string="Height", default=80)
    cheque_width = fields.Float(string="Width", default=350)
    # ac_pay Configuration
    is_bold_ac_pay = fields.Boolean('Bold')
    is_ac_pay = fields.Boolean(string="A/c Pay", default=True)
    ac_pay_top_margin = fields.Float(string="Top Margin", default=0)
    ac_pay_left_margin = fields.Float(string="Left Margin", default=400)
    font_size_ac_pay = fields.Float(string="Font Size", default=5)
    # cheque Date Configuration
    is_bold_cheque_date = fields.Boolean('Bold')
    cheque_date_top_margin = fields.Float(string="Top Margin", default=3)
    cheque_date_left_margin = fields.Float(string="Left Margin", default=460)
    font_size_cheque_date = fields.Float(string="Font Size", default=6)
    cheque_date_spacing = fields.Float(string="Character Spacing", default=10)
    # Party's/Payee Name Configuration
    is_bold_party_name = fields.Boolean('Bold')
    party_name_top_margin = fields.Float(string="Top Margin", default=35)
    party_name_left_margin = fields.Float(string="Left Margin", default=260)
    party_name_width_area = fields.Float(string="Width", default=180)
    font_size_party_name = fields.Float(string="Font Size", default=6)
    # Amount in words Configuration

    font_size_amt_word = fields.Float(string="Font Size", default=6)
    is_bold_amt_word_first_line = fields.Boolean('Bold')
    amt_word_first_line_top_margin = fields.Float(string="First Line Top Margin", default=50)
    amt_word_first_line_left_margin = fields.Float(string="First Line Left Margin", default=250)
    amt_first_word_width_area = fields.Float(string="First Line Width", default=150)
    first_line_words_count = fields.Integer(string="No. of words in 1st line", default=52)
    amt_word_second_line_top_margin = fields.Float(string="Second Line Top Margin", default=60)
    amt_word_second_line_left_margin = fields.Float(string="Second Line Left Margin", default=230)
    is_bold_amt_word_second_line = fields.Boolean('Bold')
    amt_second_word_width_area = fields.Float(string="Second Line Width", default=160)
    second_line_words_count = fields.Integer(string="No. of words in 2nd line", default=100)
    currency_name = fields.Boolean(string="Currency Name", default=True)
    currency_name_position = fields.Selection([('before', 'Before'), ('after', 'After')],
                                              string="Currency Name Position",
                                              default='before')
    amount_word_type = fields.Selection([('standard', 'Standard'), ('capital', 'All Capital'), ('small', 'All Small')],
                                        default='standard', string="Amount in Word Type")
    # Amount in Figure Configuration

    font_size_amt_figure = fields.Float(string="Font Size", default=6)
    is_bold_amt_figure = fields.Boolean('Bold')
    amt_figure_top_margin = fields.Float(string="Top Margin", default=50)
    amt_figure_left_margin = fields.Float(string="Left Margin", default=470)
    amt_figure_width_area = fields.Float(string="Width", default=45)
    currency_symbol = fields.Boolean(string="Currency Symbol", default=True)
    currency_symbol_position = fields.Selection([('before', 'Before'), ('after', 'After')],
                                                string="Currency Symbol Position",
                                                default='before')

    # cheque Counter Part Sequence Configuration
    is_sequence_configration = fields.Boolean(string="Sequence Configuration", default=True)
    cheque_sequence_top_margin_counter = fields.Float(string="Top Margin", default=3)
    cheque_sequence_left_margin_counter = fields.Float(string="Left Margin", default=154)
    font_size_cheque_sequence_counter = fields.Float(string="Font Size", default=4)
    cheque_sequence_spacing_counter = fields.Float(string="Width", default=60)

    # cheque Counter Part Date Configuration 
    is_date_configration = fields.Boolean(string="Counter Date", default=True)
    cheque_date_top_margin_counter = fields.Float(string="Top Margin", default=27)
    cheque_date_left_margin_counter = fields.Float(string="Left Margin", default=170)
    font_size_cheque_date_counter = fields.Float(string="Font Size", default=3)
    cheque_date_spacing_counter = fields.Float(string="Character Spacing", default=2)

    # Party's/Payee Name Counter Part Configuration
    is_payee_name = fields.Boolean(string="Payee Name", default=True)
    party_name_top_margin_counter = fields.Float(string="Top Margin", default=22)
    party_name_left_margin_counter = fields.Float(string="Left Margin", default=140)
    party_name_width_area_counter = fields.Float(string="Width", default=60)
    font_size_party_name_counter = fields.Float(string="Font Size", default=4)

    # Amount in Figure Counter Part Configuration
    is_amount = fields.Boolean(string="Amount Counter")
    font_size_amt_figure_counter = fields.Float(string="Font Size", default=4)
    amt_figure_top_margin_counter = fields.Float(string="Top Margin", default=60)
    amt_figure_left_margin_counter = fields.Float(string="Left Margin", default=180)
    amt_figure_width_area_counter = fields.Float(string="Width", default=30)
    currency_symbol_counter = fields.Boolean(string="Currency Symbol", default=True)
    currency_symbol_position_counter = fields.Selection([('before', 'Before'), ('after', 'After')],
                                                        string="Currency Symbol Position",
                                                        default='before')
    # cheque Counter Part Sequence Configuration 
    is_counter_sequence = fields.Boolean(string="Sequence Number")
    cheque_printed_date_top_margin_counter = fields.Float(string="Top Margin", default=75)
    cheque_printed_date_left_margin_counter = fields.Float(string="Left Margin", default=138)
    font_size_cheque_printed_date_counter = fields.Float(string="Font Size", default=5)
    cheque_printed_date_spacing_counter = fields.Float(string="Width", default=50)

    # Company Signatory Details
    company_name = fields.Boolean(string="Company Name", default=True)
    font_size_company_name = fields.Float(string="Font Size", default=4)
    company_name_top_margin = fields.Float(string="Top Margin", default=64)
    company_name_left_margin = fields.Float(string="Left Margin", default=147)
    # signator space
    cmp_signatory_width = fields.Float(string="Width", default=50)
    cmp_signatory_height = fields.Float(string="Height", default=10)
    cmp_signatory_top_margin = fields.Float(string="Top Margin", default=70)
    cmp_signatory_left_margin = fields.Float(string="Left Margin", default=147)
    # first signator
    font_size_first_signatory = fields.Float(string="Font Size", default=3)
    first_signatory = fields.Char(string="Salutation of 1st Signatory")
    first_signatory_top_margin = fields.Float(string="Top Margin", default=80)
    first_signatory_left_margin = fields.Float(string="Left Margin", default=127)
    # second signator
    font_size_second_signatory = fields.Float(string="Font Size", default=3)
    second_signatory = fields.Char(string="Salutation of 2nd Signatory")
    second_signatory_top_margin = fields.Float(string="Top Margin", default=80)
    second_signatory_left_margin = fields.Float(string="Left Margin", default=144)
    # third signator
    font_size_third_signatory = fields.Float(string="Font Size", default=3)
    third_signatory = fields.Char(string="Salutation of 3rd Signatory")
    third_signatory_top_margin = fields.Float(string="Top Margin", default=80)
    third_signatory_left_margin = fields.Float(string="Left Margin", default=170)

    # Journal/Employee Names  Configuration
    is_journal_name = fields.Boolean(string="Show Journal Name")
    font_size_journal_name = fields.Float(string="Font Size", default=16)
    journal_name_top_margin = fields.Float(string="Top Margin", default=150)
    journal_name_left_margin = fields.Float(string="Left Margin", default=480)

    is_employee_name = fields.Boolean(string="Show Employee Name")
    font_size_employee_name = fields.Float(string="Font Size", default=16)
    employee_name_top_margin = fields.Float(string="Top Margin", default=150)
    employee_name_left_margin = fields.Float(string="Left Margin", default=480)


class wizard_cheque_preview(models.TransientModel):
    _name = 'wizard.cheque.preview'

    supplier_id = fields.Many2one("res.partner", string="Supplier Name")
    payment_date = fields.Date(string="Date")
    amount = fields.Float(string="Amount")
    currency_id = fields.Many2one("res.currency", string="Currency")
    image_preview = fields.Binary(string="Image")
    is_preview = fields.Boolean(string="Preview")

    @api.multi
    def action_cheque_preview(self):
        encoded_string = ''
        data = self.read()[0]
        cheque_config_id = self.env['dynamic.cheque.format.configuration'].browse(self._context.get('active_id'))
        if cheque_config_id:
            cheque_config_id.paper_format_id.write({
                'format': 'custom',
                'page_width': cheque_config_id.cheque_width,
                'page_height': cheque_config_id.cheque_height,
            })
        data.update({'label_preview': True, 'cheque_format_id': [cheque_config_id.id, cheque_config_id.name]})
        datas = {
            'ids': self.id,
            'model': 'wizard.cheque.preview',
            'form': data
        }
        pdf_data = self.env['report'].get_html(self, 'dynamic_cheque_print.dynamic_cheque_print_template', data=datas)
        body = [(self.id, pdf_data)]
        pdf_image = self.env['report']._run_wkhtmltopdf([], [], body, None, cheque_config_id.paper_format_id,
                                                        {}, {'loaded_documents': {}, 'model': u'account.payment'})
        with Image(blob=pdf_image) as img:
            filelist = glob.glob("/tmp/*.jpg")
            for f in filelist:
                os.remove(f)
            img.save(filename="/tmp/temp.jpg")
        if os.path.exists("/tmp/temp-0.jpg"):
            with open(("/tmp/temp-0.jpg"), "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
        elif os.path.exists("/tmp/temp.jpg"):
            with open(("/tmp/temp.jpg"), "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
        self.write({'image_preview': encoded_string, 'is_preview': True})
        ctx = self._context
        return {
            'name': _('Cheque Preview'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.cheque.preview',
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }


class wizard_dynamic_cheque_print(models.TransientModel):
    _name = 'wizard.dynamic.cheque.print'

    cheque_format_id = fields.Many2one('dynamic.cheque.format.configuration', string="Cheque Format")

    @api.multi
    def action_call_report(self):
        data = self.read()[0]
        if self.cheque_format_id.paper_format_id and self.cheque_format_id.cheque_height <= 0 or self.cheque_format_id.cheque_width <= 0:
            raise Warning(_("Cheque height and width can not be less than Zero(0)."))
        result = self.cheque_format_id.paper_format_id.write({
            'format': 'custom',
            'page_width': self.cheque_format_id.cheque_width,
            'page_height': self.cheque_format_id.cheque_height,
        })
        data = {
            'ids': self._context.get('active_id'),
            'model': 'wizard.dynamic.cheque.print',
            'form': data
        }
        #return self.env['ir.actions.report'].report_action(self, 'dynamic_cheque_print.dynamic_cheque_print_template',datas)
        return self.env.ref('dynamic_cheque_print.dynamic_cheque_print_report').report_action(self, data=data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
