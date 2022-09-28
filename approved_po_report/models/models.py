# -*- coding: utf-8 -*-

from odoo import models, fields, api
class Usman(models.Model):
    _inherit="sale.order"

    name_idsss = fields.Char

# class approved_po_report(models.Model):
#     _name = 'approved_po_report.approved_po_report'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100