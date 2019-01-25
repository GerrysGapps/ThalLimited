# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning
import datetime
from odoo.tools.misc import clean_context


class TopmanagementReport(models.TransientModel):
    _name = 'topmanagement.report'

    datetime = fields.Datetime()

    @api.model
    def send_report_to_topmanagement(self):
        self.env['topmanagement.report'].sudo().create({'datetime': datetime.datetime.now()})
        # template = self.env['mail.template'].search([('name','=','Send report')])
        # template.send_mail(self.id, force_send=True)

    @api.multi
    def get_partner_name(self, partner_id):
        if partner_id:
            partner = self.env['res.partner'].search([('id', '=', partner_id)])
            return partner.name

    @api.model
    def get_leads_count_prev(self, company_id):
        return self.get_converted_opportunity(company_id) + self.get_available_leads(company_id)

    @api.model
    def get_converted_opportunity_prev(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where company_id=" + str(
            company_id) + " and type ='opportunity' and active='True' and date_conversion<" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'")
        converted_opportunity_count = self.env.cr.dictfetchall()
        return converted_opportunity_count[0]['count']

    @api.model
    def get_open_leads_prev(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where company_id=" + str(
            company_id) + " and type='lead' and won_status='pending' and active='True' and create_date<" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'")
        open_lead_count = self.env.cr.dictfetchall()
        return open_lead_count[0]['count']

    @api.model
    def get_lost_opportunities_prev(self, company_id):
        self.env.cr.execute(
            "select count(lost_reason.id),lost_reason.name as lost_reason,sum(planned_revenue) as Current,"
            "sum(actual_revenue) as Initial from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON "
            "crm.lost_reason=lost_reason.id where"
            "crm.company_id=" + str(company_id) + " and crm.type ='opportunity' and lost_reason.name!='Spam Email' and  "
                                                  "crm.won_status = 'lost' and "
                                                  "crm.date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(6)) + "'")
        lost_opportunity_count = self.env.cr.dictfetchall()
        return lost_opportunity_count[0]['count']

    @api.model
    def get_open_opportunities_prev(self, company_id):
        self.env.cr.execute(
            "select count(id) from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'pending' and active='True' and date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'")
        open_opportunity_count = self.env.cr.dictfetchall()
        return open_opportunity_count[0]['count']

    @api.model
    def get_won_opportunities_prev(self, company_id):
        self.env.cr.execute(
            "select count(id) from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'won' and active='True' and date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'")
        won_opportunity_count = self.env.cr.dictfetchall()
        return won_opportunity_count[0]['count']

    @api.model
    def get_available_leads_prev(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where company_id=" + str(
            company_id) + " and type='lead' and active='True' and create_date<" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'")
        total_lead_count = self.env.cr.dictfetchall()
        return total_lead_count[0]['count']

    @api.model
    def get_lead_conversion_percentage_prev(self, company_id):
        if self.get_leads_count(company_id) > 0:
            return round((self.get_converted_opportunity(company_id) / self.get_leads_count(company_id)) * 100, 2)
        else:
            return 0

    @api.model
    def get_lost_leads_prev(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON "
            "crm.lost_reason=lost_reason.id where crm.company_id=" + str(
            company_id) + " and crm.type='lead' and crm.won_status='lost' and lost_reason.name!='Spam Email'"
                          " and crm.create_date<" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(6)) + "'")
        lead_lost = self.env.cr.dictfetchall()
        return lead_lost[0]['count']

    @api.model
    def get_datetime_report(self):
        return 'From ' + str((datetime.datetime.now() - datetime.timedelta(6)).date()) + ' To ' + str(
            datetime.datetime.now().date())

    @api.model
    def get_leads_count(self, company_id):
        return self.get_converted_opportunity(company_id) + self.get_available_leads(company_id)

    @api.model
    def get_overdue_activity_three_days(self, company_id):
        self.env.cr.execute(
            "select count(crm.id)from mail_activity mail_act INNER JOIN crm_lead crm on mail_act.res_id=crm.id where crm.company_id=" + str(
                company_id) + " and crm.active='True' and  mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(3)) + "'")
        overdue_count_crm = self.env.cr.dictfetchall()
        self.env.cr.execute(
            "select count(sale.id)from mail_activity mail_act INNER JOIN sale_order sale "
            "on mail_act.res_id=sale.id where sale.company_id=" + str(
                company_id) + " and sale.active='True' and mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(3)) + "'")
        overdue_sale = self.env.cr.dictfetchall()
        count = 0
        if len(overdue_count_crm)>0:
            count+=overdue_count_crm[0]['count']
        if len(overdue_sale)>0:
            count+=overdue_sale[0]['count']
        return count

    @api.model
    def get_overdue_activity_seven_days(self, company_id):
        self.env.cr.execute(
            "select count(crm.id)from mail_activity mail_act INNER JOIN crm_lead crm on mail_act.res_id=crm.id where crm.company_id=" + str(
                company_id) + " and crm.active='True' and mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(7)) + "'")
        overdue_count_crm = self.env.cr.dictfetchall()
        self.env.cr.execute(
            "select count(sale.id)from mail_activity mail_act INNER JOIN sale_order sale "
            "on mail_act.res_id=sale.id where sale.company_id=" + str(
                company_id) + "and sale.active='True' and mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(7)) + "'")
        overdue_sale = self.env.cr.dictfetchall()
        count = 0
        if len(overdue_count_crm) > 0:
            count += overdue_count_crm[0]['count']
        if len(overdue_sale) > 0:
            count += overdue_sale[0]['count']
        return count

    @api.model
    def get_overdue_activity_fifteen_days(self, company_id):
        self.env.cr.execute(
            "select count(crm.id)from mail_activity mail_act INNER JOIN crm_lead crm on mail_act.res_id=crm.id where crm.company_id=" + str(
                company_id) + " and crm.active='True'and  mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(15)) + "'")
        overdue_count_crm = self.env.cr.dictfetchall()
        self.env.cr.execute(
            "select count(sale.id)from mail_activity mail_act INNER JOIN sale_order sale "
            "on mail_act.res_id=sale.id where  sale.company_id=" + str(
                company_id) + " and sale.active='True' and mail_act.date_deadline=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(15)) + "'")
        overdue_sale = self.env.cr.dictfetchall()
        count = 0
        if len(overdue_count_crm) > 0:
            count += overdue_count_crm[0]['count']
        if len(overdue_sale) > 0:
            count += overdue_sale[0]['count']
        return count

    @api.model
    def get_opportunities_count(self, company_id):
        self.env.cr.execute(
            "select count(id) from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and active='True' and date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        opportunity_count = self.env.cr.dictfetchall()
        return opportunity_count[0]['count']

    @api.model
    def get_converted_opportunity(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where  active='True' and company_id=" + str(
            company_id) + " and type ='opportunity' and date_conversion>=" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'" + " and date_conversion<=" + "'" + fields.Datetime.to_string(
            datetime.datetime.now()) + "'")
        converted_opportunity_count = self.env.cr.dictfetchall()
        return converted_opportunity_count[0]['count']

    @api.model
    def get_open_leads(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where active='True' and company_id=" + str(
            company_id) + " and type='lead' and won_status='pending' and create_date>=" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'" + " and create_date<=" + "'" + fields.Datetime.to_string(datetime.datetime.now()) + "'")
        open_lead_count = self.env.cr.dictfetchall()
        return open_lead_count[0]['count']

    @api.model
    def get_lost_opportunities(self, company_id):
        self.env.cr.execute(
            "select count(crm.id) from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON "
            "crm.lost_reason=lost_reason.id where crm.company_id=" + str(
                company_id) + " and crm.type ='opportunity' and  lost_reason.name!='Spam Email' and"
                              " crm.won_status = 'lost' and crm.date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and crm.date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        lost_opportunity_count = self.env.cr.dictfetchall()
        return lost_opportunity_count[0]['count']

    @api.model
    def get_open_opportunities(self, company_id):
        self.env.cr.execute(
            "select count(id) from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'pending' and active='True' and date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        open_opportunity_count = self.env.cr.dictfetchall()
        return open_opportunity_count[0]['count']

    @api.model
    def get_won_opportunities(self, company_id):
        self.env.cr.execute(
            "select count(id) from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'won' and active='True' and date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        won_opportunity_count = self.env.cr.dictfetchall()
        return won_opportunity_count[0]['count']

    @api.model
    def get_won_opportunities_intial_current_revenue(self, company_id):
        self.env.cr.execute(
            "select sum(planned_revenue) as Current,sum(actual_revenue) as Initial from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'won' and active='True' and date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        won_count = self.env.cr.dictfetchall()
        return won_count

    @api.model
    def get_open_opportunities_intial_current_revenue(self, company_id):
        self.env.cr.execute(
            "select sum(planned_revenue) as Current,sum(actual_revenue) as Initial from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'pending' and active='True' and date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        open_count = self.env.cr.dictfetchall()
        return open_count

    @api.model
    def get_lost_opportunities_intial_current_revenue(self, company_id):
        self.env.cr.execute(
            "select sum(crm.planned_revenue) as Current,sum(crm.actual_revenue) as Initial from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON"
            " crm.lost_reason=lost_reason.id where crm.company_id=" + str(
                company_id) + " and crm.type ='opportunity' and crm.won_status = 'won' and crm.date_last_stage_update>=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'" + " and crm.date_last_stage_update<=" + "'" + fields.Datetime.to_string(
                datetime.datetime.now()) + "'")
        lost_opportunity_count = self.env.cr.dictfetchall()
        return lost_opportunity_count

    @api.model
    def get_lost_opportunities_intial_current_revenue_prev(self, company_id):
        self.env.cr.execute(
            "select sum(crm.planned_revenue) as Current,sum(crm.actual_revenue) as Initial "
            "from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON"
            " crm.lost_reason=lost_reason.id where crm.company_id=" + str(
                company_id) + " and crm.type ='opportunity' and crm.won_status = 'lost' and "
                              "crm.date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'")

        lost_count = self.env.cr.dictfetchall()
        return lost_count

    @api.model
    def get_won_opportunities_intial_current_revenue_prev(self, company_id):
        self.env.cr.execute(
            "select sum(planned_revenue) as Current,sum(actual_revenue) as Initial from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'won' and active='True' and date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'")
        won_count = self.env.cr.dictfetchall()
        return won_count

    @api.model
    def get_open_opportunities_intial_current_revenue_prev(self, company_id):
        self.env.cr.execute(
            "select sum(planned_revenue) as Current,sum(actual_revenue) as Initial from crm_lead  where company_id=" + str(
                company_id) + " and type ='opportunity' and won_status = 'pending' and active='True' and date_last_stage_update<" + "'" + fields.Datetime.to_string(
                datetime.datetime.now() - datetime.timedelta(
                    6)) + "'")
        open_count = self.env.cr.dictfetchall()
        return open_count

    @api.model
    def get_available_leads(self, company_id):
        self.env.cr.execute("select count(id) from crm_lead  where company_id=" + str(
            company_id) + " and type='lead'  and active='True' and create_date>=" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'" + " and create_date<=" + "'" + fields.Datetime.to_string(datetime.datetime.now()) + "'")
        total_lead_count = self.env.cr.dictfetchall()
        return total_lead_count[0]['count']

    @api.model
    def get_lead_conversion_percentage(self, company_id):
        if self.get_leads_count(company_id) > 0:
            return round((self.get_converted_opportunity(company_id) / self.get_leads_count(company_id)) * 100, 2)
        else:
            return 0

    @api.model
    def get_lost_leads(self, company_id):
        self.env.cr.execute("select count(crm.id) from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON"
            " crm.lost_reason=lost_reason.id where crm.company_id=" + str(
            company_id) + " and crm.type='lead' and crm.won_status='lost' and crm.create_date>=" + "'" + fields.Datetime.to_string(
            datetime.date.today() - datetime.timedelta(
                6)) + "'" + " and crm.create_date<=" + "'" + fields.Datetime.to_string(datetime.datetime.now()) + "'")
        lead_lost = self.env.cr.dictfetchall()

        return lead_lost[0]['count']

    @api.model
    def get_details(self):
        report_data_list = []
        companies = self.env['res.company'].search(
            [('name', 'in', ['BLD - Formite', 'PPD - Carrier Bags', 'PPD - Cement & Allied'])])
        for company in companies:
            report_data_dict = {}
            report_data_dict['company'] = company.name
            report_data_dict['company_id'] = company.id
            self.env.cr.execute(
                """select count(crm.id),sum(planned_revenue) as Current,sum(actual_revenue) as Initial, p.id from crm_lead crm INNER JOIN res_users res 
                 ON crm.user_id= res.id  INNER JOIN res_partner p on res.partner_id = p.id 
               where crm.company_id='%s' and crm.type='%s' and crm.won_status='%s' and crm.active='%s' and crm.date_last_stage_update between '%s'
                and '%s'""" % (company.id, 'opportunity', 'pending', 'True',
                               fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(6)),
                    fields.Datetime.to_string(datetime.datetime.now())) + " group by p.id")
            get_all_sales_data = self.env.cr.dictfetchall()
            self.env.cr.execute(
                """select count(crm.id),sum(planned_revenue) as Current,sum(actual_revenue) as Initial,p.id from crm_lead crm INNER JOIN res_users res 
                 ON crm.user_id= res.id  INNER JOIN res_partner p on res.partner_id = p.id 
               where crm.company_id='%s' and crm.type='%s' and crm.won_status='%s' and crm.active='%s' and crm.date_last_stage_update between '%s' and '%s'""" % (
                    company.id, 'opportunity', 'won','True',
                    fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(6)),
                    fields.Datetime.to_string(datetime.datetime.now())) + " group by p.id ")
            get_all_sales_data_won = self.env.cr.dictfetchall()
            self.env.cr.execute(
                """select count(lost_reason.id),lost_reason.name as lost_reason,sum(planned_revenue) as Current,sum(actual_revenue) as Initial from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON crm.lost_reason=lost_reason.id where
                crm.company_id='%s' and crm.type='%s' and crm.won_status='%s' and lost_reason.name!='%s' and crm.date_last_stage_update between '%s' and '%s'""" % (
                    company.id, 'opportunity', 'lost','Spam Email',
                    fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(6)),
                    fields.Datetime.to_string(datetime.datetime.now())) + " group by lost_reason.name ")
            get_all_sales_lost = self.env.cr.dictfetchall()
            self.env.cr.execute(
                """select count(lost_reason.id),lost_reason.name as lost_reason,sum(crm.planned_revenue) as Current,sum(crm.actual_revenue) as Initial from crm_lead crm INNER JOIN crm_lost_reason lost_reason ON crm.lost_reason=lost_reason.id where
                crm.company_id='%s' and crm.type='%s' and crm.won_status='%s' and lost_reason.name!='%s' and crm.date_last_stage_update between '%s' and '%s'""" % (
                    company.id, 'lead', 'lost','Spam Email',
                    fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(6)),
                    fields.Datetime.to_string(datetime.datetime.now())) + " group by lost_reason.name ")
            get_all_sales_lost_leads = self.env.cr.dictfetchall()
            list_sales_person_lost = []
            list_sales_person_lost_lead = []
            list_sales_person = []
            list_sales_person_won = []
            if len(get_all_sales_lost_leads) > 0:
                for record_sale_person_lost_lead in get_all_sales_lost_leads:
                    sale_person_wise_lost_lead = {}
                    sale_person_wise_lost_lead['current_expected_revenue'] = record_sale_person_lost_lead['current']
                    sale_person_wise_lost_lead['initial_expected_revenue'] = record_sale_person_lost_lead['initial']
                    sale_person_wise_lost_lead['difference_amount'] = record_sale_person_lost_lead['current'] - \
                                                                      record_sale_person_lost_lead['initial']
                    sale_person_wise_lost_lead['count_opportunity'] = record_sale_person_lost_lead['count']
                    sale_person_wise_lost_lead['lost_reason'] = record_sale_person_lost_lead['lost_reason']
                    list_sales_person_lost_lead.append(sale_person_wise_lost_lead)

            if len(get_all_sales_lost) > 0:
                for record_sale_person_lost in get_all_sales_lost:
                    sale_person_wise_lost = {}
                    sale_person_wise_lost['current_expected_revenue'] = record_sale_person_lost['current']
                    sale_person_wise_lost['initial_expected_revenue'] = record_sale_person_lost['initial']
                    sale_person_wise_lost['difference_amount'] = record_sale_person_lost['current'] - \
                                                                 record_sale_person_lost['initial']
                    sale_person_wise_lost['count_opportunity'] = record_sale_person_lost['count']
                    sale_person_wise_lost['lost_reason'] = record_sale_person_lost['lost_reason']
                    list_sales_person_lost.append(sale_person_wise_lost)

            if len(get_all_sales_data_won) > 0:
                for record_sale_person_won in get_all_sales_data_won:
                    sale_person_wise_won = {}
                    sale_person_wise_won['current_expected_revenue'] = record_sale_person_won['current']
                    sale_person_wise_won['initial_expected_revenue'] = record_sale_person_won['initial']
                    sale_person_wise_won['difference_amount'] = record_sale_person_won['current'] - \
                                                                record_sale_person_won['initial']
                    sale_person_wise_won['count_opportunity'] = record_sale_person_won['count']
                    sale_person_wise_won['sale_person_name'] = self.get_partner_name(record_sale_person_won['id'])

                    if len(get_all_sales_data) > 0:
                        for search_data in get_all_sales_data:
                            if search_data['id'] == record_sale_person_won['id']:
                                sale_person_wise_won['open_lead_count'] = search_data['count']
                                sale_person_wise_won['open_lead_revenue'] = search_data['initial']
                                sale_person_wise_won['open_lead_expected_revenue'] = search_data['current']
                    list_sales_person_won.append(sale_person_wise_won)
            if len(get_all_sales_data) > 0:
                for record_sale_person in get_all_sales_data:
                    sale_person_wise = {}
                    sale_person_wise['current_expected_revenue'] = record_sale_person['current']
                    sale_person_wise['initial_expected_revenue'] = record_sale_person['initial']
                    sale_person_wise['difference_amount'] = record_sale_person['current'] - record_sale_person[
                        'initial']
                    sale_person_wise['count_opportunity'] = record_sale_person['count']
                    sale_person_wise['sale_person_name'] = self.get_partner_name(record_sale_person['id'])
                    list_sales_person.append(sale_person_wise)
            report_data_dict['sale_person_wise_open_lead'] = list_sales_person
            report_data_dict['sale_person_wise_won_lead'] = list_sales_person_won
            report_data_dict['lost_reason_wise_lead'] = list_sales_person_lost_lead
            report_data_dict['lost_reason_wise_opportunities'] = list_sales_person_lost
            report_data_list.append(report_data_dict)
        if len(report_data_list) > 0:
            return report_data_list




class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char('Customer Code')
    customer_category = fields.Selection(
        [('Dealer', 'Dealer'), ('Non Dealer', 'Non Dealer'), ('Corporate', 'Corporate'), ('Region', 'Region'),
         ('Associate Comapnies',
          'Associate Comapnies'), ('Direct Customer', 'Direct Customer'), ('Corporate Client', 'Corporate Client'),
         ('Export', 'Export')], string='Customer Category')
    sales_office = fields.Selection(
        [('3000', '3000'), ('4000', '4000')],
        string='Sales Office')
    distribution_channel = fields.Selection(
        [('10', '10'), ('20', '20')],
        string='Distribution Channel')
    fax_no = fields.Char('Fax No')
    ntn_no = fields.Char('NTN No')
    srtn = fields.Char('SRTN No')
    cnic_no = fields.Char('CNIC No')
    credit_limit = fields.Float('Credit Limits')
    credit_days = fields.Selection(
        [('advance', 'advance'), ('15', '15'), ('30', '30'), ('45', '45'), ('60', '60'), ('75', '75'), ('90', '90')],
        string='Credit Days')
    year_in_bussiness = fields.Selection(
        [('0-10', '0-10'), ('10-20', '10-20'), ('20-30', '20-30'), ('30-40', '30-40')],
        string='Year in Business')
    sales_history = fields.Char('Sales History')
    sales_projections = fields.Char('Sales Projections')
    comment_on_credit_performance = fields.Text('Comment on credit performance including overdue history:')
    rationale_for_credit_request = fields.Text('Rationale for credit request:')


class CustomerCategory(models.Model):
    _name = 'customer.category'

    name = fields.Char('Description')


class DistributionChannel(models.Model):
    _name = 'distribution.channel'

    name = fields.Char('Distribution Channel')


class CustomBank(models.Model):
    _name = 'custom.bank'


class CustomPort(models.Model):
    _name = 'custom.ports'

    name = fields.Char('Description')


class SalesOffice(models.Model):
    _name = 'sale.office'

    name = fields.Char('Description')


class InheritProducttemplate(models.Model):
    _inherit = 'product.template'

    old_material_no = fields.Char('Old Material No')
    default_code = fields.Char('Product Code', index=True)


class inheritSaleOrderline(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return


class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    # date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
    #                              states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
    #                              default=fields.Datetime.now.date())

    shipment_mode = fields.Selection(
        [('BY SEA VESSEL', 'BY SEA VESSEL'), ('BY AIR', 'BY AIR'), ('BY ROAD', 'BY ROAD')],
        string='Shipment Mode')
    delivery_period = fields.Char('Delivery Period')
    port_of_shipment = fields.Char(string='POF Shipment', old='port_of_shipment')
    port_of_dest = fields.Char(string='POF Destination', old='port_of_dest')
    conversion_rate = fields.Float('Conversion Rate')
    type = fields.Char('Type')
    credit_limit = fields.Boolean('Within Credit Limit ?')
    can_we_deliver = fields.Boolean('Can We Deliver ?')

    @api.multi
    def reject_quotation(self):
        super(InheritSaleOrder, self).reject_quotation()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quotation.rejection',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def send_requesttosap_func(self):
        self._check_customer_validations()
        if self.id and self.company_id:
            if self.company_id.name == 'BLD - Formite':
                template = self.env.ref('ga_thal_customization.requestSAP_companyA_template', False)
            if self.company_id.name == 'PPD - Carrier Bags':
                template = self.env.ref('ga_thal_customization.requestSAP_companyB_template',
                                        False)
            if self.company_id.name == 'PPD - Cement & Allied':
                template = self.env.ref('ga_thal_customization.requestSAP_companyC_template',
                                        False)
            template.send_mail(self.id, force_send=True)

    @api.one
    def _check_product_code_validations(self):
        for order in self.order_line:
            if not order.product_id.product_tmpl_id.default_code:
                raise Warning(_('Please Provide Product Code For ' + order.product_id.name))

    @api.one
    def _check_customer_validations(self):
        if not self.partner_id.sales_office:
            raise Warning(_('Please Provide Customr Sales Office'))
        if not self.partner_id.customer_category:
            raise Warning(_('Please Provide Customr Category'))
        if not self.partner_id.distribution_channel:
            raise Warning(_('Please Provide Customer Distribution Channel'))
        if not self.partner_id.credit_days:
            raise Warning(_('Please Provide Customer Credit Days'))
        if not self.partner_id.year_in_bussiness:
            raise Warning(_('Please Provide Customer Year in Business'))

    @api.multi
    def _action_confirm(self):
        if not self.partner_id.customer_code:
            raise Warning(_('Please Provide Customr Code'))
        self._check_product_code_validations()
        if self.approval_status == 'Rejected':
            raise Warning(_('Approval Rejected By Management '))
        res = super(InheritSaleOrder, self)._action_confirm()
        return res

    @api.multi
    def action_cancel(self):
        res = super(InheritSaleOrder, self).action_cancel()
        if self.opportunity_id:
            if self.type == 'Revised':
                sale_order_object_actual = self.env['sale.order'].search(
                    [('opportunity_id', '=', self.opportunity_id.id),
                     ('state', '!=', 'cancel'), ('type', '=', 'Revised')], order='write_date DESC', limit=1)
                self.env["crm.lead"].browse(self.opportunity_id.id).write(
                    {'actual_revenue': sale_order_object_actual.amount_total})
        return res

    # @api.onchange('opportunity_id')
    # def on_change_opp(self):
    #     if self.env.context.get('default_type', False) =='Expected Quotation':
    #         self.type = 'Expected Quotation'
    #     else:
    #         self.type = 'Revised'

    @api.model
    def create(self, vals):
        'PACKING			:	EXPORT PACKING ONTO PALLETS'
        terms = \
            "INCOTERMS : CFR\n" + \
            "PACKING:EXPORT PACKING ONTO PALLETS \n" + \
            "PAYMENT TERMS:TRANSFER IN ADVANCE IN ADVISING BANK\n" + \
            'DELIVERY PERIOD:WITHIN 2 OR 3 WEEKS \n' + \
            'BANK CHARGES:ALL BANK CHARGES OUT SIDE PAKISTAN INCLUDING \n' + \
            'REMITTANCE AND REIMBURSEMENT CHARGES ARE ON \n' + \
            'APPLICANT ACCOUNT. \n' + \
            'ADVISING BANK:“HABIB METROPOLITAN BANK LIMITED” \n' + \
            'SHAHRAH-E-FAISAL BRANCH, KARACHI – PAKISTAN,\n' + \
            'A/C. NO. : 0112-20311-119919 \n' + \
            '(SWIFT CODE NO: MPBLPKKA012)\n' + \
            'IBAN NO: PK10 MPBL 0112 0271 4011 9917 \n' + \
            'INSURANCE:TO BE ARRANGED BY THE BUYER \n' + \
            'BENIFICIARY:THAL LIMITED,\n' + \
            'LAMINATES DIVISION \n' + \
            'REMARKS:ANY ATTESTATION OR INSPECTION IF REQUIRED WILL BE ON BUYER’S ACCOUNT \n' + \
            '\t\t FOR : THAL LIMITED,\n' + \
            '\t\t LAMINATES DIVIION'

        if vals['pricelist_id']:
            pricelist = self.env['product.pricelist'].search([('id', '=', vals['pricelist_id'])])
            if pricelist:
                if 'PKR' not in pricelist.currency_id.name and 'BLD - Formite' in self.env.user.company_id.name:
                    vals['note'] = terms
                else:
                    res_config = self.env['res.config.settings'].search(
                        [('company_id', '=', self.env.user.company_id.id)], order='id DESC', limit=1)
                    if res_config:
                        vals['note'] = res_config.sale_note

        created_id = super(InheritSaleOrder, self).create(vals)
        if vals['pricelist_id']:
            # check if value already exist for today date
            price_list_object = self.env['product.pricelist'].search([('id', '=', vals['pricelist_id'])])
            currency_record = self.env['res.currency.rate'].search(
                [('currency_id', '=', price_list_object.currency_id.id), ('name', '=',
                                                                          datetime.datetime.now().date())])
            if vals['conversion_rate'] and 'PKR' not in price_list_object.currency_id:
                if not currency_record:
                    self.env['res.currency.rate'].sudo().create(
                        {'name': datetime.datetime.now().date(), 'company_id': self.env.user.company_id.id,
                         'currency_id':
                             price_list_object.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
                else:
                    self.env['res.currency.rate'].browse(currency_record[0].id).sudo().write(
                        {'rate': 1 / vals['conversion_rate']});
            return created_id

    @api.one
    @api.model
    def write(self, vals):
        terms = \
            "INCOTERMS : CFR\n" + \
            "PACKING:EXPORT PACKING ONTO PALLETS \n" + \
            "PAYMENT TERMS:TRANSFER IN ADVANCE IN ADVISING BANK\n" + \
            'DELIVERY PERIOD:WITHIN 2 OR 3 WEEKS \n' + \
            'BANK CHARGES:ALL BANK CHARGES OUT SIDE PAKISTAN INCLUDING \n' + \
            'REMITTANCE AND REIMBURSEMENT CHARGES ARE ON \n' + \
            'APPLICANT ACCOUNT. \n' + \
            'ADVISING BANK:“HABIB METROPOLITAN BANK LIMITED” \n' + \
            'SHAHRAH-E-FAISAL BRANCH, KARACHI – PAKISTAN,\n' + \
            'A/C. NO.: 0112-20311-119919 \n' + \
            '(SWIFT CODE NO: MPBLPKKA012)\n' + \
            'IBAN NO: PK10 MPBL 0112 0271 4011 9917 \n' + \
            'INSURANCE:TO BE ARRANGED BY THE BUYER \n' + \
            'BENIFICIARY:THAL LIMITED,\n' + \
            'LAMINATES DIVISION \n' + \
            'REMARKS:ANY ATTESTATION OR INSPECTION IF REQUIRED WILL BE ON BUYER’S ACCOUNT \n' + \
            '\t\t FOR : THAL LIMITED,\n' + \
            '\t\t LAMINATES DIVIION'
        write_id = super(InheritSaleOrder, self).write(vals)
        currency_record = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.pricelist_id.currency_id.id), ('name', '=',
                                                                      datetime.datetime.now().date())])
        if 'conversion_rate' in vals:
            if vals['conversion_rate'] and 'PKR' not in self.pricelist_id.currency_id:
                if not currency_record:
                    self.env['res.currency.rate'].sudo().create(
                        {'name': datetime.datetime.now().date(), 'company_id': self.env.user.company_id.id,
                         'currency_id':
                             self.pricelist_id.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
                else:
                    self.env['res.currency.rate'].browse(currency_record[0].id).sudo().write(
                        {'rate': 1 / vals['conversion_rate']});
        if 'pricelist_id' in vals:
            if vals['pricelist_id']:
                pricelist = self.env['product.pricelist'].search([('id', '=', vals['pricelist_id'])])
                if pricelist:
                    if 'PKR' not in pricelist.currency_id.name and 'BLD - Formite' in self.env.user.company_id.name:
                        self.write({'note': terms})
                    else:
                        res_config = self.env['res.config.settings'].search(
                            [('company_id', '=', self.env.user.company_id.id)], order='id DESC', limit=1)
                        if res_config:
                            self.write({'note': res_config.sale_note})

        return write_id
