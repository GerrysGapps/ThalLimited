# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import datetime


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

    priority = fields.Selection([
        ('0', '0'),
        ('1', 'Low'),
        ('2', 'High')
    ], string='Priority', index=True)

    competitor = fields.Many2one('competitor', string='Competitor')
    lost_reason_description = fields.Text('Description')
    actual_revenue = fields.Float('Initial Expected Revenue', compute='_get_quotation_revenues', store=True)
    planned_revenue = fields.Monetary('Current Expected Revenue', currency_field='company_currency',
                                      track_visibility='always', compute='_get_quotation_revenues', store=True)
    revenue_percentage = fields.Float(compute='_compute_revenue_percentage', store=True)

    def _send_email_func(self):
        all_leads_pending = self.env['crm.lead'].search([('won_status', '=', 'pending')])
        if all_leads_pending:
            for all_leads_pending_obj in all_leads_pending:
                filter_lists_3days = self.env['mail.activity'].search([('res_model', '=', 'crm.lead'), (
                'date_deadline', '=', datetime.date.today() - datetime.timedelta(3)),
                                                                  ('res_id', '=', all_leads_pending_obj.id)],
                                                                 order='create_date DESC', limit=1)
                if filter_lists_3days:
                    if  all_leads_pending_obj.company_id:
                        if  all_leads_pending_obj.company_id.name == 'BLD - Formite':
                            template = self.env.ref('ga_thal_customization.threedays_companyA_template', False)
                        if  all_leads_pending_obj.company_id.name == 'PPD - Carrier Bags':
                            template = self.env.ref('ga_thal_customization.threedays_companyB_template',
                                                    False)
                        if  all_leads_pending_obj.company_id.name == 'PPD - Cement & Allied':
                            template = self.env.ref('ga_thal_customization.threedays_companyC_template',
                                                    False)
                        template.send_mail(all_leads_pending_obj.id, force_send=True)
                # getting data from lead which is res_id in activity mail
                # check if 7 days passes
                filter_lists_7days = self.env['mail.activity'].search([('res_model', '=', 'crm.lead'), (
                'date_deadline', '=', datetime.date.today() - datetime.timedelta(7)),
                                                                  ('res_id', '=', all_leads_pending_obj.id)],
                                                                 order='create_date DESC', limit=1)
                if filter_lists_7days:
                    if  all_leads_pending_obj.company_id:
                        if  all_leads_pending_obj.company_id.name == 'BLD - Formite':
                            template = self.env.ref('ga_thal_customization.sevendays_companyA_template',
                                                    False)
                        if  all_leads_pending_obj.company_id.name == 'PPD - Carrier Bags':
                            template = self.env.ref('ga_thal_customization.sevendays_companyB_template',
                                                    False)
                        if  all_leads_pending_obj.company_id.name == 'PPD - Cement & Allied':
                            template = self.env.ref('ga_thal_customization.sevendays_companyC_template',
                                                    False)
                        template.send_mail(all_leads_pending_obj.id, force_send=True)

                # check if 15 days passes
                filter_lists_15days = self.env['mail.activity'].search([('res_model', '=', 'crm.lead'), (
                'date_deadline', '=', datetime.date.today() - datetime.timedelta(15)),
                                                                  ('res_id', '=', all_leads_pending_obj.id)],
                                                                 order='create_date DESC', limit=1)
                if filter_lists_15days:
                    if all_leads_pending_obj.company_id:
                        if all_leads_pending_obj.company_id.name == 'BLD - Formite':
                            template = self.env.ref('ga_thal_customization.fiftendays_companyA_template',
                                                    False)
                        if all_leads_pending_obj.company_id.name == 'PPD - Carrier Bags':
                            template = self.env.ref('ga_thal_customization.fiftendays_companyB_template',
                                                    False)
                        if all_leads_pending_obj.company_id.name == 'PPD - Cement & Allied':
                            template =self.env.ref('ga_thal_customization.fiftendays_companyC_template',
                                                               False)
                        template.send_mail(all_leads_pending_obj.id, force_send=True)

    @api.one
    @api.depends('actual_revenue', 'planned_revenue')
    def _compute_revenue_percentage(self):
        if self.actual_revenue and self.planned_revenue:
            self.revenue_percentage = (self.planned_revenue / self.actual_revenue) * 100

    @api.one
    @api.depends('order_ids.amount_total', 'order_ids.conversion_rate')
    def _get_quotation_revenues(self):
        if self.id:

            # get latest record from
            sale_order_object = self.env['sale.order'].search(
                [('opportunity_id', '=', self.id), ('state', '!=', 'cancel')], order='create_date ASC', limit=1)
            sale_order_object_actual = self.env['sale.order'].search([('opportunity_id', '=', self.id),
                                                                      ('state', '!=', 'cancel')],
                                                                     order='write_date DESC', limit=1)
            currency_actual = self.env['res.currency.rate'].search(
                [('currency_id', '=', sale_order_object_actual.currency_id.id)], order='name DESC', limit=1)

            if len(self.order_ids) > 0 and self.order_ids[0].conversion_rate:
                self.planned_revenue = sale_order_object_actual.amount_total * self.order_ids[0].conversion_rate
            else:
                if currency_actual:
                    self.planned_revenue = sale_order_object_actual.amount_total * (1 / currency_actual.rate)
                else:
                    self.planned_revenue = sale_order_object_actual.amount_total

            currency = self.env['res.currency.rate'].search(
                [('currency_id', '=', sale_order_object.currency_id.id)], order='name DESC', limit=1)
            self.env.cr.execute("select * from crm_lead where id=" + str(self.id))
            res = self.env.cr.dictfetchall()
            if res[0]['actual_revenue'] != None:

                if res[0]['actual_revenue'] > 0:
                    self.actual_revenue = res[0]['actual_revenue']
                else:
                    if len(self.order_ids) > 0 and self.order_ids[0].conversion_rate:
                        self.actual_revenue = sale_order_object.amount_total * self.order_ids[0].conversion_rate
                    else:
                        if currency:
                            self.actual_revenue = sale_order_object.amount_total * (1 / currency.rate)
                        else:
                            self.actual_revenue = sale_order_object.amount_total
