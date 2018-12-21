# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import Warning
import datetime
from odoo.tools.misc import clean_context


class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char('Customer Code')
    customer_category = fields.Selection(
        [('Dealer', 'Dealer'), ('Non Dealer', 'Non Dealer'), ('Corporate', 'Corporate'), ('Region', 'Region'),
         ('Associate Comapnies',
          'Associate Comapnies'), ('Direct Customer', 'Direct Customer'),('Corporate Client', 'Corporate Client'), ('Export', 'Export')], string='Customer Category')
    sales_office =fields.Selection(
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


class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    # date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
    #                              states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
    #                              default=fields.Datetime.now.date())

    shipment_mode =fields.Selection(
        [('BY SEA VESSEL', 'BY SEA VESSEL'), ('BY AIR', 'BY AIR'),('BY ROAD', 'BY ROAD')],
        string='Shipment Mode')
    delivery_period = fields.Char('Delivery Period')
    port_of_shipment =fields.Char(string='POF Shipment',old='port_of_shipment')
    port_of_dest = fields.Char(string='POF Destination',old='port_of_dest')
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
                raise Warning(_('Please Provide Product Code For '+order.product_id.name))

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
        if self.opportunity_id:
            res = super(InheritSaleOrder, self).action_cancel()
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
            "PACKING			:	EXPORT PACKING ONTO PALLETS \n" + \
            "PAYMENT TERMS		 :	 TRANSFER IN ADVANCE IN ADVISING BANK\n" + \
            'DELIVERY PERIOD	 :	 WITHIN 2 OR 3 WEEKS \n' + \
            'BANK CHARGES		 :	 ALL BANK CHARGES OUT SIDE PAKISTAN INCLUDING \n' + \
            'REMITTANCE AND REIMBURSEMENT CHARGES ARE ON \n' + \
            'APPLICANT ACCOUNT. \n' + \
            'ADVISING BANK		 :	“HABIB METROPOLITAN BANK LIMITED” \n' + \
            'SHAHRAH-E-FAISAL BRANCH, KARACHI – PAKISTAN,\n' + \
            'A/C. NO. : 0112-20311-119919 \n' + \
            '(SWIFT CODE NO: MPBLPKKA012)\n' + \
            'IBAN NO: PK10 MPBL 0112 0271 4011 9917 \n' + \
            'INSURANCE		     :	TO BE ARRANGED BY THE BUYER \n' + \
            'BENIFICIARY		 :	THAL LIMITED,\n' + \
            'LAMINATES DIVISION \n' + \
            'REMARKS			 :	ANY ATTESTATION OR INSPECTION IF REQUIRED WILL BE ON BUYER’S ACCOUNT \n' + \
            '\t\t FOR : THAL LIMITED,\n' + \
            '\t\t LAMINATES DIVIION'

        if vals['pricelist_id']:
            pricelist = self.env['product.pricelist'].search([('id','=',vals['pricelist_id'])])
            if pricelist:
                if 'PKR' not in pricelist.currency_id.name:
                    vals['note'] = terms
                else:
                    res_config = self.env['res.config.settings'].search([('company_id','=',self.env.user.company_id.id)],order='id DESC',limit=1)
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
                    self.env['res.currency.rate'].sudo().create({'name': datetime.datetime.now().date(),'company_id':self.env.user.company_id.id,'currency_id':
                        price_list_object.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
                else:
                    self.env['res.currency.rate'].browse(currency_record[0].id).sudo().write(
                        {'rate': 1 / vals['conversion_rate']});
            return created_id

    @api.one
    @api.model
    def write(self, vals):
        terms = \
            "PACKING			:	EXPORT PACKING ONTO PALLETS\n"+ \
            "PAYMENT TERMS		 :	 TRANSFER IN ADVANCE IN ADVISING BANK\n" + \
            'DELIVERY PERIOD	 :	 WITHIN 2 OR 3 WEEKS \n' + \
            'BANK CHARGES		 :	 ALL BANK CHARGES OUT SIDE PAKISTAN INCLUDING \n' + \
            'REMITTANCE AND REIMBURSEMENT CHARGES ARE ON \n' + \
            'APPLICANT ACCOUNT. \n' + \
            'ADVISING BANK		 :	“HABIB METROPOLITAN BANK LIMITED” \n' + \
            'SHAHRAH-E-FAISAL BRANCH, KARACHI – PAKISTAN,\n' + \
            'A/C. NO. : 0112-20311-119919 \n' + \
            '(SWIFT CODE NO: MPBLPKKA012)\n' + \
            'IBAN NO: PK10 MPBL 0112 0271 4011 9917 \n' + \
            'INSURANCE		     :	TO BE ARRANGED BY THE BUYER \n' + \
            'BENIFICIARY		 :	THAL LIMITED,\n' + \
            'LAMINATES DIVISION \n' + \
            'REMARKS			 :	ANY ATTESTATION OR INSPECTION IF REQUIRED WILL BE ON BUYER’S ACCOUNT \n' + \
            '\t\t FOR : THAL LIMITED,\n' + \
            '\t\t LAMINATES DIVIION'
        write_id = super(InheritSaleOrder, self).write(vals)
        currency_record = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.pricelist_id.currency_id.id), ('name', '=',
                                                                      datetime.datetime.now().date())])
        if 'conversion_rate' in vals:
            if vals['conversion_rate'] and 'PKR' not in self.pricelist_id.currency_id:
                if not currency_record:
                    self.env['res.currency.rate'].sudo().create({'name': datetime.datetime.now().date(),'company_id':self.env.user.company_id.id ,'currency_id':
                        self.pricelist_id.currency_id.id, 'rate': (1 / vals['conversion_rate'])})
                else:
                    self.env['res.currency.rate'].browse(currency_record[0].id).sudo().write(
                        {'rate': 1 / vals['conversion_rate']});
        if 'pricelist_id' in vals:
            if vals['pricelist_id']:
                pricelist = self.env['product.pricelist'].search([('id', '=', vals['pricelist_id'])])
                if pricelist:
                    if 'PKR' not in pricelist.currency_id.name:
                        self.write({'note':terms})
                    else:
                        res_config = self.env['res.config.settings'].search([('company_id', '=', self.env.user.company_id.id)],order='id DESC',limit=1)
                        if res_config:
                            self.write({'note': res_config.sale_note})

        return write_id
