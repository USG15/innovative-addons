# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Picking Approval",
    'category': 'Inventory',
    'version': '10.0.1.0',
    'author': 'Equick ERP',
    'description': """Picking Approval. """,
    'depends': ['base', 'stock'],
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/security.xml',
        'views/stock_picking_view.xml',
        'views/report_stockpicking_operations.xml'
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: