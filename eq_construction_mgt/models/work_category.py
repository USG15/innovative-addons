# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError


class work_category(models.Model):
    _name = "work.category"

    name = fields.Char(string="Name")
    sub_work_category_ids = fields.One2many('sub.work.category', 'work_category_id', string='Sub Work Category')
    is_finished_wo = fields.Boolean(string="Finished Work Order") 


class sub_work_category(models.Model):
    _name = "sub.work.category"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    work_category_id = fields.Many2one('work.category',string="Category")
    is_finished_wo = fields.Boolean(string="Finished Work Order")

    @api.onchange('is_finished_wo')
    def onchange_is_finished_wo(self):
        self.work_category_id = False
        if self.is_finished_wo:
            return {'domain':{'work_category_id':[('is_finished_wo','=',True)]}}
        else:
            return {'domain':{'work_category_id':[('is_finished_wo','=',False)]}}
