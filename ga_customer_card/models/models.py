# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning
import datetime
from odoo.tools.misc import clean_context
from datetime import datetime as dt


start_date = str(fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(6))).split(' ')[0]+" 00:00:00"
end_date = str(fields.Datetime.to_string(datetime.datetime.now())).split(' ')[0]+" 23:59:59"


class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    brand_name = fields.Char('Brand Name')

