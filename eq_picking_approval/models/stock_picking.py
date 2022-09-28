# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def verify_transfer(self):
        for picking in self:
            for operation in picking.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if not operation.qty_done:
                    raise UserError(_('Please enter done qty in operations.'))
            picking.done_varify_by_user = True
            picking.varify_user_id = self.env.user.id

    show_varify_button = fields.Boolean(string="Show Verify Button",compute='show_picking_approval_button')
    done_varify_by_user = fields.Boolean(string="Verify By User",copy=False)
    varify_user_id = fields.Many2one('res.users',string="Verify By",copy=False)
    show_validate_button = fields.Boolean(string="Show Validate Button",copy=False,compute='show_picking_approval_button')
    readonly_field_by_user = fields.Boolean(string="Readonly By User",copy=False,compute='readonly_field_for_user')

    @api.multi
    def readonly_field_for_user(self):
        readonly_field_by_user = False
        for picking in self:
            if picking.done_varify_by_user and picking.varify_user_id and picking.picking_type_code == 'incoming':
                if self.user_has_groups('eq_picking_approval.group_stock_receipt_approval') or self.env.user.id == picking.varify_user_id.id:
                    readonly_field_by_user = True
                if self.user_has_groups('stock.group_stock_manager'):
                    readonly_field_by_user = False
            picking.readonly_field_by_user = readonly_field_by_user

    @api.multi
    def show_picking_approval_button(self):
        show_varify_button = False
        show_validate_button = False
        for picking in self:
            if picking.state in ('assigned','assigned') and picking.picking_type_code == 'incoming':
                if self.user_has_groups('eq_picking_approval.group_stock_receipt_approval'):
                    show_varify_button = True

            if not show_varify_button or picking.done_varify_by_user:
                show_validate_button = True
            if picking.state in ('done','cancel'):
                show_validate_button = False

            picking.show_varify_button = show_varify_button
            picking.show_validate_button = show_validate_button