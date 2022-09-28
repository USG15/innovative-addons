# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError


class construction_work_order(models.Model):
    _name = "construction.work.order"
    _description="Work Order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="Name",copy=False)
    area = fields.Char(string="Area")
    work_category_id = fields.Many2one('work.category',string="Work Category",track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",default='draft',track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    agreed_amount = fields.Monetary(string="Agreed Amount",track_visibility='onchange')
    work_order_ids = fields.One2many('construction.work.order.line', 'work_order_id', string='Work Order lines')
    comment = fields.Text(string="Comment")
    sub_workorders_count = fields.Integer(string="Sub Workorders Count",compute='cal_sub_workorders_count')
    approval_date =  fields.Date(string="Approval Date")
    total_progress_amount = fields.Monetary(string="Total Progress Amount",compute='cal_progress_amt')
    show_finish_button = fields.Boolean(string="Show Finish Button",compute='check_show_finish_button')

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state in ('confirm','approved', 'finished'))):
            raise Warning(_('You can only delete work order which are in draft stage.'))
        return super(construction_work_order, self).unlink()

    def check_show_finish_button(self):
        for order in self:
            show_finish_button = False
            sub_work_orders_count = sum(self.env['construction.sub.work.order'].search([('work_order_id','=',order.id)]).mapped('remaining_percentage'))
            if order.state == 'approved' and order.total_progress_amount >= order.agreed_amount:
                show_finish_button = True
            order.show_finish_button = show_finish_button

    def cal_progress_amt(self):
        for each in self:
            total_progress_amount = 0.00
            sub_work_order_ids = self.env['construction.sub.work.order'].search([('work_order_id','=',each.id)])
            if sub_work_order_ids:
                progress_order_ids = self.env['construction.sub.work.order.line'].search([('sub_work_order_id','in',sub_work_order_ids.ids),('state','=','confirm')])
                total_progress_amount = sum(progress_order_ids.mapped('amount'))
            each.total_progress_amount = total_progress_amount
            
    def cal_sub_workorders_count(self):
        for each in self:
            each.sub_workorders_count = self.env['construction.sub.work.order'].search_count([('work_order_id','=',each.id)])

    @api.constrains('agreed_amount')
    def check_agreed_amount(self):
        for each in self:
            if each.agreed_amount <=0:
                raise ValidationError(_('Please enter ageed amount.'))

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
        lines_amount = sum(self.work_order_ids.mapped('amount'))
        if self.agreed_amount != lines_amount:
            raise ValidationError(_('Work order agreed amount and work order lines amount should be match.'))

        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('construction.work.order')
        
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
        sub_work_order_ids = self.env['construction.sub.work.order'].search([('work_order_id','=',self.id)])
        default_vals = {'default_work_category_id':self.work_category_id.id,'default_company_id':self.company_id.id,
            'default_work_order_id':self.id,'default_amount':self.agreed_amount}
        action = self.env.ref('eq_construction_mgt.action_construction_sub_work_order').read()[0]
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
                'res_model':'construction.work.order.activity',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{'default_work_order_id':self.id,'default_wizard_activity_ids':lst}
            }


class construction_work_order_line(models.Model):
    _name = "construction.work.order.line"

    name = fields.Char(string="Name",copy=False)
    description = fields.Char(string="Description")
    work_order_id = fields.Many2one('construction.work.order',string="Category")
    company_id = fields.Many2one('res.company',related='work_order_id.company_id',string="Company",store=True)
    currency_id = fields.Many2one('res.currency',related='work_order_id.currency_id',string="Currency",store=True)
    percentage = fields.Float(string="Percentage(%)")
    amount = fields.Monetary(string="Amount")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",related='work_order_id.state',store=True)
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Workorder")
    activity_done = fields.Boolean(string="Activity Done",copy=False,compute='cal_done_percentage',store=True)
    done_percentage = fields.Float(string="Done Percentage(%)",copy=False)

    @api.depends('done_percentage')
    def cal_done_percentage(self):
        for each in self:
            activity_done = False
            if each.done_percentage >= 100:
                activity_done = True
            each.activity_done = activity_done

    @api.onchange('percentage')
    def onchange_percentage_field(self):
        agreed_amount = self.work_order_id.agreed_amount
        if agreed_amount:
            self.amount = ((agreed_amount * self.percentage) / 100)

    @api.multi
    def generate_sub_wo_order(self):
        if self.work_order_id:
            work_order_id = self.work_order_id
            default_vals = {'default_work_category_id':work_order_id.work_category_id.id,
            'default_work_order_id':work_order_id.id,'default_amount':self.amount}
            return{
                'name':'Sub Workorder',
                'type':'ir.actions.act_window',
                'res_model':'construction.sub.work.order',
                'view_id':self.env.ref('eq_construction_mgt.construction_sub_work_order_form_view').id,
                'view_type':'form',
                'view_mode':'form',
                'context':default_vals
            }

    @api.multi
    def show_sub_wo_order(self):
        if self.work_order_id and self.sub_work_order_id:
            return{
                'name':'Sub Workorder',
                'type':'ir.actions.act_window',
                'res_model':'construction.sub.work.order',
                'view_id':self.env.ref('eq_construction_mgt.construction_sub_work_order_form_view').id,
                'view_type':'form',
                'view_mode':'form',
                'res_id':self.sub_work_order_id.id,
            }


class construction_sub_work_order(models.Model):
    _name = "construction.sub.work.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description="Sub Work Order"

    name = fields.Char(string="Name")
    work_category_id = fields.Many2one('work.category',string="Work Category",track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",default='draft',track_visibility='onchange')
    sub_work_order_ids = fields.One2many('construction.sub.work.order.line', 'sub_work_order_id', string='Progress')
    order_date = fields.Date(string="Order Date",default=fields.date.today(),track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner',string="Vendor",track_visibility='onchange')
    work_order_id = fields.Many2one('construction.work.order',string="Work Order",track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    # sub_work_other_ids = fields.One2many('construction.sub.work.other.line', 'sub_work_order_id', string='Work Order lines')
    progress_workorders_count = fields.Integer(string="Progress Count",compute='cal_progress_count')
    project_id = fields.Many2one('project.project',string="Project",track_visibility='onchange')
    activity_id = fields.Many2one('construction.work.order.line',string="Activity",track_visibility='onchange')
    remaining_percentage = fields.Float(string="Remaining Percentage",compute="cal_remaining_percentage")
    show_finish_button = fields.Boolean(string="Show Finish Button",compute='check_show_finish_button')
    total_progress_amount = fields.Monetary(string="Total Amount",compute='cal_progress_amt')

    def cal_progress_amt(self):
        for each in self:
            total_progress_amount = 0.00
            progress_order_ids = self.env['construction.sub.work.order.line'].search([('sub_work_order_id','=',each.id),('state','=','confirm')])
            total_progress_amount = sum(progress_order_ids.mapped('amount'))
            each.total_progress_amount = total_progress_amount

    def check_show_finish_button(self):
        for order in self:
            show_finish_button = False
            if order.state == 'approved' and order.remaining_percentage <=0.00:
                show_finish_button = True
            order.show_finish_button = show_finish_button

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state in ('confirm','approved', 'finished'))):
            raise Warning(_('You can only delete work order which are in draft stage.'))
        return super(construction_sub_work_order, self).unlink()

    def cal_remaining_percentage(self):
        for each in self:
            each.remaining_percentage =  (100 - sum(self.env['construction.sub.work.order.line'].search([('sub_work_order_id','=',each.id),('state','=','confirm')]).mapped('percentage')))

    def cal_progress_count(self):
        for each in self:
            progress_workorders_count = self.env['construction.sub.work.order.line'].search_count([('sub_work_order_id','=',each.id)])
            each.progress_workorders_count = progress_workorders_count

    @api.constrains('work_order_id','state')
    def check_activity_progress_status(self):
        for each in self:
            sub_work_order_id = self.env['construction.sub.work.order'].search([('work_order_id','=',each.work_order_id.id),('id','!=',each.id),('state','!=','finished')],limit=1)
            if sub_work_order_id:
                raise ValidationError(_("You can't start new activity untill finish previous activity."))

    def do_confirm(self):
        if not self.activity_id:
            raise Warning(_('Please select activity.'))
        self.state ='confirm'

    def do_approval(self):
        if not self.activity_id:
            raise Warning(_('Please select activity.'))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('sub.construction.work.order') 
        self.write({'state':'approved'})

    @api.onchange('work_order_id')
    def onchange_work_order_id_field(self):
        lst = []
        self.work_category_id = False
        self.work_category_id = self.work_order_id.work_category_id.id

    @api.multi
    def action_view_progress(self):
        progress_order_ids = self.env['construction.sub.work.order.line'].search([('sub_work_order_id','=',self.id)])
        default_vals = {'default_sub_work_order_id':self.id,'default_sub_activity_id':self.activity_id.id,
        'default_company_id':self.company_id.id}
        action = self.env.ref('eq_construction_mgt.action_construction_sub_work_order_line').read()[0]
        action['domain'] = [('id','in',progress_order_ids.ids)]
        action['context'] = default_vals
        return action

    def open_activity(self):
        if self.work_order_id:
            lst = []
            for lines in self.work_order_id.work_order_ids.filtered(lambda l:not l.activity_done):
                lst.append((0,0,{'work_activity_id':lines.id,'work_order_id':self.work_order_id.id}))
            return{
                'name':'Choose Subwork',
                'type':'ir.actions.act_window',
                'res_model':'construction.work.activity',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{'default_work_order_id':self.work_order_id.id,'default_sub_work_order_id':self.id,'default_wizard_activity_ids':lst}
            }
        
    @api.multi
    def do_finished(self):
        if not self.activity_id:
            raise Warning(_('Please select activity.'))
        self.write({'state':'finished'})

    def do_open(self):
        return{
            'name':'Service Sub Work Order',
            'type':'ir.actions.act_window',
            'res_model':'construction.sub.work.order',
            'view_type':'form',
            'view_mode':'form',
            'res_id':self.id,
            'target':'current',
        }


class construction_sub_work_order_line(models.Model):
    _name = "construction.sub.work.order.line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="Name",copy=False)
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order",track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)
    amount = fields.Monetary(string="Amount")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm')],string="Status",default='draft',track_visibility='onchange')
    done_date = fields.Date(string="Done Date",default=fields.date.today(),track_visibility='onchange')
    percentage = fields.Float(string="Percentage(%)",track_visibility='onchange')
    # sub_activity_id = fields.Many2one('construction.sub.work.other.line',string="Sub Activity",track_visibility='onchange')
    invoice_id = fields.Many2one('account.invoice',string="Vendor Bill")
    sub_activity_id = fields.Many2one('construction.work.order.line',string="Activity",track_visibility='onchange')

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda l: l.state == 'confirm')):
            raise Warning(_('You cannot delete progress record which is confirmed.'))
        return super(construction_sub_work_order_line, self).unlink()

    @api.onchange('sub_work_order_id')
    def change_sub_work_order_id_field(self):
        if not self.env.context.get('default_sub_work_order_id'):
            self.sub_activity_id = False
        return {'domain':{'sub_activity_id':[('activity_done','!=',True),('id','=',self.sub_work_order_id.activity_id.id)]}}

    @api.constrains('percentage')
    def check_percentage(self):
        for each in self:
            if each.percentage <=0 or each.percentage > 100:
                raise ValidationError(_('Please enter proper percentage.'))

            progress_ids = self.env['construction.sub.work.order.line'].search([('sub_activity_id','=',each.sub_activity_id.id)])
            if progress_ids:
                if len(progress_ids) > 1:
                    progress_ids = progress_ids.filtered(lambda l:l.state == 'confirm')
                    total_progress_percentage = sum(progress_ids.mapped('percentage')) + each.percentage
                    if total_progress_percentage > 100:
                        raise ValidationError(_("You can't consume percentage more than define in workorder activity percentage."))
                else:
                    total_progress_percentage = sum(progress_ids.mapped('percentage'))
                    if total_progress_percentage > 100:
                        raise ValidationError(_("You can't consume percentage more than define in workorder activity percentage."))

    @api.onchange('percentage','sub_activity_id')
    def onchange_percentage_field(self):
        amount = self.sub_activity_id.amount
        if amount:
            self.amount = ((amount * self.percentage) / 100)

    def do_confirm(self):
        if self.percentage <=0 or self.percentage > 100:
            raise Warning(_('Please enter proper percentage.'))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('construction.sub.work.order.line')
        invoice_id = self.generate_vendor_bill()
        self.sub_activity_id.done_percentage += self.percentage
        if invoice_id:
            self.write({'state':'confirm','invoice_id':invoice_id.id,'done_date':fields.date.today()})

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
            'invoice_line_ids':[(0,0,{'name':self.sub_activity_id.name,'account_id':account.id,
                'price_unit':self.amount,'quantity':1,'sub_work_order_id':self.sub_work_order_id.name,
                'project_id':self.sub_work_order_id.project_id.id})]
        }
        invoice_id = invoice_id.with_context(ctx).create(vals)
        invoice_id._onchange_partner_id()
        invoice_id._onchange_journal_id()
        invoice_id._onchange_payment_term_date_invoice()
        invoice_id.action_invoice_open()
        return invoice_id


class construction_sub_work_other_line(models.Model):
    _name = "construction.sub.work.other.line"
    _rec_name = 'activity_id'

    activity_id = fields.Many2one('construction.work.order.line',string="Name",required=True)
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Category")
    amount = fields.Float(string="Amount",required=True)


class construction_work_activity(models.TransientModel):
    _name = "construction.work.activity"

    work_order_id = fields.Many2one('construction.work.order',string="Work Order")
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order")
    wizard_activity_ids = fields.One2many('construction.work.activity.line', 'wizard_work_activity_id', string='Wizard Activity')
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

            if len(self.wizard_activity_ids.filtered(lambda l:l.select)) > 1:
                raise Warning(_("You can't select more than one activity."))

            activity_id = self.wizard_activity_ids.filtered(lambda l:l.select)[0]
            self.sub_work_order_id.write({'activity_id':activity_id.work_activity_id.id})


class construction_work_activity_line(models.TransientModel):
    _name = "construction.work.activity.line"

    select = fields.Boolean(string="Select")
    work_activity_id = fields.Many2one('construction.work.order.line',string="Activity")
    work_order_id = fields.Many2one('construction.work.order',string="Work Order")
    wizard_work_activity_id = fields.Many2one('construction.work.activity',string="Wizard WO Activity")



class construction_work_order_activity(models.TransientModel):
    _name = "construction.work.order.activity"

    work_order_id = fields.Many2one('construction.work.order',string="Work Order")
    wizard_activity_ids = fields.One2many('construction.work.order.activity.line', 'wizard_work_order_activity_id', string='Wizard Activity')
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


class construction_work_order_activity_line(models.TransientModel):
    _name = "construction.work.order.activity.line"

    select = fields.Boolean(string="Select")
    wizard_work_order_activity_id = fields.Many2one('construction.work.order.activity',string="Wizard WO Activity")
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")


class project_project(models.Model):
    _inherit = 'project.project'

    # @api.multi
    # def _get_project_data(self):
    #     print "\n\n- -_get_project_data---",self
    #     lst = []
    #     workorder_exp_cat_ids = self.env['project.workorder.exp.cat']
    #     for project in self:
    #         service_work_order_ids = self.env['construction.sub.work.order'].search([('project_id','=',project.id)])
    #         finished_work_order_ids = self.env['finished.sub.work.order'].search([('project_id','=',project.id)])
            
    #         for service_work_order in service_work_order_ids:
    #             vals = {'name':service_work_order.name,'project_id':project.id,'service_sub_work_order_id':service_work_order.id}
    #             workorder_exp_cat_ids |= self.env['project.workorder.exp.cat'].create(vals)
    #             # lst.append((0,0,vals))

    #         # for finish_work_order in finished_work_order_ids:
    #         #     vals = {'name':finish_work_order.name,'project_id':project.id,'finished_sub_work_order_id':finish_work_order.id}
    #             # self.env['project.workorder.exp.cat'].create(vals)
    #             # lst.append(vals)
            

    #         print "\n\n- -lst---",lst

    #         # workorder_exp_cat_ids = self.env['project.workorder.exp.cat'].create(lst)
    #         print "\n\n --workorder_exp_cat_ids---",workorder_exp_cat_ids
    #         for line in workorder_exp_cat_ids:
    #             print "\n\n- -line---",line,line.name,line.project_id
    #         # project.workorder_exp_cat_ids = lst

    project_type = fields.Selection([('Own','Own'),('Rental','Rental'),('Third Party','Third Party')],string="Project Type") 
    picking_ids = fields.One2many('stock.picking','project_id',string="Pickings",domain=[('state', '=', 'done')])
    workorder_exp_cat_ids = fields.One2many('project.workorder.exp.cat','project_id',string="Work Order")
    # project_data = fields.Boolean(string="Pickings",compute='_get_project_data')
    service_sub_work_order_ids = fields.One2many('construction.sub.work.order','project_id',string="Construction Work Order",
        domain=[('state', 'in', ('approved','finished'))])
    finished_sub_work_order_ids = fields.One2many('finished.sub.work.order','project_id',string="Finished Sub Work Order",
        domain=[('state', 'in', ('approved','finished'))])


class project_workorder_exp_cat(models.Model):
    _name = "project.workorder.exp.cat"
    _description = "Project Workorder Lines"

    name = fields.Char(string="Name")
    project_id = fields.Many2one('project.project',string="Project")
    service_sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Service Sub Work Order")
    finished_sub_work_order_id = fields.Many2one('finished.sub.work.order',string="Finished Sub Work Order")