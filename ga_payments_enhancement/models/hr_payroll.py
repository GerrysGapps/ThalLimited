from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payslip_status = fields.Selection([('Unpaid','Unpaid'), ('Paid','Paid')], default='Unpaid')
    payment_ref = fields.Many2one('account.payment', 'Payment Reference', store=True)


class HrPayslipBatches(models.Model):
    _inherit = 'hr.payslip.run'

    batch_status = fields.Selection([('Unpaid', 'Unpaid'), ('Paid', 'Paid')], default='Unpaid')
    payment_ref = fields.Many2one('account.payment', 'Payment Reference', store=True)