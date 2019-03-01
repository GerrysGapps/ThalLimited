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
    "depends": ['base','mail','contacts','ga_sale_order_approval','product','sale','sale_management',"crm",'sale_crm','ga_competitor','sale_order_revision',
    ],
    "data": [
        "view/mail_data.xml",
        "view/cron.xml",
        "security/ir.model.access.csv",
        "view/sale.xml",
        "view/view.xml",
        "view/crm.xml",
        "view/groups.xml",
        "report/report.xml",
        "report/view.xml",
        "report/monthly_crm.xml",
        "report/formite.xml",
        "report/carrier_cement.xml",

    ],
'qweb': ['static/src/web.xml'],
    "installable": True,
}
