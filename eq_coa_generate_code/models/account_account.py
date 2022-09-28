# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError


class account_account(models.Model):
    _inherit = "account.account"

    coa_code_no = fields.Integer(string="COA Code No",copy=False)
    acc_sub_type_id = fields.Many2one('account.account.sub.type', string="Sub type")
    code = fields.Char(size=64, required=False, index=True)

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for account in self:
            name  = account.name
            if account.code:
                name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result

    @api.model
    def create(self,vals):
        res = super(account_account,self).create(vals)
        for account in res:
            account.generate_acc_code()
        return res

    @api.multi
    def write(self,vals):
        res = super(account_account,self).write(vals)
        if vals.get('company_id') or vals.get('acc_sub_type_id') or vals.get('user_type_id'):
            self.generate_acc_code()
        return res

    def generate_acc_code(self):
        for account in self:
            if not account.company_id or not account.company_id.acc_code_prefix:
                raise Warning(_("Please enter company coa prefix code to generate proper account code."))
            # if not account.user_type_id or not account.user_type_id.code:
            #     raise Warning(_("Please enter account type code to generate proper account code."))
            if not account.acc_sub_type_id or not account.acc_sub_type_id.code:
                raise Warning(_("Please enter account sub type code to generate proper account code."))

            last_acc_rec = self.env['account.account'].with_context(active_test=False).search(
                [('company_id','=',account.company_id.id),('id','!=',account.id)])
            next_no = 0
            coa_code_no_lst = last_acc_rec.mapped('coa_code_no')
            if coa_code_no_lst:
                next_no = max(coa_code_no_lst)
            next_no +=1
            update_next_no = str(next_no).zfill(4)
            acc_code = account.company_id.acc_code_prefix + '-' + account.acc_sub_type_id.code + '-' + update_next_no

            # acc_code = account.company_id.acc_code_prefix + '-' + account.user_type_id.code + '-' + account.acc_sub_type_id.code + '-' + update_next_no
            if acc_code:
                account.code = acc_code
                account.coa_code_no = next_no

            if not account.code:
                raise Warning(_('Please enter account code properly.'))


class res_company(models.Model):
    _inherit = "res.company"

    acc_code_prefix = fields.Char(string="COA code prefix",copy=False)
    # acc_type_code_prefix = fields.Char(string="Account Type code prefix",copy=False)
    # acc_sub_type_code_prefix = fields.Char(string="Account Sub type code prefix",copy=False)

    @api.constrains('acc_code_prefix')
    def check_company_coa_code(self):
        for each in self:
            if each.acc_code_prefix:
                company_ids = self.env['res.company'].search_count([('acc_code_prefix','=',each.acc_code_prefix),('id','!=',each.id)])
                if company_ids >= 1:
                    raise Warning(_('Company coa prefix code must be unique.'))

    # @api.constrains('acc_type_code_prefix')
    # def check_company_acc_type_code_prefix(self):
    #     for each in self:
    #         if each.acc_type_code_prefix:
    #             company_ids = self.env['res.company'].search_count([('acc_type_code_prefix','=',each.acc_type_code_prefix),('id','!=',each.id)])
    #             if company_ids >= 1:
    #                 raise Warning(_('Company accunt type code must be unique.'))

    # @api.constrains('acc_sub_type_code_prefix')
    # def check_company_acc_sub_type_code_prefix(self):
    #     for each in self:
    #         if each.acc_sub_type_code_prefix:
    #             company_ids = self.env['res.company'].search_count([('acc_sub_type_code_prefix','=',each.acc_sub_type_code_prefix),('id','!=',each.id)])
    #             if company_ids >= 1:
    #                 raise Warning(_('Company sub type accunt code must be unique.'))


class account_account_type(models.Model):
    _inherit = "account.account.type"

    code = fields.Char(string="Code",copy=False)
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env['res.company']._company_default_get('account.account'))
    acc_type_code_no = fields.Integer(string="Acc type code no",copy=False)

    @api.constrains('code')
    def check_account_type_code(self):
        for each in self:
            if each.code:
                account_type_ids = self.env['account.account.type'].search_count([('code','=',each.code),('id','!=',each.id),('company_id','=',each.company_id.id)])
                if account_type_ids >= 1:
                    raise Warning(_('Type code must be unique.'))

    @api.model
    def create(self,vals):
        res = super(account_account_type,self).create(vals)
        for account_type in res:
            account_type.generate_account_type_code()
        return res

    def generate_account_type_code(self):
        for account_type in self:
            if not account_type.company_id:
                raise Warning(_("Please enter company in account type."))
            # if not account_type.company_id.acc_type_code_prefix:
            #     raise Warning(_("Please configured account type code in company."))

            last_account_type_rec = self.env['account.account.type'].search(
                [('company_id','=',account_type.company_id.id),('id','!=',account_type.id)])
            next_no = 0
            account_type_code_no_lst = last_account_type_rec.mapped('acc_type_code_no')
            if account_type_code_no_lst:
                next_no = max(account_type_code_no_lst)
            next_no +=1
            update_next_no = str(next_no).zfill(2)
            if update_next_no:
                # update_next_no = account_type.company_id.acc_type_code_prefix + '-' + update_next_no
                account_type.code = update_next_no
                account_type.acc_type_code_no = next_no

            if not account_type.code:
                raise Warning(_('Please enter account type code properly.'))


class account_account_sub_type(models.Model):
    _name = "account.account.sub.type"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code",copy=False)
    parent_id = fields.Many2one('account.account.sub.type', 'Parent Category', index=True, ondelete='cascade')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    sub_type_code_no = fields.Integer(string="Sub type code no",copy=False)
    child_id = fields.One2many('account.account.sub.type', 'parent_id', 'Child Categories')
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.user.company_id.id)
    account_account_type_id = fields.Many2one('account.account.type', string="Account Type")
    account_account_ids = fields.One2many('account.account', 'acc_sub_type_id', string="Accounts")
    currency_id = fields.Many2one('res.currency', string='Currency',related="company_id.currency_id")
    balance = fields.Monetary(string="Balance",compute='cal_balance')

    def cal_balance(self):
        for each in self:
            each.balance = sum(self.env['account.move.line'].search([('acc_sub_type_id','=',each.id)]).mapped('balance')) or 0.00

    @api.model
    def create(self,vals):
        res = super(account_account_sub_type,self).create(vals)
        for account_sub_type in res:
            account_sub_type.generate_acc_code()
        return res

    @api.multi
    def write(self,vals):
        res = super(account_account_sub_type,self).write(vals)
        if vals.get('parent_id'):
            self.generate_acc_code()
        return res

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive sub types.'))
        return True

    @api.constrains('code')
    def check_sub_type_code(self):
        for each in self:
            if each.code:
                sub_type_ids = self.env['account.account.sub.type'].search_count([('code','=',each.code),('company_id','=',each.company_id.id),('id','!=',each.id)])
                if sub_type_ids >= 1:
                    raise Warning(_('Sub type code must be unique.'))

    def generate_acc_code(self):
        for account_sub_type in self:
            if not account_sub_type.company_id:
                raise Warning(_("Please enter company in account sub type."))
            if account_sub_type.parent_id and not account_sub_type.parent_id.code:
                raise Warning(_("Please configured code in parent catrgories."))
            if account_sub_type.account_account_type_id and not account_sub_type.account_account_type_id.code:
                raise Warning(_("Please configured code in account type."))

            last_acc_rec = self.env['account.account.sub.type'].with_context(active_test=False).search(
                [('parent_id','=',account_sub_type.parent_id.id),('company_id','=',account_sub_type.company_id.id),('id','!=',account_sub_type.id)])
            next_no = 0
            acc_sub_type_code_no_lst = last_acc_rec.mapped('sub_type_code_no')
            if acc_sub_type_code_no_lst:
                next_no = max(acc_sub_type_code_no_lst)
            next_no +=1
            update_next_no = str(next_no).zfill(2)

            if account_sub_type.parent_id:
                acc_code = account_sub_type.parent_id.code + '-' + account_sub_type.account_account_type_id.code + '-' + update_next_no
            else:
                acc_code = account_sub_type.account_account_type_id.code + '-' + update_next_no
            if acc_code:
                account_sub_type.code = acc_code
                account_sub_type.sub_type_code_no = next_no

            if not account_sub_type.code:
                raise Warning(_('Please enter account code properly.'))

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.multi
    def generate_coa(self):
        return{
            'type':'ir.actions.act_window',
            'name':'Chart of Accounts',
            'res_model':'account.account',
            'view_type':'form',
            'view_mode':'form',
            'target':'current',
            'context':{'default_acc_sub_type_id':self.id,
                'default_user_type_id':self.account_account_type_id.id,
                'default_company_id':self.company_id.id}
        }



class account_move_line(models.Model):
    _inherit = 'account.move.line'

    acc_sub_type_id = fields.Many2one('account.account.sub.type', related='account_id.acc_sub_type_id', index=True, store=True,string="Sub Type")
