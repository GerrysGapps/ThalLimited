# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'Dynamic Cheque Print',
    'version': '1.0',
    'author': 'Gerrys apps',
    'category': 'Account',
    'description': """
        User can print the cheque and also can configure cheque different bank's cheque formats.
    """,
    'website': 'https://www.acespritech.com',
    'summary': 'Dynamic Cheque Print. User can print cheque easily.',
    'depends': ['base', 'sale', 'account'],
    'currency': 'EUR',
    'price': 60.00,
    'data': [
        'views/dynamic_cheque_preview.xml',
        'views/dynamic_cheque_format_configuration_view.xml',
        'views/dynamic_cheque_print.xml',
        'views/account_payment_view.xml',
        'views/dynamic_cheque_print_template.xml',
        'dynamic_cheque_print_report.xml',
        'data/demo.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
