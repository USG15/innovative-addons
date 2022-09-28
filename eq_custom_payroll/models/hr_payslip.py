# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import time
import babel
from odoo import fields, models, api,tools, _
from datetime import datetime, timedelta
from dateutil import rrule
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import Warning,UserError
import pytz
import calendar


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('line_ids')
    def compute_net_amount(self):
        for rec in self:
            amount = 0
            amount = sum(rec.line_ids.filtered(lambda l:l.category_id.code == 'NET').mapped('total'))
            rec.net_amount = amount

    net_amount = fields.Float('Current Month Payable Amount', compute='compute_net_amount',store=True)
    payment_done = fields.Boolean(string="Payment Done?",copy=False)
    payment_move_ids = fields.Many2many('account.move',string="Payment Move")
    remaining_amount = fields.Float('Remaining Amount',copy=False)
    arrears = fields.Float('Arrears',copy=False)
    no_of_days = fields.Float(string="No of days",compute='compute_payslip_no_of_days',store=True)
    total_ot_hours = fields.Float(string="OT Hours",compute='compute_emp_ot_hours',store=True)
    total_hours = fields.Float(string="Total Hours",compute='compute_emp_ot_hours',store=True)
    normal_hours = fields.Float(string="Normal Hours",compute='compute_emp_ot_hours',store=True)

    weekly_schedule_hour = fields.Float(string="Weekly Schedule Hours",compute='compute_weekly_hour',store=True)
    weekly_off_hour = fields.Float(string="Weekly Off Hours",compute='compute_weekly_hour',store=True)
    weekly_days = fields.Float(string="Weekly Schedule Day",compute='compute_weekly_hour',store=True)
    per_day_working_hour = fields.Float('Per Day Working Hour',copy=False)
    total_advance_salary = fields.Float('Total Advance Salary',copy=False,compute='compute_weekly_hour',store=True)
    advance_salary = fields.Float('Advance Salary',copy=False,store=True)
    month = fields.Selection([
        (1,'January'),(2,'February'),(3,'March'),(4,'April'),
        (5,'May'),(6,'June'),(7,'July'),(8,'August'),
        (9,'September'),(10,'October'),(11,'November'),(12,'December'),
    ],string="Month")
    per_day_cal = fields.Float('Per Day Cal',copy=False)
    emp_code = fields.Char(related='employee_id.emp_code',string="Employee Code",store=True)

    @api.model
    def create(self,vals):
        backdated_days = int(self.env["ir.config_parameter"].get_param("backdated_days"))
        if backdated_days:
            payslip_end_date = datetime.strptime(vals.get('date_to'), '%Y-%m-%d').date()
            today_date = fields.datetime.now().date() - timedelta(days=backdated_days)
            if payslip_end_date < today_date and not self.user_has_groups('eq_custom_payroll.group_allow_backdated_payslip'):
                raise UserError(_("You can't create backdated payslip. please contact to adminstrator."))
        return super(HrPayslip,self).create(vals)

    @api.depends('date_to', 'date_from', 'employee_id', 'contract_id','contract_id.working_hours')
    def compute_weekly_hour(self):
        for payslip in self:
            total_weekly_schedule_hour = 0.00
            total_weekly_off_hour = 0.00
            total_weekly_days = 0.00

            total_advance_salary = sum(self.env['employee.adv.payment'].search([('employee_id','=',payslip.employee_id.id),('state','=','approved')]).mapped('approved_amount'))
            total_paid_adv_salary = sum(self.env['hr.payslip'].search([('employee_id','=',payslip.employee_id.id),('state','=','done')]).mapped('advance_salary'))
            if payslip.contract_id and payslip.contract_id.working_hours:
                for weekday in range(0,7):
                    attendance_ids = payslip.contract_id.working_hours.attendance_ids.filtered(lambda l:l.dayofweek == str(weekday))
                    from_hours = sum(attendance_ids.mapped('hour_from'))
                    to_hour = sum(attendance_ids.mapped('hour_to'))
                    per_day_hour = (to_hour - from_hours)
                    total_weekly_schedule_hour += per_day_hour
                    if attendance_ids:
                        total_weekly_days+=1

                leave_ids = payslip.contract_id.working_hours.leave_ids
                for each_leave in leave_ids:
                    date_from = datetime.strptime(each_leave.date_from, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    date_to = datetime.strptime(each_leave.date_to, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    if date_from >= payslip.date_from and date_to <= payslip.date_to:
                        date_from = fields.Datetime.from_string(date_from)
                        date_to = fields.Datetime.from_string(date_to)
                        total_weekly_off_hour += (date_to - date_from).days + 1

            payslip.weekly_schedule_hour = total_weekly_schedule_hour
            payslip.weekly_off_hour = total_weekly_off_hour
            payslip.weekly_days = total_weekly_days
            payslip.total_advance_salary = (total_advance_salary - total_paid_adv_salary)
            payslip.advance_salary = (total_advance_salary - total_paid_adv_salary)

            if total_weekly_schedule_hour and total_weekly_days:
                payslip.per_day_working_hour = (total_weekly_schedule_hour / total_weekly_days)

            if total_weekly_off_hour and payslip.per_day_working_hour:
                payslip.weekly_off_hour = total_weekly_off_hour * payslip.per_day_working_hour

    @api.onchange('employee_id', 'date_from', 'date_to','month')
    def onchange_employee(self):
        self.worked_days_line_ids = []
        self.per_day_cal = 0.00
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        if self.month:
            per_day_cal = float((calendar.monthrange(datetime.now().year,self.month)[1]))
            self.per_day_cal = float(per_day_cal / 7)

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return
    
    @api.depends('date_to', 'date_from', 'employee_id', 'contract_id')
    def compute_emp_ot_hours(self):
        hr_attendance_obj = self.env['hr.attendance']
        for payslip in self:
            total_ot_hour = 0
            total_spent_hours = 0.00
            total_normal_hours = 0.00
            if payslip.date_to and payslip.date_from and payslip.date_to >= payslip.date_from and payslip.employee_id and payslip.employee_id.contract_id and payslip.contract_id:
                total_normal_hours,total_ot_hour = payslip.get_employee_attendance()
                total_spent_hours = (total_normal_hours + total_ot_hour) 

            payslip.total_ot_hours = total_ot_hour
            payslip.total_hours = total_spent_hours
            payslip.normal_hours = total_normal_hours


    @api.depends('date_to', 'date_from', 'employee_id')
    def compute_payslip_no_of_days(self):
        for payslip in self:
            payslip.get_worked_day_lines(payslip.contract_id.ids, payslip.date_from, payslip.date_to)
            no_of_days = 0.00
            per_day_cal = 0.00
            if payslip.date_to and payslip.date_from and payslip.date_to >= payslip.date_from:
                date_from = datetime.strptime(payslip.date_from, '%Y-%m-%d')
                date_to = datetime.strptime(payslip.date_to, '%Y-%m-%d')
                no_of_days = (date_to - date_from).days + 1
            payslip.no_of_days = no_of_days

    def get_employee_attendance(self):
        leave_ids = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('type','=','remove'),('state','=','validate')])
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        total_ot_hours = 0
        total_spent_hours = 0.00
        total_normal_hours = 0.00
        count = 0
        date_from = datetime.strptime(self.date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d').date()
        attendance_allowance = False
        is_missing_attdance = False
        is_diff_attdance = False
        for day in rrule.rrule(rrule.DAILY,
                               dtstart=date_from,
                               until=date_to):
            check_in = day.strftime('%Y-%m-%d 00:00:01')
            check_out = day.strftime('%Y-%m-%d 23:59:59')
            weekday = day.weekday()
            each_date = day.date()

            check_in = user_tz.localize(datetime.strptime(check_in, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(pytz.utc)
            check_in = check_in.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            check_out = user_tz.localize(datetime.strptime(check_out, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(pytz.utc)
            check_out = check_out.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            hr_attendance_id = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id),('check_in','>=',check_in),('check_out','<=',check_out)])
            if not hr_attendance_id:
                continue

            actual_working_hours = sum(hr_attendance_id.mapped('worked_hours'))
            att_ids = self.contract_id.working_hours.attendance_ids.filtered(lambda l:l.dayofweek == str(weekday))
            from_hours = sum(att_ids.mapped('hour_from'))
            to_hour = sum(att_ids.mapped('hour_to'))
            per_day_hour = (to_hour - from_hours)
            margin_limit = sum(att_ids.mapped('margin_time'))
            if not att_ids and actual_working_hours:
                total_ot_hours += actual_working_hours
                continue

            for leave in leave_ids:
                date_from = fields.Datetime.from_string(leave.date_from).date()
                date_to = fields.Datetime.from_string(leave.date_to).date()
                if each_date >= date_from and each_date <= date_to:
                    per_day_hour = 0

            # if actual_working_hours and not per_day_hour:
            #     total_ot_hours += actual_working_hours

            if actual_working_hours > per_day_hour:
                total_ot_hours += (actual_working_hours - per_day_hour)
                total_normal_hours += per_day_hour
            else:
                diff_hour = abs(per_day_hour - actual_working_hours) * 60
                if margin_limit and diff_hour and diff_hour > margin_limit:
                    actual_working_hours = (actual_working_hours-1)
                else:
                    actual_working_hours = actual_working_hours
                    
                total_normal_hours += actual_working_hours

        return total_normal_hours,total_ot_hours

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            if not payslip.total_advance_salary and payslip.advance_salary:
                raise Warning(_("You can't pay advance salary if there is no advance salary amount."))
            if payslip.total_advance_salary and payslip.advance_salary <0 or payslip.advance_salary > payslip.total_advance_salary:
                raise Warning(_("Please enter proper advance salary."))

            payslip.compute_net_amount()
            payslip.compute_emp_ot_hours()
            payslip.compute_weekly_hour()
            payslip.get_employee_payslip_amt()
        return super(HrPayslip,self).compute_sheet()

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip,self).action_payslip_done()
        for payslip in self:
            total_remaining_amount = payslip.net_amount + payslip.arrears
            # total_remaining_amount += payslip.get_employee_payslip_amt()
            payslip.remaining_amount = total_remaining_amount
        return res

    def get_employee_payslip_amt(self):
        payslip_ids = self.env['hr.payslip']
        amount = 0.00
        domain = [('employee_id','=',self.employee_id.id),('company_id','=',self.company_id.id),('state','=','done'),('remaining_amount','>',0),('id','!=',self.id),('payment_done','=',True)]
        payslip_ids = payslip_ids.search(domain,order='id desc',limit=1)
        if not payslip_ids:
            return amount
        amount = sum(payslip_ids.mapped('remaining_amount'))
        self.arrears = amount
        return amount

    @api.multi
    def action_view_entries(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id','in',self.payment_move_ids.ids)]
        action['context'] = {}
        return action

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to)
            ], limit=1)

        res = []
        #fill only if the contract as a working schedule linked
        uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref('product.product_uom_hour', raise_if_not_found=False)
            interval_data = []
            holidays = self.env['hr.holidays']
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1

            # Gather all intervals and holidays
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:
                    interval_data.append((interval, was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])))

            # Extract information from previous data. A working interval is considered:
            # - as a leave if a hr.holiday completely covers the period
            # - as a working period instead
            for interval, holiday in interval_data:
                holidays |= holiday
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                if holiday:
                    #if he was on leave, fill the leaves dict
                    if holiday.holiday_status_id.name in leaves:
                        leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        leaves[holiday.holiday_status_id.name] = {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.name,
                            'number_of_days': 0.0,
                            'number_of_hours': hours,
                            'contract_id': contract.id,
                        }
                else:
                    #add the input vals to tmp (increment if existing)
                    attendances['number_of_hours'] += hours

            # Clean-up the results
            leaves = [value for key, value in leaves.items()]
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day)\
                    if uom_day and uom_hour\
                    else data['number_of_hours'] / 8.0
                res.append(data)

            if self.normal_hours:
                vals = {
                    'name': _("Normal Working Hours"),
                    'sequence': 2,
                    'code': 'Normal Hours',
                    'number_of_days': 0.0,
                    'number_of_hours': self.normal_hours,
                    'contract_id': contract.id,
                    }
                res.append(vals)
            if self.total_ot_hours:
                vals = {
                    'name': _("OT Hours"),
                    'sequence': 3,
                    'code': 'OT Hours',
                    'number_of_days': 0.0,
                    'number_of_hours': self.total_ot_hours,
                    'contract_id': contract.id,
                    }
                res.append(vals)
        return res


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    payment_journal_id = fields.Many2one('account.journal',string="Payment Journal",copy=False)


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    margin_time = fields.Float('Margin Time(Minutes)')


