# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta
import calendar


class rental_registration(models.Model):
    _name = "rental.registration"
    _description="Rental Contract Registration"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_rental_days(self):
        return [('1', 'Every 1'), ('2', 'Every 2'), ('3', 'Every 3'), ('4', 'Every 4'), ('5', 'Every 5'), ('6', 'Every 6'), ('7', 'Every 7'), ('8', 'Every 8'), ('9', 'Every 9'), ('10', 'Every 10'), ('11', 'Every 11'), ('12', 'Every 12'), ('13', 'Every 13'), ('14', 'Every 14'), ('15', 'Every 15'), ('16', 'Every 16'), ('17', 'Every 17'), ('18', 'Every 18'), ('19', 'Every 19'), ('20', 'Every 20'), ('21', 'Every 21'), ('22', 'Every 22'), ('23', 'Every 23'), ('24', 'Every 24'), ('25', 'Every 25'), ('26', 'Every 26'), ('27', 'Every 27'), ('28', 'Every 28'), ('29', 'Every 29'), ('30', 'Every 30'),('31', 'Every 31')]

    name = fields.Char(string="Name",copy=False)
    partner_id = fields.Many2one('res.partner',string="Partner")
    project_id = fields.Many2one('project.project',string="Project")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    security_deposite_amt = fields.Monetary(string="Security")
    advance_rent_month = fields.Integer(string="Advance Rent Month",default=1)
    rental_due_date = fields.Selection(_get_rental_days,string="Rental Due Date")
    monthly_rent_amt = fields.Monetary(string="Monthly Rental")
    document_status = fields.Selection([('Completed','Completed'),('Pending','Pending')],string="Document Status",default='Pending',track_visibility='onchange')
    registration_lines = fields.One2many('rental.registration.line', 'rental_registration_id', string='Registration Lines')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    contract_amt = fields.Monetary(string="Contract Amount",compute="cal_contract_amt",store=True)
    state = fields.Selection([('draft','Draft'),('confirm','Confirm')],string="Status",default='draft',track_visibility='onchange')
    vacation_date = fields.Date(string="Vacation Date")
    rent_payment_count = fields.Integer(string="Payment Count",compute='cal_rent_payment_count')

    @api.multi
    def action_view_payments(self):
        # default_vals = {'default_work_category_id':self.work_category_id.id,'default_company_id':self.company_id.id,
        #     'default_work_order_id':self.id,'default_amount':self.agreed_amount}
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('rental_registration_line_id','in',self.registration_lines.ids)]
        # action['context'] = default_vals
        return action

    @api.depends('registration_lines','registration_lines.payment_ids')
    def cal_rent_payment_count(self):
        for each in self:
            each.rent_payment_count = len(each.registration_lines.mapped('payment_ids'))

    @api.depends('registration_lines','registration_lines.amount')
    def cal_contract_amt(self):
        for each in self:
            each.contract_amt = sum(each.registration_lines.mapped('amount'))

    @api.multi
    def do_confirm(self):
        self.check_rental_validation()
        self.state = 'confirm'

    @api.constrains('start_date')
    def check_dates(self):
        current_date = datetime.today().date()
        for each in self:
            start_date = datetime.strptime(each.start_date, '%Y-%m-%d').date()
            if start_date < current_date:
                raise ValidationError(_('start date can not be before today.'))

    @api.multi
    def check_rental_validation(self):
        current_date = datetime.today().date()
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        if self.end_date < self.start_date:
            raise ValidationError(_('Please enter proper start date and end date.'))
        if self.security_deposite_amt < 0:
            raise ValidationError(_('Please enter proper security amount.'))
        if self.advance_rent_month < 0:
            raise ValidationError(_('Please enter proper advance rent month.'))
        if self.monthly_rent_amt < 0:
            raise ValidationError(_('Please enter proper monthly rental amount.'))

        if self.vacation_date:
            vacation_date = datetime.strptime(self.vacation_date, '%Y-%m-%d').date()
            if vacation_date <= start_date:
                raise ValidationError(_('vacation date should me greater than start date.'))

        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        if int(self.rental_due_date) > end_date.day:
            raise ValidationError(_('Please enter proper end date or rental due date.'))

    @api.multi
    def generate_schedule(self):
        self.check_rental_validation() 
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        if self.vacation_date:
            end_date = datetime.strptime(self.vacation_date, '%Y-%m-%d')

        # print "\n\n- -end_date---",end_date
        dates = [dt for dt in rrule(MONTHLY, dtstart=start_date,until=end_date)]
        #     last_day_per_month = calendar.monthrange(last_month_date.year, last_month_date.month)[-1]
        #     rental_perticular_day = 
        #     print "\n\n- --71--last_day_per_month---",last_day_per_month
        #     print "\n\n- --71--rental_perticular_day---",rental_perticular_day,end_date.day
        # if int(self.rental_due_date) > end_date.day:
        #     raise ValidationError(_('Please enter proper end date or rental due date.'))
        # print "\n\n --last_month_date---",last_month_date
        registration_lines = self.registration_lines.filtered(lambda l:not l.rental_payment == 'Paid')
        for line in registration_lines:
            line.payment_ids.filtered(lambda l:l.state == 'draft').unlink()
        registration_lines.unlink()
        lst = []
        current_date = datetime.today().date()
        for date in dates:
            months = datetime.strftime(date,'%B')
            last_day_per_month = calendar.monthrange(date.year, date.month)[-1]
            rental_perticular_day = int(self.rental_due_date)

            actual_month_days = last_day_per_month

            if last_day_per_month < rental_perticular_day:
                due_rental = date.replace(day=last_day_per_month)
            else:
                due_rental = date.replace(day=rental_perticular_day)

            if end_date.month == due_rental.month and end_date.year == due_rental.year:
                due_rental = date.replace(day=end_date.day)
                actual_month_days = end_date.day

            line_already_have = self.registration_lines.filtered(lambda l:l.date_month == due_rental.month and l.date_year == due_rental.year)

            if line_already_have:
                continue

            amount = ((self.monthly_rent_amt / last_day_per_month) * actual_month_days)
            vals = {'months':months,'due_rental':due_rental,'amount':amount,'received':0.00,
                'adjustment':0.00,'date_month':due_rental.month,'date_year':due_rental.year}
            lst.append((0,0,vals))
        self.write({'registration_lines': lst})
        return

    @api.model
    def create(self,vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('rental.registration')
        return super(rental_registration,self).create(vals)

    # @api.multi
    # def unlink(self):
    #     if any(self.filtered(lambda l: l.state in ('confirm','approved','finish'))):
    #         raise Warning(_('You can only delete records which are in draft stage.'))
    #     return super(po_approve_demand, self).unlink()


class rental_registration_line(models.Model):
    _name = "rental.registration.line"
    _description="Rental Contract Registration Lines"

    rental_registration_id = fields.Many2one('rental.registration',string="Rental Registration")
    sr_no = fields.Integer(string="Schedule",compute='cal_sr_no')
    months = fields.Char(String="Months")
    due_rental = fields.Date(string="Due Rental")
    amount = fields.Monetary(string="Amounts")
    rental_payment = fields.Selection([('Paid','Paid'),('Due','Due'),('Not Due','Not Due'),('Pending','Pending')],string="Status",compute='cal_rental_payment',store=True)
    received = fields.Monetary(string="Received")
    adjustment = fields.Monetary(string="Adjustment")
    pending = fields.Monetary(string="Pending",compute='cal_pending_amt',store=True)
    company_id = fields.Many2one('res.company',string="Company",related='rental_registration_id.company_id',store=True)
    currency_id = fields.Many2one('res.currency',related='rental_registration_id.currency_id',string="Currency",store=True)
    date_month = fields.Integer(String="Date Months")
    date_year = fields.Integer(String="Date Year")
    payment_ids = fields.One2many('account.payment', 'rental_registration_line_id',string='Account Payment')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm')],string="Status",related="rental_registration_id.state",store=True)

    @api.depends('due_rental','amount','received','adjustment')
    def cal_rental_payment(self):
        for each in self:
            rental_payment = 'Not Due'
            current_date = datetime.today().date()
            # current_date = datetime.strptime(each.rental_registration_id.start_date, '%Y-%m-%d').date()
            due_rental = datetime.strptime(each.due_rental, '%Y-%m-%d').date()
            if current_date.month == due_rental.month and current_date.year == due_rental.year:
                rental_payment = 'Due'
            if due_rental.month < current_date.month and  due_rental.year == current_date.year and each.received < each.amount:
                rental_payment = 'Pending'
            if due_rental.month > current_date.month and due_rental.year == current_date.year:
                rental_payment = 'Not Due'

            if each.received >= each.amount:
                rental_payment = 'Paid'

            if rental_payment:
                each.rental_payment = rental_payment

    @api.depends('rental_registration_id.registration_lines')
    def cal_sr_no(self):
        for line in self:
            no = 0
            for l in line.rental_registration_id.registration_lines:
                no += 1
                l.sr_no = no
    
    @api.depends('amount','received','rental_payment')
    def cal_pending_amt(self):
        for each in self:
            each.pending = 0.00
            if each.rental_payment == 'Due':
                each.pending = (each.amount - each.received)

    @api.multi
    def do_payment(self):
        vals = {'default_payment_type':'inbound','default_partner_id':self.rental_registration_id.partner_id.id,
            'default_payment_date':self.due_rental,'default_company_id':self.company_id.id,'default_currency_id':self.currency_id.id,
            'default_amount':(self.amount - self.pending),'default_rental_registration_line_id':self.id,
            'default_communication':self.rental_registration_id.name,'default_partner_type': 'customer'
            }
        if self.pending:
            vals['default_amount'] = self.pending
        return{
                'name':'Payments',
                'type':'ir.actions.act_window',
                'res_model':'account.payment',
                'view_type':'form',
                'view_mode':'form',
                'target':'current',
                'context':vals
            }


class account_payment(models.Model):
    _inherit = 'account.payment'

    rental_registration_line_id = fields.Many2one('rental.registration.line',string="Registration Line",copy=False)
    instrument_number = fields.Char(string="Instrument Number",copy=False)
    vendor_credit_account_id = fields.Many2one('account.account',string="Credit Account")

    @api.onchange('journal_id')
    def onchange_journal_id_field(self):
        if self.journal_id:
            self.vendor_credit_account_id = self.journal_id.default_credit_account_id.id or self.journal_id.default_debit_account_id.id

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        res = super(account_payment,self)._get_shared_move_line_vals(debit,credit,amount_currency,move_id,invoice_id)
        if self.rental_registration_line_id and self.rental_registration_line_id.rental_registration_id:
            res.update({'project_id':self.rental_registration_line_id.rental_registration_id.project_id.id})
        return res

    def _get_counterpart_move_line_vals(self, invoice=False):
        res = super(account_payment,self)._get_counterpart_move_line_vals(invoice)
        if self.instrument_number and self.payment_type == 'outbound':
            res.update({'name':self.instrument_number})
        return res

    def _get_liquidity_move_line_vals(self, amount):
        res = super(account_payment,self)._get_liquidity_move_line_vals(amount)
        if self.vendor_credit_account_id and self.payment_type == 'outbound':
            res.update({'account_id':self.vendor_credit_account_id.id})
        return res

    @api.multi
    def post(self):
        res = super(account_payment,self).post()
        for rec in self:
            if rec.rental_registration_line_id:
                rec.rental_registration_line_id.received += rec.amount
        return res