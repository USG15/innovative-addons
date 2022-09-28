# -*- coding: utf-8 -*-
{
    'name': "goods_receive_note",

    'summary': """
         Goods Received report from Vendors""",

    'description': """
        Goods Received report from Vendors
    """,

    'author': "MarkERP",
    'website': "https://markinnovative.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

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