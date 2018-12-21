# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import ValidationError
import re


class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.constrains('email')
    def _check_email_validation(self):
        if self.email:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",self.email) != None:
                return True
            else:
                raise ValidationError("Invalid Email")

    @api.one
    @api.constrains('website')
    def _check_weburl_validation(self):
        if self.website:
            regex = re.compile(
                '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', re.IGNORECASE)
            if re.match(regex, self.website) is not None:
                return  True
            else:
                raise ValidationError("Invalid Web URL")


    # @api.constrains('mobile')
    # def _check_mobile_validation(self):
    #     if self.mobile:
    #         if re.match("^((\+92)|(0092))-{0,1}\d{3}-{0,1}\d{7}$|^\d{11}$|^\d{4}-\d{7}$", self.mobile) != None:
    #             return True
    #         else:
    #             raise ValidationError("Invalid Mobile No.")
    #
    # @api.constrains('phone')
    # def _check_phone_validation(self):
    #     if self.phone:
    #         if re.match("^(\+?[0-9]+)((\-?)[0-9]+)*$", self.phone) != None:
    #             return True
    #         else:
    #             raise ValidationError("Invalid Phone No.")



class InheritCRM(models.Model):
    _inherit = 'crm.lead'

    @api.one
    @api.constrains('email_from')
    def _check_email_validation(self):
        if self.email_from:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",self.email_from) != None:
                return True
            else:
                raise ValidationError("Invalid Email")

    @api.one
    @api.constrains('website')
    def _check_weburl_validation(self):
        if self.website:
            regex = re.compile(
                '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', re.IGNORECASE)
            if re.match(regex, self.website) is not None:
                return True
            else:
                raise ValidationError("Invalid Web URL")

    # @api.constrains('mobile')
    # def _check_mobile_validation(self):
    #     if self.mobile:
    #         if re.match("^((\+92)|(0092))-{0,1}\d{3}-{0,1}\d{7}$|^\d{11}$|^\d{4}-\d{7}$", self.mobile) != None:
    #             return True
    #         else:
    #             raise ValidationError("Invalid Mobile No.")
    #
    # @api.constrains('phone')
    # def _check_phone_validation(self):
    #     if self.phone:
    #         if re.match("^(\+?[0-9]+)((\-?)[0-9]+)*$", self.phone) != None:
    #             return True
    #         else:
    #             raise ValidationError("Invalid Phone No.")

