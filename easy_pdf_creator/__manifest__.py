# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': 'Easy PDF creator',
    'version': '1.0',
    'author': 'InceptionMara',
    'price': 35.0,
    'currency': 'USD',
    'website': ' inception.mara@gmail.com ',
    'category': 'Tools',
    'summary': "Easy PDF report create end direct print",
    'description': """
        Easy PDF template creator, No development, Quick print(no download) """,
    'images': [
        'static/description/icon.jpg',
    ],
    'depends': [
        'base',
        'web',
        'web_editor',
        'report',
        'stock', # example
    ],
    'data': [
        'xml/templates.xml',
        'view/pdf_template_generator_view.xml',
        # 'view/example_picking_print_view.xml', # example
        'view/menu_view.xml',
    ],
    'installable': True,
    'application': True,
}
