# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import xlsxwriter
import base64
from odoo import fields, models, api, _
import base64
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang


class wizard_payslip_report(models.TransientModel):
    _name = 'wizard.payslip.report'
    _description = 'Wizard Payslip Report'

    xls_file = fields.Binary(string='Download')
    name = fields.Char(string='File name', size=64)
    state = fields.Selection([('choose', 'choose'),
                              ('download', 'download')], default="choose", string="Status")
    payslip_ids = fields.Many2many('hr.payslip', string="Payslip Ref.")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    report_by = fields.Selection([('employee', 'Employee'),('department', 'Department'),('analytic', 'Analytic Account')],
        default="choose", string="Report By")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    department_ids = fields.Many2many('hr.department', string="Department")
    analytic_account_ids = fields.Many2many('account.analytic.account', string="Analytic Account")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def find_payslip(self):
        payslip_ids = self.env['hr.payslip']
        if self.end_date < self.start_date:
            raise Warning(_('Please select proper date range.'))
        domain = [('company_id','=',self.company_id.id),('state','=','done'),('date_from','>=',self.start_date),('date_to','<=',self.end_date)]
        if self.report_by:
            if self.report_by == 'employee':
                employee_ids = self.with_context(active_test=False).employee_ids or self.env['hr.employee'].search([('company_id','=',self.company_id.id),'|',('active','=',True),('active','=',False)])
                domain += [('employee_id','in',employee_ids.ids)]
            
            if self.report_by == 'department':
                department_ids = self.department_ids or self.env['hr.department'].search([('company_id','=',self.company_id.id)])
                domain += [('contract_id.department_id','in',department_ids.ids)]

            if self.report_by == 'analytic':
                analytic_account_ids = self.analytic_account_ids or self.env['account.analytic.account'].search([('company_id','=',self.company_id.id)])
                domain += [('contract_id.analytic_account_id','in',analytic_account_ids.ids)]

        payslip_ids = payslip_ids.search(domain)
        if not payslip_ids:
            raise Warning(_('No payslip record found.'))
        self.payslip_ids = payslip_ids

    @api.onchange('report_by')
    def onchange_report_by(self):
        self.employee_ids = self.department_ids = self.analytic_account_ids = False

    @api.multi
    def print_report_xls(self):
        self.find_payslip()
        slip_ids = self.payslip_ids
        xls_filename = 'Payslip Report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        worksheet = workbook.add_worksheet("Payslip Report")
        
        text_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        text_center.set_text_wrap()
        text_font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','bg_color':'#808080'})
        font_bold_right = workbook.add_format({'bold': True})
        font_bold_right.set_num_format('###0.00')
        number_format = workbook.add_format()
        number_format.set_num_format('###0.00')
        
        worksheet.set_column('A:AZ', 18)
        for i in range(3):
            worksheet.set_row(i, 18)
        worksheet.write(0, 1, 'Company Name', text_font_bold_center)
        worksheet.merge_range(0, 2, 0, 3, self.env.user.company_id.name or '', text_center)
        row = 3
        worksheet.merge_range(row, 0, row + 1, 0, 'No #', font_bold_center)
        worksheet.merge_range(row, 1, row + 1, 1, 'Payslip Ref', font_bold_center)
        worksheet.merge_range(row, 2, row + 1, 2, 'Code', font_bold_center)
        worksheet.merge_range(row, 3, row + 1, 3, 'Employee', font_bold_center)
        worksheet.merge_range(row, 4, row + 1, 4, 'Designation', font_bold_center)
        worksheet.merge_range(row, 5, row + 1, 5, 'Department', font_bold_center)
        worksheet.merge_range(row, 6, row + 1, 6, 'Period', font_bold_center)
        
        col = 7
        worksheet.set_row(row + 1, 30)
        result = self.get_header(slip_ids)
        col_lst = []
        # make the header by category
        for item in result:
            for categ_id, salary_rule_ids in item.items():
                if not salary_rule_ids:
                    continue
                if len(salary_rule_ids) == 1:
                    worksheet.write(row, col, categ_id.name, font_bold_center)
                    worksheet.write(row + 1, col, salary_rule_ids[0].name, font_bold_center)
                    col += 1
                    col_lst.append(salary_rule_ids[0])
                else:
                    rule_count = len(salary_rule_ids) - 1
                    worksheet.merge_range(row, col, row, col + rule_count, categ_id.name, font_bold_center)
                    for rule_id in salary_rule_ids.sorted(key=lambda l: l.sequence):
                        worksheet.write(row + 1, col, rule_id.name, font_bold_center)
                        col += 1
                        col_lst.append(rule_id)
        row += 3
        sr_no = 1
        total_rule_sum_dict = {}

        group_wise = {}
        if self.report_by:
            group_wise = self.get_group_wise_payslip(slip_ids)
            for key,value in group_wise.items():
                total_rule_sum_dict = {}
                total_arrears = 0.00
                total_grand_total = 0.00
                sr_no = 1
                worksheet.merge_range(row, 2, row, 4, key.name, text_font_bold_center)
                row+=1
                for payslip in value:
                    worksheet.write(row, 0, sr_no, text_center)
                    worksheet.write(row, 1, payslip.number)
                    worksheet.write(row, 2, payslip.employee_id.emp_code or '')
                    worksheet.write(row, 3, payslip.employee_id.name)
                    worksheet.write(row, 4, payslip.employee_id.contract_id.job_id.name or '')
                    worksheet.write(row, 5, payslip.employee_id.contract_id.department_id.name or '')
                    worksheet.write(row, 6, str(payslip.date_from) + ' - ' + str(payslip.date_to) or '')
                    col = 7
                    for col_rule_id in col_lst:
                        line_id = payslip.line_ids.filtered(lambda l: l.salary_rule_id.id == col_rule_id.id)
                        amount = line_id.total or 0.0
                        worksheet.write(row, col, formatLang(self.env, amount), number_format)
                        col += 1
                        total_rule_sum_dict.setdefault(col_rule_id, [])
                        total_rule_sum_dict[col_rule_id].append(amount)
                    row += 1
                    sr_no += 1

                    last_row = row -1
                    worksheet.merge_range(3, col, 4, col, 'Arrears', font_bold_center)
                    worksheet.write(last_row, col, formatLang(self.env,payslip.arrears))
                    total_arrears += payslip.arrears
                    col +=1
                    worksheet.merge_range(3, col, 4, col, 'Grand Total', font_bold_center)
                    worksheet.write(last_row, col, formatLang(self.env,payslip.arrears + payslip.net_amount))
                    total_grand_total += (payslip.arrears + payslip.net_amount)

                # print the footer
                col = 7
                row += 1
                worksheet.write(row, 6, "Total", text_font_bold_center)
                for col_rule_id in col_lst:
                    worksheet.write(row, col, formatLang(self.env, sum(total_rule_sum_dict.get(col_rule_id))), font_bold_right)
                    col += 1
                worksheet.write(row,col,formatLang(self.env, total_arrears), font_bold_right)
                worksheet.write(row,col+1,formatLang(self.env, total_grand_total), font_bold_right)
                row += 2
        else:
            total_arrears = 0.00
            total_grand_total = 0.00
            for payslip in slip_ids:
                worksheet.write(row, 0, sr_no, text_center)
                worksheet.write(row, 1, payslip.number)
                worksheet.write(row, 2, payslip.employee_id.emp_code or '')
                worksheet.write(row, 3, payslip.employee_id.name)
                worksheet.write(row, 4, payslip.employee_id.contract_id.job_id.name or '')
                worksheet.write(row, 5, payslip.employee_id.contract_id.department_id.name or '')
                worksheet.write(row, 6, str(payslip.date_from) + ' - ' + str(payslip.date_to) or '')
                col = 7
                for col_rule_id in col_lst:
                    line_id = payslip.line_ids.filtered(lambda l: l.salary_rule_id.id == col_rule_id.id)
                    amount = line_id.total or 0.0
                    worksheet.write(row, col, formatLang(self.env, amount), number_format)
                    col += 1
                    total_rule_sum_dict.setdefault(col_rule_id, [])
                    total_rule_sum_dict[col_rule_id].append(amount)
                row += 1
                sr_no += 1

                last_row = row -1
                worksheet.merge_range(3, col, 4, col, 'Arrears', font_bold_center)
                worksheet.write(last_row, col, formatLang(self.env,payslip.arrears))
                total_arrears += payslip.arrears
                col +=1
                worksheet.merge_range(3, col, 4, col, 'Grand Total', font_bold_center)
                worksheet.write(last_row, col, formatLang(self.env,payslip.arrears + payslip.net_amount))
                total_grand_total += (payslip.arrears + payslip.net_amount)
            # print the footer
            col = 7
            row += 1
            worksheet.write(row, 6, "Total", font_bold_center)
            for col_rule_id in col_lst:
                worksheet.write(row, col, formatLang(self.env, sum(total_rule_sum_dict.get(col_rule_id))), font_bold_right)
                col += 1
            worksheet.write(row,col,formatLang(self.env, total_arrears), font_bold_right)
            worksheet.write(row,col+1,formatLang(self.env, total_grand_total), font_bold_right)

        workbook.close()
        action = self.env.ref('eq_custom_payroll.action_wizard_payslip_report').read()[0]
        action['res_id'] = self.id
        self.write({'state': 'download',
                    'name': xls_filename,
                    'xls_file': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read())})
        return action

    @api.multi
    def print_report_pdf(self):
        data = self.read()[0]
        self.find_payslip()
        return self.env['report'].get_action(self, 'eq_custom_payroll.report_payslip_template', data=data)

    @api.multi
    def get_header(self, slip_ids):
        category_list_ids = self.env['hr.salary.rule.category'].search([])
        # find all the rule by category
        col_by_category = {}
        for payslip in slip_ids:
            for line in payslip.line_ids:
                col_by_category.setdefault(line.category_id, [])
                col_by_category[line.category_id] += line.salary_rule_id.ids
        for categ_id, rule_ids in col_by_category.items():
            col_by_category[categ_id] = self.env['hr.salary.rule'].browse(set(rule_ids))
        # make the category wise rule
        result = []
        for categ_id in category_list_ids:
            rule_ids = col_by_category.get(categ_id)
            if not rule_ids:
                continue
            result.append({categ_id: rule_ids.sorted(lambda l: l.sequence)})
        return result

    @api.multi
    def action_go_back(self):
        action = self.env.ref('eq_custom_payroll.action_wizard_payslip_report').read()[0]
        action['res_id'] = self.id
        self.write({'state': 'choose'})
        return action

    def get_group_wise_payslip(self,slip_ids):
        group_wise = {}
        if self.report_by:
            if self.report_by == 'department':
                for payslip in slip_ids:
                    group_wise.setdefault(payslip.contract_id.department_id,[])
                    group_wise[payslip.contract_id.department_id].append(payslip)
            
            if self.report_by == 'analytic':
                for payslip in slip_ids:
                    group_wise.setdefault(payslip.contract_id.analytic_account_id,[])
                    group_wise[payslip.contract_id.analytic_account_id].append(payslip)

            if self.report_by == 'employee':
                for payslip in slip_ids:
                    group_wise.setdefault(payslip.employee_id,[])
                    group_wise[payslip.employee_id].append(payslip)
        return group_wise


class eq_custom_payroll_report_payslip_template(models.AbstractModel):
    _name = 'report.eq_custom_payroll.report_payslip_template'

    @api.model
    def render_html(self, docids, data=None):
        wizard_id = self.env['wizard.payslip.report'].browse(data.get('id'))
        slip_ids = wizard_id.payslip_ids
        get_header = wizard_id.get_header(slip_ids)
        get_group_wise_data = wizard_id.get_group_wise_payslip(slip_ids)
        get_rule_list = []
        for header_dict in get_header:
            for rule_ids in header_dict.values():
                for rule_id in rule_ids:
                    get_rule_list.append(rule_id)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'wizard.payslip.report',
            'docs': slip_ids,
            'data': data,
            'slip_ids': slip_ids,
            '_get_header': get_header,
            '_get_rule_list': get_rule_list,
            'report_by':True if wizard_id.report_by else False,
            'get_group_wise_data':get_group_wise_data,
            'company_id':wizard_id.company_id

        }
        return self.env['report'].render('eq_custom_payroll.report_payslip_template', docargs)


class wizard_emp_ledger_report(models.TransientModel):
    _name = 'wizard.emp.ledger.report'
    _description = 'Employee Ledger Report'

    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    report_by = fields.Selection([('ledger', 'Ledger Report'),('trial', 'Trial Balance')],
        default="ledger", string="Report By")
    group_by = fields.Selection([('employee', 'Employee'),('department', 'Department')],string="Filter By")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    department_ids = fields.Many2many('hr.department', string="Department")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.onchange('group_by','report_by')
    def onchange_group_by(self):
        self.employee_ids = self.department_ids = False

    @api.multi
    def print_report_pdf(self):
        if self.end_date < self.start_date:
            raise Warning(_('Please select proper date range.'))
        data = self.read()[0]
        return self.env['report'].get_action(self, 'eq_custom_payroll.employee_ledger_report_template', data=data)

    def find_emp_payslip(self,employee=None):
        payslip_ids = self.env['hr.payslip'].sudo()
        domain = [('company_id','=',self.company_id.id),('state','=','done')]
        if employee:
            domain += [('employee_id','=',employee.id)]
        if self.start_date:
            domain += [('date_from','>=',self.start_date)]
        if self.end_date:
            domain += [('date_to','<=',self.end_date)]

        if self.group_by:
            if self.group_by == 'employee':
                employee_ids = self.with_context(active_test=False).employee_ids or self.env['hr.employee'].search([('company_id','=',self.company_id.id),'|',('active','=',True),('active','=',False)])
                domain += [('employee_id','in',employee_ids.ids)]

            if self.group_by == 'department':
                department_ids = self.department_ids or self.env['hr.department'].search([('company_id','=',self.company_id.id)])
                domain += [('contract_id.department_id','in',department_ids.ids)]

        payslip_ids = payslip_ids.search(domain)
        return payslip_ids

    def find_emp_advance_salary(self,employee=None):
        advance_salary_ids = self.env['employee.adv.payment'].sudo()
        domain = [('company_id','=',self.company_id.id),('state','=','approved')]
        if employee:
            domain += [('employee_id','=',employee.id)]
        if self.start_date:
            domain += [('approval_date','>=',self.start_date)]
        if self.end_date:
            domain += [('approval_date','<=',self.end_date)]

        if self.group_by:
            if self.group_by == 'employee':
                employee_ids = self.with_context(active_test=False).employee_ids or self.env['hr.employee'].search([('company_id','=',self.company_id.id),'|',('active','=',True),('active','=',False)])
                domain += [('employee_id','in',employee_ids.ids)]

            if self.group_by == 'department':
                department_ids = self.department_ids or self.env['hr.department'].search([('company_id','=',self.company_id.id)])
                domain += [('department_id','in',department_ids.ids)]

        advance_salary_ids = advance_salary_ids.search(domain)
        return advance_salary_ids

    def find_emp_payslip_adjustment(self,employee=None):
        payslip_payment_adjs = self.env['employee.adjustment.payment'].sudo()
        domain = [('company_id','=',self.company_id.id),('state','=','approved')]
        if employee:
            domain += [('employee_id','=',employee.id)]
        if self.start_date:
            domain += [('approval_date','>=',self.start_date)]
        if self.end_date:
            domain += [('approval_date','<=',self.end_date)]

        if self.group_by:
            if self.group_by == 'employee':
                employee_ids = self.with_context(active_test=False).employee_ids or self.env['hr.employee'].search([('company_id','=',self.company_id.id),'|',('active','=',True),('active','=',False)])
                domain += [('employee_id','in',employee_ids.ids)]

            if self.group_by == 'department':
                department_ids = self.department_ids or self.env['hr.department'].search([('company_id','=',self.company_id.id)])
                domain += [('department_id','in',department_ids.ids)]

        payslip_payment_adjs = payslip_payment_adjs.search(domain)
        return payslip_payment_adjs

    def find_emp_payslip_payment(self,employee=None):
        payslip_payment_line_ids = self.env['payslip.partial.payment.line'].sudo()
        domain = [('partial_payment_id.state','=','confirm'),('partial_payment_id.company_id','=',self.company_id.id)]

        if employee:
            domain += [('employee_id','=',employee.id)]

        if self.start_date:
            domain += [('partial_payment_id.acc_date','>=',self.start_date)]
        if self.end_date:
            domain += [('partial_payment_id.acc_date','<=',self.end_date)]

        if self.group_by:
            if self.group_by == 'employee':
                employee_ids = self.with_context(active_test=False).employee_ids or self.env['hr.employee'].search([('company_id','=',self.company_id.id),'|',('active','=',True),('active','=',False)])
                domain += [('employee_id','in',employee_ids.ids)]

            if self.group_by == 'department':
                department_ids = self.department_ids or self.env['hr.department'].search([('company_id','=',self.company_id.id)])
                domain += [('employee_id.department_id','in',department_ids.ids)]

        payslip_payment_line_ids = payslip_payment_line_ids.search(domain)
        return payslip_payment_line_ids

    def get_report_wise_emp_data(self):
        slip_ids = self.find_emp_payslip()
        group_wise = {}
        if self.group_by:
            if self.group_by == 'department':
                for payslip in slip_ids:
                    group_wise.setdefault(payslip.contract_id.department_id,[])
                    group_wise[payslip.contract_id.department_id].append(payslip)

            if self.group_by == 'employee':
                for payslip in slip_ids:
                    group_wise.setdefault(payslip.employee_id,[])
                    group_wise[payslip.employee_id].append(payslip)
        return group_wise

    def get_trial_balance_report(self):
        employee_ids = self.env['hr.employee']
        payslip_ids = self.find_emp_payslip()
        employee_ids |= payslip_ids.mapped('employee_id')

        payslip_payment_line_ids = self.find_emp_payslip_payment()
        employee_ids |= payslip_payment_line_ids.mapped('employee_id')

        emp_advance_salary = self.find_emp_advance_salary()
        employee_ids |= emp_advance_salary.mapped('employee_id')

        empl_payslip_adjustment = self.find_emp_payslip_adjustment()
        employee_ids |= empl_payslip_adjustment.mapped('employee_id')

        trial_balance_lst = []
        for employee in employee_ids:
            total_payslip_amount = sum(payslip_ids.filtered(lambda l:l.employee_id.id == employee.id).mapped('net_amount'))
            total_payslip_payment_amount = sum(payslip_payment_line_ids.filtered(lambda l:l.employee_id.id == employee.id).mapped('amount'))
            total_advance_salary_payment_amount = sum(emp_advance_salary.filtered(lambda l:l.employee_id.id == employee.id).mapped('approved_amount'))
            total_payslip_adjustment_receivable_amount = sum(empl_payslip_adjustment.filtered(lambda l:l.employee_id.id == employee.id and l.adjustment_type == 'Receivable').mapped('approved_amount'))
            total_payslip_adjustment_payable_amount = sum(empl_payslip_adjustment.filtered(lambda l:l.employee_id.id == employee.id and l.adjustment_type == 'Payable').mapped('approved_amount'))
            balance = (total_payslip_amount - total_payslip_payment_amount - total_advance_salary_payment_amount + total_payslip_adjustment_payable_amount - total_payslip_adjustment_receivable_amount)
            trial_balance_lst.append({'employee':employee,'balance':balance})
        return trial_balance_lst

    def get_trial_balance_report(self):
        employee_ids = self.env['hr.employee']
        payslip_ids = self.find_emp_payslip()
        employee_ids |= payslip_ids.mapped('employee_id')

        payslip_payment_line_ids = self.find_emp_payslip_payment()
        employee_ids |= payslip_payment_line_ids.mapped('employee_id')

        emp_advance_salary = self.find_emp_advance_salary()
        employee_ids |= emp_advance_salary.mapped('employee_id')

        empl_payslip_adjustment = self.find_emp_payslip_adjustment()
        employee_ids |= empl_payslip_adjustment.mapped('employee_id')

        trial_balance_lst = []
        for employee in employee_ids:
            total_payslip_amount = sum(payslip_ids.filtered(lambda l:l.employee_id.id == employee.id).mapped('net_amount'))
            total_payslip_payment_amount = sum(payslip_payment_line_ids.filtered(lambda l:l.employee_id.id == employee.id).mapped('amount'))
            total_advance_salary_payment_amount = sum(emp_advance_salary.filtered(lambda l:l.employee_id.id == employee.id).mapped('approved_amount'))
            total_payslip_adjustment_receivable_amount = sum(empl_payslip_adjustment.filtered(lambda l:l.employee_id.id == employee.id and l.adjustment_type == 'Receivable').mapped('approved_amount'))
            total_payslip_adjustment_payable_amount = sum(empl_payslip_adjustment.filtered(lambda l:l.employee_id.id == employee.id and l.adjustment_type == 'Payable').mapped('approved_amount'))
            balance = (total_payslip_amount - total_payslip_payment_amount - total_advance_salary_payment_amount + total_payslip_adjustment_payable_amount - total_payslip_adjustment_receivable_amount)
            trial_balance_lst.append({'employee':employee,'balance':balance})
        return trial_balance_lst

    def get_employee(self):
        employee_ids = self.env['hr.employee'].sudo()
        payslip_ids = self.find_emp_payslip()
        employee_ids |= payslip_ids.mapped('employee_id')

        payslip_payment_line_ids = self.find_emp_payslip_payment()
        employee_ids |= payslip_payment_line_ids.mapped('employee_id')

        emp_advance_salary = self.find_emp_advance_salary()
        employee_ids |= emp_advance_salary.mapped('employee_id')

        empl_payslip_adjustment = self.find_emp_payslip_adjustment()
        employee_ids |= empl_payslip_adjustment.mapped('employee_id')

        return employee_ids

    def get_ledger_balance_report(self,employee):
        employee_ids = employee
        payslip_ids = self.find_emp_payslip(employee)
        employee_ids |= payslip_ids.mapped('employee_id')

        payslip_payment_line_ids = self.find_emp_payslip_payment(employee)
        employee_ids |= payslip_payment_line_ids.mapped('employee_id')

        emp_advance_salary = self.find_emp_advance_salary(employee)
        employee_ids |= emp_advance_salary.mapped('employee_id')

        empl_payslip_adjustment = self.find_emp_payslip_adjustment(employee)
        employee_ids |= empl_payslip_adjustment.mapped('employee_id')

        ledger_balance_dict = {}
        ledger_balance_lst = []
        for payslip in payslip_ids:
            ledger_balance_dict.setdefault(payslip.date_to,[])
            ledger_balance_dict[payslip.date_to] += [{'date':payslip.date_to,'voucher_no':payslip.number,
                'desc':'Payslip','type':'Payslip','amount':payslip.net_amount,'total_amount':payslip.net_amount}]

        for payslip_payment in payslip_payment_line_ids:
            ledger_balance_dict.setdefault(payslip_payment.partial_payment_id.acc_date,[])
            ledger_balance_dict[payslip_payment.partial_payment_id.acc_date] += [{'date':payslip_payment.partial_payment_id.acc_date,
                'voucher_no':payslip_payment.partial_payment_id.name,'desc':'Payslip Payment',
                    'type':'Payslip Payment','amount':-payslip_payment.amount,'total_amount':-payslip_payment.amount}]

        for advance_salary in emp_advance_salary:
            ledger_balance_dict.setdefault(advance_salary.approval_date,[])
            ledger_balance_dict[advance_salary.approval_date] += [{'date':advance_salary.approval_date,
                'voucher_no':advance_salary.name,'desc':'Advance Salary','type':'Advance Salary',
                    'amount':-advance_salary.approved_amount,'total_amount':-advance_salary.approved_amount}]

        for payslip_adjustment in empl_payslip_adjustment:
            ledger_balance_dict.setdefault(payslip_adjustment.approval_date,[])


            amount = payslip_adjustment.approved_amount if payslip_adjustment.adjustment_type == 'Payable' else -payslip_adjustment.approved_amount
            total_amount = payslip_adjustment.approved_amount if payslip_adjustment.adjustment_type == 'Payable' else -payslip_adjustment.approved_amount

            ledger_balance_dict[payslip_adjustment.approval_date] += [{'date':payslip_adjustment.approval_date,
                'voucher_no':payslip_adjustment.name,'desc':payslip_adjustment.comment,'type':'Payslip Adjustment',
                    'amount':amount,'total_amount':total_amount}]

        for key , value in sorted(ledger_balance_dict.items(),key=lambda key: key[0]):
            ledger_balance_lst.extend(value)

        return ledger_balance_lst


class eq_custom_payroll_employee_ledger_report_template(models.AbstractModel):
    _name = 'report.eq_custom_payroll.employee_ledger_report_template'

    @api.model
    def render_html(self, docids, data=None):
        trial_balance_lst = []
        wizard_id = self.env['wizard.emp.ledger.report'].browse(data.get('id'))
        if wizard_id.report_by == 'trial':
            trial_balance_lst = wizard_id.get_trial_balance_report()

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'wizard.payslip.report',
            'docs': wizard_id,
            'data': data,
            'company_id':wizard_id.company_id,
            'trial_balance_lst':trial_balance_lst,
        }
        return self.env['report'].render('eq_custom_payroll.employee_ledger_report_template', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: