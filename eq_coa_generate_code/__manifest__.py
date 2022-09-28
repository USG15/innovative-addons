# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "COA Code Structure",
    'category': 'Accounting',
    'version': '10.0.1.0',
    'author': 'Equick ERP',
    'description': """ COA Code structure. """,
    'depends': ['base', 'account_accountant'],
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_account_sub_type_view.xml'
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: