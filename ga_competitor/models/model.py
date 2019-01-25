
from odoo import api, fields, models

class InheritCustomer(models.Model):
    _inherit = 'res.partner'

    suppliers = fields.One2many('current.supplier','partner_id')
    outlet_location  =fields.One2many('outlet.location','partner_id')
    num_of_outlets = fields.Integer('No. Of Outlets')


class OutletLocation(models.Model):
    _name = 'outlet.location'

    partner_id = fields.Many2one('res.partner')
    city = fields.Char('City')
    region = fields.Char('Region')
    no_of_outlets  = fields.Integer('No. Of Outlets')
    tentative_opening_date = fields.Date('Tentative Opening Date')


class current_supplier(models.Model):
    _name = 'current.supplier'
    partner_id = fields.Many2one('res.partner')
    competitor = fields.Many2one('competitor','Supplier')
    description = fields.Text('Description/Comments')
    city = fields.Char(related='competitor.city',string='City')


class InheritLead(models.Model):
    _inherit = "crm.lead"

    key_feature_business = fields.Html('Key Feature Of Business')
    challanges = fields.Html('CHALNNAGES IF ANY')
    business_updates = fields.Html('BUSINESS UPDATES')

class Competitor(models.Model):
    _name = "competitor"
    
    name = fields.Char()
    active = fields.Boolean(default=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char()
    website = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",)
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized image of this contact. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    
    