class hr_employee(models.Model):
    _inherit = "hr.employee"

    emp_code = fields.Char(string="Employee Code",copy=False)
    emp_code_no = fields.Integer(string="Employee Code No",copy=False)

    @api.model
    def create(self,vals):
        res = super(hr_employee,self).create(vals)
        for employee in res:
            employee.generate_emp_code()
        return res

    @api.multi
    def write(self,vals):
        res = super(hr_employee,self).write(vals)
        if vals.get('company_id') or vals.get('department_id') or vals.get('job_id'):
            self.generate_emp_code()
        return res

    def generate_emp_code(self):
        for employee in self:
            # if not employee.emp_code:
            if not employee.company_id or not employee.company_id.code:
                raise Warning(_("Please enter company code to generate proper employee code."))
            if not employee.department_id or not employee.department_id.code:
                raise Warning(_("Please enter department code to generate proper employee code."))
            if not employee.job_id or not employee.job_id.code:
                raise Warning(_("Please enter job title code to generate proper employee code."))

            last_emp_rec = self.env['hr.employee'].with_context(active_test=False).search(
                [('company_id','=',employee.company_id.id),('department_id','=',employee.department_id.id),
                ('job_id','=',employee.job_id.id),('id','!=',employee.id)])
            next_no = 0
            emp_code_no_lst = last_emp_rec.mapped('emp_code_no')
            if emp_code_no_lst:
                next_no = max(emp_code_no_lst)
            next_no +=1
            update_next_no = str(next_no).zfill(4)
            emp_code = employee.company_id.code + '-' + employee.department_id.code + '-' + employee.job_id.code + '-' + update_next_no
            if emp_code:
                employee.emp_code = emp_code
                employee.emp_code_no = next_no

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if self._context.get('show_emp_code'):
            args += ['|',('active','=',True),('active','=',False)]
        if name:
            recs = self.search([('emp_code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if self._context.get('show_emp_code') and record.emp_code and record.name:
                name = '[' + str(record.emp_code) + ']' + ' ' + record.name
            else:
                name = record.name
            result.append((record.id, name))
        return result


class res_company(models.Model):
    _inherit = "res.company"

    code = fields.Char(string="Code",copy=False)

    @api.constrains('code')
    def check_company_code(self):
        for each in self:
            if each.code:
                company_ids = self.env['res.company'].search_count([('code','=',each.code),('id','!=',each.id)])
                if company_ids >= 1:
                    raise Warning(_('Company code must be unique.'))


class hr_department(models.Model):
    _inherit = "hr.department"

    code = fields.Char(string="Code",copy=False)

    @api.constrains('code')
    def check_department_code(self):
        for each in self:
            if each.code:
                department_ids = self.env['hr.department'].search_count([('code','=',each.code),('id','!=',each.id)])
                if department_ids >= 1:
                    raise Warning(_('Department code must be unique.'))


class hr_job(models.Model):
    _inherit = "hr.job"

    code = fields.Char(string="Code",copy=False)

    @api.constrains('code')
    def check_job_code(self):
        for each in self:
            if each.code:
                job_ids = self.env['hr.job'].search_count([('code','=',each.code),('id','!=',each.id)])
                if job_ids >= 1:
                    raise Warning(_('Job title code must be unique.'))


class HrPayrollConfigSettings(models.TransientModel):
    _inherit = 'hr.payroll.config.settings'

    backdated_days = fields.Integer(string="Backdated Days")

    @api.model
    def get_default_backdated_days(self, fields):
        backdated_days = int(self.env["ir.config_parameter"].get_param("backdated_days"))
        return {'backdated_days': backdated_days}

    @api.multi
    def set_backdated_days(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("backdated_days", record.backdated_days)


class hr_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    month = fields.Selection([
        (1,'January'),(2,'February'),(3,'March'),(4,'April'),
        (5,'May'),(6,'June'),(7,'July'),(8,'August'),
        (9,'September'),(10,'October'),(11,'November'),(12,'December'),
        ],string="Month")


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        month = False
        if self.env.context.get('active_id'):
            month = self.env['hr.payslip.run'].browse(self.env.context.get('active_id')).month
        return super(HrPayslipEmployees, self.with_context(default_month=month)).compute_sheet()