# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError
from datetime import datetime, timedelta


class payslip_partial_payment(models.Model):
    _name = 'payslip.partial.payment'
    _description = 'Payslip Partial payment'

    name = fields.Char(string='Name',)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm')], default="draft", string="Status")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    acc_date = fields.Date(string="Accounting Date",default=fields.date.today())
    partial_payment_lines = fields.One2many('payslip.partial.payment.line','partial_payment_id',string="Partial Payment Line",copy=False)
    comment = fields.Text(string="Comment")

    @api.model
    def create(self,vals):
        backdated_days = int(self.env["ir.config_parameter"].get_param("backdated_days"))
        if backdated_days:
            acc_date = datetime.strptime(vals.get('acc_date'), '%Y-%m-%d').date()
            today_date = fields.datetime.now().date() - timedelta(days=backdated_days)
            if acc_date < today_date and not self.user_has_groups('eq_custom_payroll.group_allow_backdated_payslip'):
                raise UserError(_("You can't create backdated payslip payment. please contact to adminstrator."))
        return super(payslip_partial_payment,self).create(vals)

    def fetch_payslip(self):
        return {
            'name': 'Fetch Payslip Record',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.payslip.payment',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context':{'default_partial_payment_id':self.id}
        }

    def do_confirm(self):
        if not self.partial_payment_lines:
            raise Warning(_('No payment lines found.'))

        for line in self.partial_payment_lines:
            if not line.journal_id:
                raise Warning(_('Please configured payment journal in employee contract.'))
            if line.amount < 0:
                raise Warning(_('Amount should be positve.'))
            if line.other_charges < 0:
                raise Warning(_('Other Charges should be positve.'))
            if line.amount:
                line.generate_payment_move()
        self.state = 'confirm'

    def get_journal_data(self):
        journal_data = {}
        for line in self.partial_payment_lines.filtered(lambda l:l.journal_id):
            journal_data.setdefault(line.journal_id,0.00)
            journal_data[line.journal_id] += (line.total_paid_amount)
        return journal_data


class payslip_partial_payment_line(models.Model):
    _name = 'payslip.partial.payment.line'
    _description = 'Payslip Partial payment line'

    partial_payment_id = fields.Many2one('payslip.partial.payment',string="Partial Payment")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    remaining_amount = fields.Float(string="Remaining Amount")
    other_charges = fields.Float(string="Other Charges")
    amount = fields.Float(string="Amount Paid")
    payslip_id = fields.Many2one('hr.payslip',string="Payslip")
    journal_id = fields.Many2one('account.journal',string="Payment Journal")
    total_paid_amount = fields.Float(string="Total Paid Amount",compute='cal_paid_amount',store=True)
    emp_code = fields.Char(related='employee_id.emp_code',string="Employee Code",store=True)
    sr_no = fields.Integer(string="Sr#",compute='cal_sr_no')

    @api.depends('partial_payment_id.partial_payment_lines')
    def cal_sr_no(self):
        for line in self:
            no = 0
            for l in line.partial_payment_id.partial_payment_lines:
                no += 1
                l.sr_no = no

    @api.depends('amount','other_charges','employee_id','payslip_id')
    def cal_paid_amount(self):
        for each in self:
            each.total_paid_amount = (each.other_charges + each.amount)

    def generate_payment_move(self):
        self.ensure_one()
        payslip_obj = self.env['hr.payslip']
        partial_payment_id = self.partial_payment_id
        move_lines = []

        if not self.journal_id.default_debit_account_id or not self.journal_id.default_credit_account_id:
            raise Warning(_("Configured Payment Journal Credit and Debit Account!"))

        journal_rec = self.payslip_id.journal_id
        if journal_rec and not (journal_rec.default_debit_account_id or journal_rec.default_credit_account_id):
            raise Warning(_('Journal have should be configured Credit and Debit Account.!'))

        credit_vals = {
            'name': 'Salary Paid',
            'debit': 0.0,
            'credit': abs(self.total_paid_amount),
            'account_id':self.journal_id.default_credit_account_id.id,
        }
        move_lines.append((0, 0, credit_vals))

        debit_vals = {
                'name': self.payslip_id.name,
                'debit': abs(self.total_paid_amount),
                'credit': 0.0,
                'account_id': journal_rec.default_debit_account_id.id,
            }
        move_lines.append((0, 0, debit_vals))

        vals = {
            'journal_id': self.journal_id.id,
            'date': partial_payment_id.acc_date or fields.date.today(),
            'state': 'draft',
            'line_ids': move_lines,
            'ref': self.employee_id.name + ' - ' + partial_payment_id.name,
            'narration':'Employee - '  + self.employee_id.name + ' Payslip Payment'
        }
        move = self.env['account.move'].sudo().create(vals)
        move.post()
        remaining_amount = self.payslip_id.remaining_amount - (abs(self.total_paid_amount))
        self.payslip_id.write({'payment_done': True,
            'remaining_amount':remaining_amount if remaining_amount >= 0 else 0.00})
        self.payslip_id.payment_move_ids += move
        return True


class wizard_payslip_payment(models.TransientModel):
    _name = 'wizard.payslip.payment'

    partial_payment_id = fields.Many2one('payslip.partial.payment',string="Partial Payment")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def do_confirm(self):
        payslip_ids = self.env['hr.payslip']
        # domain = [('company_id','=',self.partial_payment_id.company_id.id),('state','=','done'),('date_from','>=',self.start_date),('date_to','<=',self.end_date),('remaining_amount','>',0)]
        domain = [('company_id','=',self.partial_payment_id.company_id.id),('state','=','done'),('date_from','>=',self.start_date),('date_to','<=',self.end_date),('payment_done','=',False)]
        payslip_ids = payslip_ids.search(domain)
        if not payslip_ids:
            raise Warning(_('No payslip record found.'))
        lst = []
        for payslip in payslip_ids:
            if not payslip.contract_id.payment_journal_id:
                raise Warning(_('Please configured payment journal in employee contract.'))
            total_remaining_amount = payslip.remaining_amount
            lst.append((0,0,{'employee_id':payslip.employee_id.id,'journal_id':payslip.contract_id.payment_journal_id.id,
                'payslip_id':payslip.id,'remaining_amount':total_remaining_amount,'amount':total_remaining_amount}))

        self.partial_payment_id.partial_payment_lines.unlink()
        self.partial_payment_id.partial_payment_lines = lst

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: