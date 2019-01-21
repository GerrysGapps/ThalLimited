from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class IncomingMailServer(models.AbstractModel):
    _inherit = "mail.thread"

    @api.multi
    def _check_email_format(self,email_from):
        if self.email_from:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.email_from) != None:
                return True
            else:
                return False

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        email_from = 'auto@fetch_email.com'
        if not self._check_email_format(msg_dict['from']):
            email_from = msg_dict['from'].split("<")[1].split(">")[0]
        company_id = self.get_company_id(msg_dict, object=self)
        data = {}
        if isinstance(custom_values, dict):
            data = custom_values.copy()
        fields = self.fields_get()
        name_field = self._rec_name or 'name'
        data['email_from'] = email_from
        if name_field in fields and not data.get('name'):
            data[name_field] = msg_dict.get('subject', '')

        if len(company_id)>0:
            data['company_id'] = company_id.id
        return self.create(data)

    @api.multi
    def get_company_id(self,msg_dict, object):
        to_email = msg_dict['to']
        if to_email.find("<")!=-1:
            to_email = msg_dict['to'].split("<")[1].split(">")[0]
        company_id = self.env['fetchmail.server'].search([('user', '=', to_email),('object_id','=',object._name)]).company_id
        return company_id


class FetchMailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one('res.company', string='Company', required=True)

