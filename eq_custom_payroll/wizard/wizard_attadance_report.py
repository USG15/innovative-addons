# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import xlsxwriter
import base64
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang
from datetime import datetime, timedelta
from dateutil import rrule
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class wizard_attadance_report(models.TransientModel):
    _name = 'wizard.attadance.report'
    _description = 'Wizard Attendance Report'

    xls_file = fields.Binary(string='Download')
    name = fields.Char(string='File name', size=64)
    state = fields.Selection([('choose', 'choose'),
                              ('download', 'download')], default="choose", string="Status")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.multi
    def print_report_xls(self):
        if self.end_date < self.start_date:
            raise Warning(_('Please select proper date range.'))
        
        date_from = datetime.strptime(self.start_date, '%Y-%m-%d')
        date_to = datetime.strptime(self.end_date, '%Y-%m-%d')
        no_of_days = (date_to - date_from).days + 1
        if no_of_days > 31:
            raise Warning(_("You can't print report more than 31 days."))

        xls_filename = 'Attendance Report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        worksheet = workbook.add_worksheet("Attendance Report")
        
        text_center = workbook.add_format({'align': 'center', 'valign': 'vcenter','border':1})
        text_center.set_text_wrap()
        text_font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','border':1})
        font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','bg_color':'#D3D3D3','border':1})
        number_format = workbook.add_format({'align': 'center', 'valign': 'vcenter','border':1,'num_format':'#,##0.0'})
        number_format.set_text_wrap()

        ot_number_format = workbook.add_format({'align': 'center', 'valign': 'vcenter','border':1,'num_format':'#,##0.0','bg_color':'#FFFF00'})
        ot_number_format.set_text_wrap()

        total_ot_text_font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','border':1,'num_format':'#,##0.0','bg_color':'#FFFF00'})
        total_text_font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','border':1,'num_format':'#,##0.0'})

        absent_bold_center = workbook.add_format({'align': 'center', 'valign': 'vcenter','bg_color':'#CD853F','border':1})
        off_bold_center = workbook.add_format({'align': 'center', 'valign': 'vcenter','bg_color':'#6B8E23','border':1})

        sign_text_enter = workbook.add_format({'align': 'center', 'valign': 'vcenter','border':1,'font':15})

        worksheet.set_column('A:B', 18)
        worksheet.set_column('C:BK', 4.43)
        worksheet.write(0, 0, 'Company Name', text_font_bold_center)
        worksheet.merge_range(0, 1, 0, 3, self.env.user.company_id.name or '', text_center)
        worksheet.write(1, 0, 'Date From', text_font_bold_center)
        worksheet.merge_range(1, 1, 1, 3, self.start_date, text_center)
        worksheet.write(2, 0, 'Date To', text_font_bold_center)
        worksheet.merge_range(2, 1, 2, 3, self.end_date, text_center)

        row = 4
        col = 2
        employee_ids = self.employee_ids or self.env['hr.attendance'].sudo().search([('check_in','>=',self.start_date),('check_out','<=',self.end_date)]).mapped('employee_id')
        worksheet.merge_range(row, 0, row + 2, 0, 'Code', font_bold_center)
        worksheet.merge_range(row, 1, row + 2, 1, 'Employee', font_bold_center)

        day_dict = {}

        for day in rrule.rrule(rrule.DAILY,
                               dtstart=date_from,
                               until=date_to):
            weekday = day.strftime('%a') 
            day = day.strftime('%d/%b')
            worksheet.merge_range(row, col, row, col+1, day,font_bold_center)
            worksheet.merge_range(row+1, col, row+1, col+1, weekday,font_bold_center)
            worksheet.write(row + 2, col, 'NH',font_bold_center)
            worksheet.write(row + 2, col+1, 'OT',font_bold_center)
            col +=2

        worksheet.merge_range(4, col, 4, col+1, 'Total', font_bold_center)
        worksheet.merge_range(4+1, col, 4+1, col+1, ' ', font_bold_center)
        worksheet.write(4 + 2, col, 'NH',font_bold_center)
        worksheet.write(4 + 2, col+1, 'OT',font_bold_center)

        row = 8
        nh_column_wise_total = {}
        ot_column_wise_total = {}
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        for employee in employee_ids:
            leave_ids = self.env['hr.holidays'].search([('employee_id','=',employee.id),('type','=','remove'),('state','=','validate')])
            col = 2
            total_normal_hour = 0.00
            total_ot_hour = 0.00
            worksheet.write(row, 0, employee.emp_code or '',text_font_bold_center)
            worksheet.write(row, 1, employee.name,text_font_bold_center)
            for day in rrule.rrule(rrule.DAILY,
                               dtstart=date_from,
                               until=date_to):
                weekday = day.weekday()
                check_in = day.strftime('%Y-%m-%d 00:00:01')
                check_out = day.strftime('%Y-%m-%d 23:59:59')
                each_date = day.date()
                check_in = user_tz.localize(datetime.strptime(check_in, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(pytz.utc)
                check_in = check_in.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                check_out = user_tz.localize(datetime.strptime(check_out, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(pytz.utc)
                check_out = check_out.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                normal_hour = 0.00
                ot_hour = 0.00
                att_ids = False
                emp_on_leave = False
                off_day = False

                hr_attendance_id = self.env['hr.attendance'].search([('employee_id','=',employee.id),('check_in','>=',check_in),('check_out','<=',check_out)])
                if not hr_attendance_id:
                    emp_on_leave = True

                check_att_ids = employee.contract_id.working_hours.attendance_ids.filtered(lambda l:l.dayofweek == str(weekday))
                if not check_att_ids:
                    off_day = True

                if hr_attendance_id:
                    worked_hours = sum(hr_attendance_id.mapped('worked_hours'))
                    att_ids = employee.contract_id.working_hours.attendance_ids.filtered(lambda l:l.dayofweek == str(weekday))
                    from_hours = sum(att_ids.mapped('hour_from'))
                    to_hour = sum(att_ids.mapped('hour_to'))
                    per_day_hour = (to_hour - from_hours)
                    margin_limit = sum(att_ids.mapped('margin_time'))
                    normal_hour = per_day_hour
                    if worked_hours <= 0:
                        normal_hour = 0

                    for leave in leave_ids:
                        leave_date_from = fields.Datetime.from_string(leave.date_from).date()
                        leave_date_to = fields.Datetime.from_string(leave.date_to).date()
                        if each_date >= leave_date_from and each_date <= leave_date_to:
                            normal_hour = 0
                            emp_on_leave = True
                    
                    diff_hour = abs(normal_hour - worked_hours) * 60
                    if worked_hours and worked_hours > normal_hour:
                        ot_hour = worked_hours - normal_hour

                    if worked_hours and worked_hours < normal_hour:
                        if margin_limit and diff_hour and diff_hour > margin_limit:
                            normal_hour = (worked_hours-1)
                        else:
                            normal_hour = worked_hours

                    total_normal_hour += normal_hour
                    total_ot_hour += ot_hour
            
                worksheet.write(row, col, normal_hour,number_format)
                worksheet.write(row, col+1, ' - ',number_format)
                if ot_hour:
                    worksheet.write(row, col+1, ot_hour,ot_number_format)

                if not normal_hour and not ot_hour and emp_on_leave and not att_ids:
                    worksheet.merge_range(row, col, row, col+1, "Absent",absent_bold_center)
                if off_day:
                    if not ot_hour:
                        worksheet.merge_range(row, col, row, col+1, "Off",off_bold_center)
                    else:
                        worksheet.write(row, col, "Off",off_bold_center)

                nh_column_wise_total.setdefault(col,0.00)
                ot_column_wise_total.setdefault(col+1,0.00)
                nh_column_wise_total[col] += normal_hour
                ot_column_wise_total[col+1] += ot_hour
                col +=2
            
            worksheet.write(row, col, total_normal_hour,number_format)
            worksheet.write(row, col+1, total_ot_hour,ot_number_format)
            row+=1

        # worksheet.write(row, 0, "Total",text_font_bold_center)
        worksheet.merge_range(row, 0, row, 1, 'Total',text_font_bold_center)
        column_wise_nh_total = 0.00
        column_wise_ot_total = 0.00
        for key,value in nh_column_wise_total.items():
            column_wise_nh_total+= value
            worksheet.write(row, key, value ,total_text_font_bold_center)
        for key,value in ot_column_wise_total.items():
            column_wise_ot_total+= value
            worksheet.write(row, key, ' - ',total_text_font_bold_center)
            if value:
                worksheet.write(row, key, value ,total_ot_text_font_bold_center)

        worksheet.write(row, col, column_wise_nh_total ,total_text_font_bold_center)
        worksheet.write(row, col+1, column_wise_ot_total ,total_ot_text_font_bold_center)
        worksheet.merge_range(row+4, col-4, row+5, col, 'Authorized Signature',sign_text_enter)

        workbook.close()
        action = self.env.ref('eq_custom_payroll.action_wizard_attadance_report').read()[0]
        action['res_id'] = self.id
        self.write({'state': 'download',
                    'name': xls_filename,
                    'xls_file': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read())})
        return action

    @api.multi
    def action_go_back(self):
        action = self.env.ref('eq_custom_payroll.action_wizard_attadance_report').read()[0]
        action['res_id'] = self.id
        self.write({'state': 'choose'})
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: