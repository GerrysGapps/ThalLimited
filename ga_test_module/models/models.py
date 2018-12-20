# -*- coding: utf-8 -*-

from odoo import models, fields, api


class gaTestSO(models.Model):
    _inherit = 'sale.order'

    remarks = fields.Char('Remarks', required=False, store=True)