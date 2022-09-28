# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from datetime import datetime, timedelta
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError


class employee_adjustment_payment(models.Model):
    _name = 'employee.adjustment.payment'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Payslip Adjustment'

    name = fields.Char(string='Name',)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('approved','Approved'),('cancel', 'Cancel'),
                              ], default="draft", string="Status",track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    requested_date = fields.Date(string="Requested Date",default=fields.date.today())
    approval_date = fields.Date(string="Approval Date",copy=False)
    confirmation_date = fields.Date(string="Confirmation Date",copy=False)
    comment = fields.Char(string="Reason",track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee',string="Employee")
    # remaining_amount = fields.Float(string="Remaining Amount",copy=False)
    requested_amount = fields.Float(string="Requested Amount",copy=False)
    approved_amount = fields.Float(string="Approval Amount",copy=False)
    confirmation_amount = fields.Float(string="Confirmation Amount",copy=False)
    acc_move_id = fields.Many2one('account.move',string="Journal Entry",copy=False)
    journal_id = fields.Many2one('account.journal',string="Payment By")
    department_id = fields.Many2one('hr.department', string="Department",copy=False)
    job_id = fields.Many2one('hr.job', string='Job Title',copy=False)
    emp_code = fields.Char(related='employee_id.emp_code',string="Employee Code",store=True)
    debit_account_id = fields.Many2one('account.account',string="Debit Account")
    credit_account_id = fields.Many2one('account.account',string="Credit Account")
    adjustment_type = fields.Selection([('Receivable', 'Receivable'),
        ('Payable', 'Payable')], default="Payable", string="Type",track_visibility='onchange')

    @api.model
    def create(self,vals):
        backdated_days = int(self.env["ir.config_parameter"].get_param("backdated_days"))
        if backdated_days:
            requested_date = datetime.strptime(vals.get('requested_date'), '%Y-%m-%d').date()
            today_date = fields.datetime.now().date() - timedelta(days=backdated_days)
            if requested_date < today_date and not self.user_has_groups('eq_custom_payroll.group_allow_backdated_payslip'):
                raise UserError(_("You can't create backdated payslip adjustment. please contact to adminstrator."))

        vals['name'] = self.env['ir.sequence'].next_by_code('employee.adjustment.payment')
        if not vals['confirmation_amount']:
            vals['confirmation_amount'] = vals['requested_amount']
        return super(employee_adjustment_payment,self).create(vals)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.job_id = self.department_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id
            self.department_id = self.employee_id.department_id

    @api.constrains('requested_amount','confirmation_amount','approved_amount')
    def check_amount(self):
        for each in self:
            if not each.requested_amount:
                raise Warning(_('Please enter request amount.'))
            if each.requested_amount <0:
                raise Warning(_('Please enter proper request amount.'))
            if each.confirmation_amount <0:
                raise Warning(_('Please enter proper confirmation amount.'))
            if each.approved_amount <0:
                raise Warning(_('Please enter proper approved amount.'))
            if each.confirmation_amount > each.requested_amount:
                raise Warning(_("Confirmation amount can't higher than Requested Amount."))
            if each.approved_amount > each.confirmation_amount:
                raise Warning(_("Approval amount can't higher than Confirmation Amount."))

    @api.multi
    def do_confirm(self):
        if not self.confirmation_amount:
            raise Warning(_('Please enter confirmation amount.'))
        self.write({'state':'confirm','confirmation_date':datetime.now().date(),'approved_amount':self.confirmation_amount})

    @api.multi
    def do_approved(self):
        if not self.approved_amount:
            raise Warning(_('Please enter approval amount.'))
        self.generate_payment_move()
        if not self.approval_date:
            self.approval_date = datetime.now().date()
        self.write({'state':'approved'})

    @api.multi
    def do_cancel(self):
        if self.state == 'approved':
            raise Warning(_("You can't cancel record becuase it it in approved state."))
        self.write({'state':'cancel'})

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state in ('approved', 'cancel'))):
            raise Warning(_('You cannot delete a record which is approved or cancelled!'))
        return super(employee_adjustment_payment, self).unlink()

    def generate_payment_move(self):
        self.ensure_one()
        move_lines = []
        
        credit_vals = {
            'name': 'Payslip Adjustment- ' + self.comment,
            'debit': 0.0,
            'credit': abs(self.approved_amount),
            'account_id': self.credit_account_id.id,
        }
        move_lines.append((0, 0, credit_vals))

        debit_vals = {
                'name': self.employee_id.name + ' - ' + self.name,
                'debit': abs(self.approved_amount),
                'credit': 0.0,
                'account_id':self.debit_account_id.id,
            }
        move_lines.append((0, 0, debit_vals))

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.approval_date or fields.date.today(),
            'state': 'draft',
            'line_ids': move_lines,
            'ref': self.employee_id.name + ' - ' + self.name,
            'narration':'Employee - '  + self.employee_id.name + ' Payslip Adjustment'
        }
        move = self.env['account.move'].sudo().create(vals)
        move.post()
        self.acc_move_id = move.id
        return True

    @api.multi
    def action_view_entries(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id','=',self.acc_move_id.id)]
        action['context'] = {}
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: