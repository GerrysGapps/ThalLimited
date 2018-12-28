from odoo import api, models, _, fields


class resPartner(models.Model):
    _inherit = 'res.partner'

    income_tax_withheld = fields.Many2one('account.tax', "Income Tax Withheld")
    till_date = fields.Date(string="Till Date", track_visibility='onchange')
    use_after_expiry = fields.Many2one("account.tax", string="Use after Expiry", track_visibility='onchange')