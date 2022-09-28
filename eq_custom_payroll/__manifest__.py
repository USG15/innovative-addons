# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Custom Payroll",
    'category': 'Payroll',
    'version': '10.0.1.0',
    'author': 'Equick ERP',
    'description': """ Custom Paytoll changes. """,
    'depends': ['base', 'hr_payroll_account','account_accountant','hr_attendance','resource'],
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/wizard_payslip_report.xml',
        'report/report_payslip_template.xml',
        'report/report.xml',
        'views/partial_payment_view.xml',
        'views/hr_payslip_view.xml',
        'report/inherit_report_payslip_templates.xml',
        'report/report_payslip_payment_template.xml',
        'wizard/wizard_attadance_report_view.xml',
        'views/emp_advance_payment_view.xml',
        'report/report_advance_salary_template.xml',
        'report/employee_ledger_report_template.xml',
        'views/employee_payment_adjustment_view.xml',
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: