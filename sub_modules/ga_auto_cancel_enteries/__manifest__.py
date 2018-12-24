#This file basically a definition of module i.e this file provides complete details of modules.
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'ga Auto Cancel JE',
    'version': '1.0',
    'author': 'Gerrys Apps',
    'website': "http://www.gerrys.net",
    'summary': 'Auto Cancel Journal Enteries',
    'description': """
    Set a cron job for cancelling posted journal enteries""",
    'depends': ['base_setup','account_accountant'],
    'data': [
        'data/scheduled_action_data.xml',
       ],
    'installable': True,
    'auto_install': False,

}