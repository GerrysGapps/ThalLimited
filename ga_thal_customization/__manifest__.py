# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "GA Thal Customization",
    "version": "12.0.0.0.1",
    "category": "Thal",
    "author": "GAPPS",
    "website": "http://www.gerrys.net",
    "license": "AGPL-3",
    "depends": ['base','account','ga_sale_order_approval','product','sale',"crm",'sale_crm','ga_competitor',
    ],
    "data": [
        "security/ir.model.access.csv",
        "view/sale.xml",
        #"view/view.xml",
        "view/crm.xml",
        "view/groups.xml",

    ],
    "installable": True,
}
