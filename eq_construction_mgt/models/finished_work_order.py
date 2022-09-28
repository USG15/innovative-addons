# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError


class finished_construction_work_order(models.Model):
    _name = "finished.construction.work.order"
    _description="Finished Work Order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="Name",copy=False)
    work_category_id = fields.Many2one('work.category',string="Work Category",track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",default='draft',track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    agreed_amount = fields.Monetary(string="Agreed Amount",track_visibility='onchange',compute='cal_agreed_amount',store=True)
    work_order_ids = fields.One2many('finished.construction.work.order.line', 'finished_work_order_id', string='Work Order lines')
    comment = fields.Text(string="Comment")
    sub_workorders_count = fields.Integer(string="Sub Workorders Count",compute='cal_sub_workorders_count')
    total_progress_amount = fields.Monetary(string="Total Progress Amount",compute='cal_progress_amt')
    show_finish_button = fields.Boolean(string="Show Finish Button",compute='check_show_finish_button')
    approval_date =  fields.Date(string="Approval Date",track_visibility='onchange')
    area = fields.Char(string="Area")

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state in ('confirm','approved', 'finished'))):
            raise Warning(_('You can only delete work order which are in draft stage.'))
        return super(finished_construction_work_order, self).unlink()

    @api.depends('work_order_ids','work_order_ids.amount')
    def cal_agreed_amount(self):
        for each in self:
            each.agreed_amount = sum(each.work_order_ids.mapped('amount'))

    def check_show_finish_button(self):
        for order in self:
            show_finish_button = False
            sub_workorder_ids = self.env['finished.sub.work.order'].search([('work_order_id','=',order.id)])
            total_remaining_amt = sum(sub_workorder_ids.mapped('total_remaining_amt'))
            if order.state == 'approved' and order.total_progress_amount >= order.agreed_amount:
                show_finish_button = True
            order.show_finish_button = show_finish_button

    def cal_progress_amt(self):
        for each in self:
            total_progress_amount = 0.00
            sub_workorder_ids = self.env['finished.sub.work.order'].search([('work_order_id','=',each.id)])
            if sub_workorder_ids:
                sub_workorder_progress_ids = self.env['finished.sub.work.order.progress'].search([('sub_work_order_id','in',sub_workorder_ids.ids),('state','=','confirm')])
                if sub_workorder_progress_ids:
                    total_progress_amount = sum(sub_workorder_progress_ids.mapped('invoice_total_amt'))
            each.total_progress_amount =  total_progress_amount

    def cal_sub_workorders_count(self):
        for each in self:
            each.sub_workorders_count = self.env['finished.sub.work.order'].search_count([('work_order_id','=',each.id)])

    def do_confirm(self):
        if not self.work_order_ids:
            raise Warning(_('Please enter work order lines.'))
        lines_amount = sum(self.work_order_ids.mapped('amount'))
        if self.agreed_amount != lines_amount:
            raise ValidationError(_('Work order agreed amount and work order lines amount should be match.'))
        self.state ='confirm'

    def do_approval(self):
        if not self.work_order_ids:
            raise Warning(_('Please enter work order lines.'))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('finished.construction.work.order')
        self.write({'state':'approved','approval_date':fields.Date.today()})

    def do_finished(self):
        if not self.work_order_ids:
            raise Warning(_('Please enter work order lines.'))
        lines_amount = sum(self.work_order_ids.mapped('amount'))
        if self.agreed_amount != lines_amount:
            raise ValidationError(_('Work order agreed amount and work order lines amount should be match.'))
        self.state = 'finished'

    @api.multi
    def action_view_sub_workorders(self):
        sub_work_order_ids = self.env['finished.sub.work.order'].search([('work_order_id','=',self.id)])
        default_vals = {'default_work_category_id':self.work_category_id.id,
            'default_work_order_id':self.id,'default_company_id':self.company_id.id}
        action = self.env.ref('eq_construction_mgt.action_finished_construction_sub_work_order').read()[0]
        action['domain'] = [('id','in',sub_work_order_ids.ids)]
        action['context'] = default_vals
        return action

    def open_activity(self):
        if self.work_category_id:
            lst = []
            for lines in self.work_category_id.sub_work_category_ids:
                lst.append((0,0,{'name':lines.name,'description':lines.description}))
            return{
                'name':'Choose Subwork',
                'type':'ir.actions.act_window',
                'res_model':'finished.construction.work.order.activity',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{'default_work_order_id':self.id,'default_wizard_activity_ids':lst}
            }


class finished_construction_work_order_line(models.Model):
    _name = "finished.construction.work.order.line"

    sr_no = fields.Integer(string="Sr#",compute='cal_sr_no')
    name = fields.Char(string="Name",copy=False)
    description = fields.Char(string="Description")
    finished_work_order_id = fields.Many2one('finished.construction.work.order',string="Category")
    company_id = fields.Many2one('res.company',related='finished_work_order_id.company_id',string="Company",store=True)
    currency_id = fields.Many2one('res.currency',related='finished_work_order_id.currency_id',string="Currency",store=True)
    qty = fields.Float(string="Qty",default=1)
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    sft = fields.Float(string="Unit",compute='cal_unit',store=True)
    total_sft = fields.Float(string="Total Measurement",compute='cal_total_sft',store=True)
    rate = fields.Monetary(string="Rate")
    amount = fields.Monetary(string="Amount",compute='cal_total_amt',store=True)
    activity_done = fields.Boolean(string="Activity Done",copy=False,compute='cal_done_amount',store=True)
    done_amount = fields.Float(string="Amount Done",copy=False)

    @api.depends('done_amount')
    def cal_done_amount(self):
        for each in self:
            activity_done = False
            if each.done_amount and each.amount and each.done_amount >= each.amount:
                activity_done = True
            each.activity_done = activity_done

    @api.depends('finished_work_order_id.work_order_ids')
    def cal_sr_no(self):
        for line in self:
            no = 0
            for l in line.finished_work_order_id.work_order_ids:
                no += 1
                l.sr_no = no

    @api.depends('total_sft','rate')
    def cal_total_amt(self):
        for each in self:
            each.amount = (each.total_sft * each.rate)

    @api.depends('width','length')
    def cal_unit(self):
        for each in self:
            each.sft = (each.width * each.length)

    @api.depends('sft','qty')
    def cal_total_sft(self):
        for each in self:
            each.total_sft = (each.sft * each.qty)


