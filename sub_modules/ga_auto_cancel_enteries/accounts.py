# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'account.move'

    auto_cancel = fields.Boolean('Auto Cancel', store=True)

    @api.multi
    def post(self):
        for rec in self:
            if rec.auto_cancel:
                raise ValidationError(_("You are not able to repost this journal entry"))
            else:
                return super(AccountMove, self).post()

    @api.multi
    def auto_cancel_enteries(self):
        account_move_obj = self.env['account.move']
        self.env.cr.execute("""select id from account_move where state = 'posted'""")
        account_moves = self.env.cr.dictfetchall()
        for account_move in account_moves:
            self.env.cr.execute(
                """select id,account_id from account_move_line where move_id=%s""" % (account_move['id']))
            move_lines = self.env.cr.dictfetchall()
            if len(move_lines) == 2:
                if move_lines[0]['account_id'] == move_lines[1]['account_id']:
                    account_move_obj.browse(account_move['id']).button_cancel()
                    account_move_obj.browse(account_move['id']).write({'auto_cancel': True})
