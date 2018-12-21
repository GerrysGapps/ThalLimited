# Copyright 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Dreambits Technologies Pvt. Ltd. (<http://dreambits.in>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Order Approval",
    "version": "12.0.0.0.1",
    "category": "CRM",
    "author": "Gerrys APPS",
    "website": "http://www.gerrys.net",
    "license": "AGPL-3",
    "depends": [
        'sale','product','sale_order_revision'
    ],
    "data": [
        "security/ir.model.access.csv",
        "view/view.xml",
        "view/groups.xml",
    ],
    "installable": True,
}