class finished_sub_work_order(models.Model):
    _name = "finished.sub.work.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description="Finished Sub Work Order"

    name = fields.Char(string="Name")
    work_category_id = fields.Many2one('work.category',string="Work Category",track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",default='draft',track_visibility='onchange')
    sub_work_order_ids = fields.One2many('finished.construction.sub.work.order.line', 'finished_sub_work_order_id', string='Progress')
    order_date = fields.Date(string="Order Date",default=fields.date.today(),track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner',string="Vendor",track_visibility='onchange')
    work_order_id = fields.Many2one('finished.construction.work.order',string="Work Order",track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    progress_workorders_count = fields.Integer(string="Progress Count",compute='cal_progress_count')
    project_id = fields.Many2one('project.project',string="Project",track_visibility='onchange')
    total_remaining_amt = fields.Monetary(string="Total Remaining Amount",compute="cal_remaining_amt")
    show_finish_button = fields.Boolean(string="Show Finish Button",compute='check_show_finish_button')
    total_progress_amount = fields.Monetary(string="Total Amount",compute='cal_progress_amt')

    def cal_progress_amt(self):
        for each in self:
            total_progress_amount = 0.00
            sub_workorder_progress_ids = self.env['finished.sub.work.order.progress'].search([('sub_work_order_id','=',each.id),('state','=','confirm')])
            if sub_workorder_progress_ids:
                total_progress_amount = sum(sub_workorder_progress_ids.mapped('invoice_total_amt'))
            each.total_progress_amount =  total_progress_amount

    def check_show_finish_button(self):
        for order in self:
            show_finish_button = False
            sub_workorder_progress_ids = self.env['finished.sub.work.order.progress'].search([('sub_work_order_id','=',order.id),('state','=','confirm')])
            if order.state == 'approved' and sub_workorder_progress_ids and not order.total_remaining_amt:
                show_finish_button = True
            order.show_finish_button = show_finish_button

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state in ('confirm','approved', 'finished'))):
            raise Warning(_('You can only delete sub work order which are in draft stage.'))
        return super(finished_sub_work_order, self).unlink()

    @api.multi
    def action_view_progress(self):
        progress_order_ids = self.env['finished.sub.work.order.progress'].search([('sub_work_order_id','=',self.id)])
        default_vals = {'default_sub_work_order_id':self.id,'default_company_id':self.company_id.id}
        action = self.env.ref('eq_construction_mgt.action_finished_sub_work_order_progress_sub').read()[0]
        action['domain'] = [('id','in',progress_order_ids.ids)]
        action['context'] = default_vals
        return action

    def cal_progress_count(self):
        for each in self:
            each.progress_workorders_count = self.env['finished.sub.work.order.progress'].search_count([('sub_work_order_id','=',each.id)])

    def cal_remaining_amt(self):
        for each in self:
            amount = 0.00
            for line in each.sub_work_order_ids:
                qty = abs(line.qty - line.received_qty)
                total_amount = line.finished_work_order_line_id.amount
                per_qty_amount = (line.finished_work_order_line_id.amount / line.finished_work_order_line_id.qty) * qty
                amount += per_qty_amount
            each.total_remaining_amt = amount

    def do_confirm(self):
        if not self.sub_work_order_ids:
            raise Warning(_('Please select activity.'))
        self.state ='confirm'

    def do_approval(self):
        if not self.sub_work_order_ids:
            raise Warning(_('Please select activity.'))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('finished.sub.work.order') 
        self.write({'state':'approved'})

    @api.onchange('work_order_id')
    def onchange_work_order_id_field(self):
        lst = []
        self.work_category_id = False
        self.work_category_id = self.work_order_id.work_category_id.id

    def open_activity(self):
        if self.work_order_id:
            lst = []
            exclude_work_order_ids = self.env['finished.construction.sub.work.order.line'].search([('finished_work_order_line_id','in',self.work_order_id.work_order_ids.ids)])
            for lines in self.work_order_id.work_order_ids.filtered(lambda l:not l.activity_done and l.id not in exclude_work_order_ids.mapped('finished_work_order_line_id').ids):
                lst.append((0,0,{'work_activity_id':lines.id,'work_order_id':self.work_order_id.id}))
            return{
                'name':'Choose Subwork',
                'type':'ir.actions.act_window',
                'res_model':'finished.construction.work.activity',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{'default_work_order_id':self.work_order_id.id,'default_sub_work_order_id':self.id,'default_wizard_activity_ids':lst}
            }
        
    @api.multi
    def do_finished(self):
        if not self.sub_work_order_ids:
            raise Warning(_('Please select activity.'))
        self.write({'state':'finished'})

    @api.multi
    def do_change_vendor(self):
        return{
                'name':'Change Vendor',
                'type':'ir.actions.act_window',
                'res_model':'wizard.change.vendor',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{'default_sub_work_order_id':self.id}
            }

    def do_open(self):
        return{
            'name':'Finished Sub Work Order',
            'type':'ir.actions.act_window',
            'res_model':'finished.sub.work.order',
            'view_type':'form',
            'view_mode':'form',
            'res_id':self.id,
            'target':'current',
        }


class finished_construction_sub_work_order_line(models.Model):
    _name = "finished.construction.sub.work.order.line"
    _rec_name = 'finished_work_order_line_id'

    finished_work_order_line_id = fields.Many2one('finished.construction.work.order.line',string="Activity")
    finished_sub_work_order_id = fields.Many2one('finished.sub.work.order',string="Finished Sub Work Order")
    to_be_received_qty = fields.Float(string="To Be Received",compute='cal_to_be_received_qty')
    qty = fields.Float(string="Qty")
    received_qty = fields.Float(string="Received Qty")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",related='finished_sub_work_order_id.state')
    activity_done = fields.Boolean(related='finished_work_order_line_id.activity_done',string="Activity Done",store=True)
    company_id = fields.Many2one('res.company',related='finished_sub_work_order_id.company_id',string="Company",store=True)
    currency_id = fields.Many2one('res.currency',related='finished_sub_work_order_id.currency_id',string="Currency",store=True)

    @api.depends('qty','received_qty')
    def cal_to_be_received_qty(self):
        for lines in self:
            if lines.received_qty > lines.qty:
                lines.to_be_received_qty = 0.00
            else:    
                lines.to_be_received_qty = abs(lines.qty - lines.received_qty)

    def do_swo_progress(self):
        if self.finished_sub_work_order_id:
            if self.activity_done:
                raise ValidationError(_("You can't use activity which is already done."))
            return{
                'name':'Progress',
                'type':'ir.actions.act_window',
                'res_model':'finished.sub.work.order.progress',
                'view_type':'form',
                'view_mode':'form',
                'target':'current',
                'context':{'default_activity_id':self.id,'default_sub_work_order_id':self.finished_sub_work_order_id.id}
            }


class finished_sub_work_order_progress(models.Model):
    _name = "finished.sub.work.order.progress"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description="Sub Work Order Progress"

    name = fields.Char(string="Name",copy=False)
    state = fields.Selection([('draft','Draft'),('confirm','Confirm')],string="Status",default='draft',track_visibility='onchange')
    activity_id = fields.Many2one('finished.construction.sub.work.order.line',string="Activity")
    sub_work_order_id = fields.Many2one('finished.sub.work.order',string="Sub Workorder")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    qty = fields.Float(string="Qty")
    done_date = fields.Date(string="Done Date",default=fields.date.today(),track_visibility='onchange')
    invoice_id = fields.Many2one('account.invoice',string="Vendor Bill")
    amount = fields.Monetary(string="Unit Price",compute='cal_unit_price',store=True)
    invoice_total_amt = fields.Monetary(string="Total Amount",compute='cal_invoice_total_amt',store=True)
    activity_done = fields.Boolean(related='activity_id.finished_work_order_line_id.activity_done',string="Activity Done",store=True)


    @api.onchange('sub_work_order_id')
    def change_sub_work_order_id_field(self):
        if not self.env.context.get('default_sub_work_order_id'):
            self.activity_id = False

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state == 'confirm')):
            raise Warning(_('You cannot delete progress record which is confirmed.'))
        return super(finished_sub_work_order_progress, self).unlink()

    @api.depends('qty','amount')
    def cal_invoice_total_amt(self):
        for each in self:
            each.invoice_total_amt = (each.qty * each.amount)

    @api.depends('qty','activity_id')
    def cal_unit_price(self):
        for each in self:
            work_order_line_id =each.activity_id.finished_work_order_line_id
            if work_order_line_id:
                each.amount = (work_order_line_id.amount / work_order_line_id.qty or 1)
            else:
                each.amount = 0.00

    @api.constrains('invoice_total_amt')
    def check_invoice_total_amt(self):
        for each in self:
            if each.state == 'draft':
                progress_ids = self.env['finished.sub.work.order.progress'].search([('activity_id','=',each.activity_id.id)])
                if progress_ids:
                    if len(progress_ids) > 1:
                        progress_ids = progress_ids.filtered(lambda l:l.state == 'confirm')
                        total_progress_amount = sum(progress_ids.mapped('invoice_total_amt')) + each.invoice_total_amt
                        if total_progress_amount > each.activity_id.finished_work_order_line_id.amount:
                            raise ValidationError(_("You can't consume amount more than define in workorder activity amount."))
                    else:
                        total_progress_amount = sum(progress_ids.mapped('invoice_total_amt'))
                        if total_progress_amount > each.activity_id.finished_work_order_line_id.amount:
                            raise ValidationError(_("You can't consume amount more than define in workorder activity amount."))


    def do_confirm(self):
        if self.qty <=0:
            raise Warning(_('Please enter proper qty.'))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('finished.sub.work.order.progress')

        invoice_id = self.generate_vendor_bill()
        if invoice_id:
            self.write({'state':'confirm','invoice_id':invoice_id.id,'done_date':fields.date.today(),'invoice_total_amt':invoice_id.amount_total})
            self.activity_id.received_qty += self.qty
            self.activity_id.finished_work_order_line_id.done_amount +=invoice_id.amount_total

    def generate_vendor_bill(self):
        invoice_id = self.env['account.invoice']
        ctx = {'default_type': 'in_invoice', 'type': 'in_invoice', 'journal_type': 'purchase','default_journal_type': 'purchase'}
        
        journal_id = self.env['account.journal'].search([('company_id','=',self.company_id.id),('type','=','purchase')], limit=1)
        if not journal_id:
            raise Warning(_('Please define purchase journal.'))
        account = journal_id.default_debit_account_id
        if not account:
            raise Warning(_('Please define debit account in purchase journal.'))

        vals={
            'partner_id':self.sub_work_order_id.vendor_id.id,
            'date_invoice':fields.date.today(),'journal_id':journal_id.id,
            'origin':self.name,'reference':self.name,
            'invoice_line_ids':[(0,0,{'name':self.activity_id.finished_work_order_line_id.name,'account_id':account.id,
                'price_unit':self.amount,'quantity':self.qty,'sub_work_order_id':self.sub_work_order_id.name,
                'project_id':self.sub_work_order_id.project_id.id})]
        }
        invoice_id = invoice_id.with_context(ctx).create(vals)
        invoice_id._onchange_partner_id()
        invoice_id._onchange_journal_id()
        invoice_id._onchange_payment_term_date_invoice()
        invoice_id.action_invoice_open()
        return invoice_id


class finished_construction_work_activity(models.TransientModel):
    _name = "finished.construction.work.activity"

    work_order_id = fields.Many2one('finished.construction.work.order',string="Work Order")
    sub_work_order_id = fields.Many2one('finished.sub.work.order',string="Sub Work Order")
    wizard_activity_ids = fields.One2many('finished.construction.work.activity.line', 'wizard_work_activity_id', string='Wizard Activity')
    select_type = fields.Selection([('check','Check All'),('uncheck','Uncheck All')],string="Select Type",default='uncheck')

    @api.onchange('select_type')
    def onchange_select_type_field(self):
        select = True if self.select_type == 'check' else False
        for each in self.wizard_activity_ids:
            each.select = select

    @api.multi
    def do_confirm(self):
        lst = []
        if self.sub_work_order_id and self.work_order_id and self.wizard_activity_ids:
            if all(not line.select for line in self.wizard_activity_ids):
                raise Warning(_("Please select atleast one subwork."))
            for lines in self.wizard_activity_ids.filtered(lambda l:l.select):
                if self.sub_work_order_id.sub_work_order_ids and self.sub_work_order_id.sub_work_order_ids.filtered(lambda l:l.finished_work_order_line_id.id == lines.work_activity_id.id):
                    continue
                lst.append((0,0,{'finished_work_order_line_id':lines.work_activity_id.id,'qty':lines.work_activity_id.qty}))

            self.sub_work_order_id.write({'sub_work_order_ids':lst})


class finished_construction_work_activity_line(models.TransientModel):
    _name = "finished.construction.work.activity.line"

    select = fields.Boolean(string="Select")
    work_activity_id = fields.Many2one('finished.construction.work.order.line',string="Activity")
    work_order_id = fields.Many2one('finished.construction.work.order',string="Work Order")
    wizard_work_activity_id = fields.Many2one('finished.construction.work.activity',string="Wizard WO Activity")


class finished_construction_work_order_activity(models.TransientModel):
    _name = "finished.construction.work.order.activity"

    work_order_id = fields.Many2one('finished.construction.work.order',string="Work Order")
    wizard_activity_ids = fields.One2many('finished.construction.work.order.activity.line', 'finished_wizard_work_order_activity_id', string='Wizard Activity')
    select_type = fields.Selection([('check','Check All'),('uncheck','Uncheck All')],string="Select Type",default='uncheck')

    @api.onchange('select_type')
    def onchange_select_type_field(self):
        select = True if self.select_type == 'check' else False
        for each in self.wizard_activity_ids:
            each.select = select

    @api.multi
    def do_confirm(self):
        if self.work_order_id and self.wizard_activity_ids:
            lst = []
            if all(not line.select for line in self.wizard_activity_ids):
                raise Warning(_("Please select atleast one sub workorder."))

            for lines in self.wizard_activity_ids.filtered(lambda l:l.select):
                if self.work_order_id.work_order_ids and self.work_order_id.work_order_ids.filtered(lambda l:l.name == lines.name):
                    continue
                lst.append((0,0,{'name':lines.name,'description':lines.description}))

            self.work_order_id.write({'work_order_ids':lst})


class finished_construction_work_order_activity_line(models.TransientModel):
    _name = "finished.construction.work.order.activity.line"

    select = fields.Boolean(string="Select")
    finished_wizard_work_order_activity_id = fields.Many2one('finished.construction.work.order.activity',string="Wizard WO Activity")
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")


class wizard_change_vendor(models.TransientModel):
    _name = "wizard.change.vendor"

    sub_work_order_id = fields.Many2one('finished.sub.work.order',string="Sub Work Order")
    vendor_id = fields.Many2one('res.partner',string="Vendor")
    reason = fields.Text(string="Reason")

    @api.multi
    def do_confirm(self):
        if self.sub_work_order_id and self.vendor_id:
            if self.sub_work_order_id.vendor_id.id != self.vendor_id.id:
                if self.reason:
                    self.sub_work_order_id.message_post(body='Vendor Change Reason: ' + self.reason)
                self.sub_work_order_id.write({'vendor_id':self.vendor_id.id})