# -*- coding: utf-8 -*-
{
    'name': "goods_issuance_note",

    'summary': """
        Goods issuance report to projects""",

    'description': """
        Goods issuance report to projects
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
        'report/template.xml',
        'report/header.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}