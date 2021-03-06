from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re
from copy import deepcopy


class crmlead(models.Model):
    _inherit = 'crm.lead'

    incoming_mail_server = fields.Char(string='Incoming Mail Server')
    email_text = fields.Text(string='Email Body')


class IncomingMailServer(models.AbstractModel):
    _inherit = "mail.thread"

    @api.multi
    def _extract_email(self, email,mail_server):
        email_servers = mail_server.search([])
        emails = [e.lower() for e in deepcopy(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", email, re.IGNORECASE))]
        for email in email_servers:
            if email.user.lower() in emails:
                user_email = email.user
                return user_email.lower()

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        email_from = msg_dict['from']

        company_id = self.get_company_id(msg_dict, object=self)
        data = {}

        if isinstance(custom_values, dict):
            data = custom_values.copy()
        fields = self.fields_get()

        name_field = self._rec_name or 'name'
        data['email_from'] = email_from
        data['incoming_mail_server'] = msg_dict['to']
        data['email_text'] = msg_dict['to'] + ' ' + str(company_id.id)+" "+str(self._name) +" " + "\n" +str(msg_dict)

        if name_field in fields and not data.get('name'):
            data[name_field] = msg_dict.get('subject', '')

        if len(company_id) > 0:
            data['company_id'] = company_id.id
        return self.create(data)

    @api.multi
    def get_info(self, email, object, mail_server):
        to_email = self._extract_email(email, mail_server)
        object_model = self.env['ir.model'].search([('model', '=', object._name)])
        company_id = mail_server.search([('user', '=', to_email), ('object_id', '=', object_model.id)]).company_id
        return company_id

    @api.multi
    def get_company_id(self, msg_dict, object):
        mail_server = self.env['fetchmail.server']
        res = self.get_info(msg_dict['to'], object, mail_server)
        if not res:
            return self.get_info(msg_dict['cc'], object, mail_server)
        return res


class FetchMailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one('res.company', string='Company', required=True)
