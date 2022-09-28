# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Construction Management",
    'category': 'Project',
    'version': '10.0.1.0',
    'author': 'Equick ERP',
    'description': """ Construction Management. """,
    'depends': ['base', 'account_accountant','project','purchase','stock_account','sale','payment'],
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/stock_picking_view.xml',
        'views/hide_inventory_menu.xml',
        'views/work_category_view.xml',
        'views/work_order_view.xml',
        'views/finished_work_order_view.xml',
        'views/account_view.xml',
        'views/po_approve_demand_view.xml',
        'views/rental_registration_view.xml',
        'wizard/wizard_project_report_view.xml',
        'report/report.xml',
        'report/layout_templates.xml',
        'report/print_project_report_template.xml',
        'report/print_rental_registration_template.xml',
        'report/print_service_wo_template.xml',
        'report/print_service_sub_wo_template.xml',
        'report/print_service_progress_template.xml',
        'report/print_finished_wo_template.xml',
        'report/print_finished_sub_wo_template.xml',
        'report/print_finished_progress_template.xml',
        'report/report_invoice.xml',
        'report/report_purchaseorder.xml',
        'report/purchase_quotation_templates.xml',
        'report/report_payment.xml',
        'report/report_deliveryslip.xml',
        'report/print_quotation_template.xml',
        'report/print_quotation_with_price_template.xml',
        # 'report/report_stockpicking_operations.xml'
    ],
    'demo': [],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: