# -*- coding: utf-8 -*-
{
    'name': "Invoice_report",

    'summary': """
        Vendor Bill report is for Purchases and 
        for booking of payables to vendors""",

    'description': """
        Vendor Bill report is for Purchases and 
        for booking of payables to vendors
    """,

    'author': "MarkERP",
    'website': "https://markinnovative.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/header.xml',
        'report/template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}