# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InheritCrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    competitor = fields.Many2one('competitor', string='Competitor')
    description = fields.Text('Description')

    @api.multi
    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'lost_reason': self.lost_reason_id.id, 'competitor': self.competitor.id,
                     'lost_reason_description': self.description})
        return leads.action_set_lost()


class InheritCrmLostReason(models.Model):
    _inherit = 'crm.lost.reason'


class InheritLead(models.Model):
    _inherit = "crm.lead"

    competitor = fields.Many2one('competitor', string='Competitor')
    lost_reason_description = fields.Text('Description')
    actual_revenue = fields.Float('Initial Expected Revenue', compute='_get_quotation_revenues', store=True)
    planned_revenue = fields.Monetary('Current Expected Revenue', currency_field='company_currency',
                                      track_visibility='always', compute='_get_quotation_revenues', store=True)
    revenue_percentage = fields.Float(compute='_compute_revenue_percentage', store=True)

    @api.one
    @api.depends('actual_revenue', 'planned_revenue')
    def _compute_revenue_percentage(self):
        if self.actual_revenue and self.planned_revenue:
            self.revenue_percentage = (self.planned_revenue / self.actual_revenue) * 100

    @api.one
    @api.depends('order_ids.amount_total', 'order_ids.conversion_rate')
    def _get_quotation_revenues(self):
        if self.id:
            sale_order_object = self.env['sale.order'].search(
                [('opportunity_id', '=', self.id), ('state', '!=', 'cancel')], order='create_date ASC', limit=1)
            sale_order_object_actual = self.env['sale.order'].search([('opportunity_id', '=', self.id),
                                                                      ('state', '!=', 'cancel')],
                                                                     order='write_date DESC', limit=1)
            if sale_order_object_actual.conversion_rate > 0:
                self.planned_revenue = sale_order_object_actual.amount_total * sale_order_object_actual.conversion_rate
            else:
                self.planned_revenue = sale_order_object_actual.amount_total

            self.env.cr.execute("select * from crm_lead where id=" + str(self.id))
            res = self.env.cr.dictfetchall()
            if res[0]['actual_revenue'] != None:
                if res[0]['actual_revenue'] > 0:
                    self.actual_revenue = res[0]['actual_revenue']
                else:
                    if sale_order_object.conversion_rate > 0:
                        self.actual_revenue = sale_order_object.amount_total * sale_order_object.conversion_rate
                    else:
                        self.actual_revenue = sale_order_object.amount_total
