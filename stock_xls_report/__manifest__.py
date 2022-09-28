{
    'name': 'Export Stock Excel Report',
    'version': '0.2',
    'category': 'Warehouse',
    'license': "AGPL-3",
    'summary': "Current Stock Report for all Products in each Warehouse",
    'author': 'ItechResources',
    'company': 'ItechResources',
    'website': 'http://www.itechresources.pk/',
    'depends': [
                'base',
                'web',
                'stock',
                'sale',
                'purchase',
                'report_xlsx'
                ],
    'data': [
            'views/wizard_view.xml',
            'views/wh_location.xml',
            ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
}
