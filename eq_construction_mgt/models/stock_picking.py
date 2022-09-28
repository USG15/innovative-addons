    # -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_compare, float_round
from datetime import datetime


class stock_picking(models.Model):
    _inherit = "stock.picking"

    cons_type = fields.Selection([('1','1 Option'),('2','2 Option')],string="Type",copy=False)
    project_id = fields.Many2one('project.project',string="Project",copy=False)
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order",copy=False)
    hide_customer = fields.Boolean(string="Hide Customer",related='picking_type_id.hide_customer',store=True)
    return_picking = fields.Boolean(string="Return Picking",default=False,copy=False)
    invoice_id = fields.Many2one('account.invoice',string="Invoice", copy=False)
    amount = fields.Float(string="Amount",compute='cal_transfer_amt')

    def cal_transfer_amt(self):
        for picking in self:
            total_amount = 0.00
            for move in picking.move_lines:
                total_amount += (move.product_qty * move.price_unit)
            picking.amount = total_amount

    def do_open(self):
        return{
            'name':'Goods Issuance Note',
            'type':'ir.actions.act_window',
            'res_model':'stock.picking',
            'view_type':'form',
            'view_mode':'form',
            'res_id':self.id,
            'target':'current',
        }

    @api.multi
    def open_multi_products_wiz(self):
        return{
            'name':'Multi Products',
            'type':'ir.actions.act_window',
            'res_model':'picking.multi.product.selection',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'context':{'default_picking_id':self.id}
        }

    @api.model
    def default_get(self,fieldslist):
        res =super(stock_picking,self).default_get(fieldslist)
        if self.env.context.get('set_picking_type'):
            warehouse_id = self.env['stock.warehouse'].search([('company_id','=',self.env.user.company_id.id)],limit=1)
            picking_type_id = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse_id.id),
                ('code','=',self.env.context.get('set_picking_type'))],limit=1)
            if picking_type_id:
                res['picking_type_id'] = picking_type_id.id
        return res

    @api.onchange('cons_type')
    def onchange_cons_type(self):
        self.sub_work_order_id = False
        self.origin = False

    # @api.onchange('sub_work_order_id')
    # def onchange_sub_work_order_id_field(self):
    #     if self.sub_work_order_id:
    #         self.origin = self.sub_work_order_id.work_order_id.name

    @api.multi
    def write(self,vals):
        if vals.get('sub_work_order_id'):
            record_id = self.env['construction.sub.work.order'].sudo().browse(vals.get('sub_work_order_id'))
            vals['origin'] = record_id.work_order_id.name
        return super(stock_picking,self).write(vals)

    @api.model
    def create(self,vals):
        if vals.get('sub_work_order_id'):
            record_id = self.env['construction.sub.work.order'].sudo().browse(vals.get('sub_work_order_id'))
            vals['origin'] = record_id.work_order_id.name
        return super(stock_picking,self).create(vals)

    @api.multi
    def generate_vendor_bill(self):
        if not self.move_lines:
            return
        if self.invoice_id:
            return
        invoice_type = 'in_invoice'
        journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
            ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise UserError(_('Please define an accounting journal for vendor bill.'))

        picking_ids = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        invoice_date = self.min_date or datetime.now().today().date()
        if not self.partner_id:
            raise ValidationError(_("Partner not found. For create bill, picking must have the partner."))

        user_id = self.env.user.id
        key = (self.partner_id.id, self.company_id.id, self.env.user)
        invoice_vals = self.with_context(journal_id=journal_id.id, invoice_date=invoice_date, invoice_type=invoice_type, user_id=user_id)._prepare_invoice()
        invoice_id = self.env['account.invoice'].create(invoice_vals)
        if invoice_id:
            for each in self.move_lines:
                if each.purchase_line_id:
                    invoice_id.write({'purchase_id': each.purchase_line_id.order_id.id})
                    invoice_id.with_context({'from_picking_done_qty': each.product_uom_qty})._prepare_invoice_line_from_po_line(each.purchase_line_id)
                    invoice_id.purchase_order_change()
            self.write({'invoice_id': invoice_id.id})
            invoice_id.compute_taxes()

            if not invoice_id.invoice_line_ids:
                invoice_id.sudo().unlink()
            else:
                invoice_id.action_invoice_open()

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        context = self.env.context
        invoice_vals = {
            'name': self.name,
            'type': context.get('invoice_type'),
            'partner_id': self.partner_id.id,
            'journal_id': context.get('journal_id'),
            'company_id': self.company_id.id,
            'date_invoice': context.get('invoice_date'),
            'stock_picking_ids': [(4, self.id)],
            'origin': self.origin,
            'user_id': context.get('user_id')
        }
        return invoice_vals

    @api.one
    @api.depends('move_lines.date_expected')
    def _compute_dates(self):
        self.min_date = min(self.move_lines.mapped('date_expected') or [datetime.now()])
        self.max_date = max(self.move_lines.mapped('date_expected') or [datetime.now()])


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection([
            ('draft','Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Posted'),
            ('paid', 'Completed'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(account_invoice, self)._prepare_invoice_line_from_po_line(line)
        if self.env.context.get('from_picking_done_qty'):
            data['quantity'] = self.env.context.get('from_picking_done_qty')
        data['discount'] = line.discount
        return data

    stock_picking_ids = fields.Many2many('stock.picking', 'table_account_invoice_stock_picking_relation', 'invoice_id', 'picking_id',
                                        string="Picking Ref.")

    @api.model
    def invoice_line_move_line_get(self):
        res = super(account_invoice,self).invoice_line_move_line_get()
        for line in self.invoice_line_ids:
            for x in res:
                if x.get('invl_id') and x['invl_id'] == line.id:
                    x.update({'project_id':line.project_id.id,'sub_work_order_id':line.sub_work_order_id})
        return res


class stock_picking_type(models.Model):
    _inherit = "stock.picking.type"

    hide_customer = fields.Boolean(string="Hide Customer",default=False)
    credit_account_id = fields.Many2one('account.account',string="Credit Account")
    debit_account_id = fields.Many2one('account.account',string="Debit Account")


class StockQuant(models.Model):
    _inherit = "stock.quant"

    product_cost = fields.Float(string="Rate",related='product_id.standard_price',store=True)

    def _account_entry_move(self, move):
        if move.picking_type_id.code == 'incoming' and not move.inventory_id and not move.picking_id.return_picking:
            return False
        return super(StockQuant,self)._account_entry_move(move)

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        if  move.picking_type_id:
            if move.picking_type_id.credit_account_id:
                credit_account_id = move.picking_type_id.credit_account_id.id
            if move.picking_type_id.debit_account_id:
                debit_account_id = move.picking_type_id.debit_account_id.id
        return super(StockQuant,self)._create_account_move_line(move, credit_account_id, debit_account_id, journal_id)


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    project_id = fields.Many2one('project.project',string="Project",copy=False)
    # sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order",copy=False)
    sub_work_order_id = fields.Char(string="Sub Work Order",copy=False)

    @api.model
    def default_get(self, fields):
        rec = super(account_move_line, self).default_get(fields)
        if 'line_ids' not in self._context:
            return rec
        #compute the default name of the next line in case of a manual entry
        label_name = ''
        for line in self.move_id.resolve_2many_commands(
                'line_ids', self._context['line_ids'], fields=['name']):
            label_name = line.get('name')
        if label_name:
            rec.update({'name': label_name})
        return rec


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    project_id = fields.Many2one('project.project',string="Project",copy=False)
    # sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order",copy=False)
    sub_work_order_id = fields.Char(string="Sub Work Order",copy=False)


class StockMove(models.Model):
    _inherit = "stock.move"

    project_id = fields.Many2one('project.project',string="Project",copy=False,
        related="picking_id.project_id",store=True)
    sub_work_order_id = fields.Many2one('construction.sub.work.order',string="Sub Work Order",copy=False,
        related="picking_id.sub_work_order_id",store=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        domain = super(StockMove,self).onchange_product_id()
        if self.product_id and self._context.get('default_picking_type_id'):
            picking_type_id = self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id'))
            if picking_type_id and picking_type_id.code =='outgoing':
                self.product_uom_qty = abs(self.product_id.qty_available)
        return domain

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.product_id and self._context.get('default_picking_type_id'):
            picking_type_id = self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id'))
            if picking_type_id and picking_type_id.code =='outgoing' and self.product_id.type == 'product':
                qty = self.product_uom_qty
                product_context = dict(self._context, location=self.location_id.id)
                product_quantity = self.product_id.with_context(product_context)._product_available()
                product_quantity = product_quantity[self.product_id.id]['qty_available']
                if product_quantity < qty:
                    msg = 'Please verify the product %s quantity which is more than available Quanity.' % (self.product_id.display_name)
                    raise ValidationError(_(msg))

    @api.constrains('product_uom_qty')
    def check_delivery_qty_on_hand(self):
        for move in self:
            if move.picking_id.picking_type_id.code == 'outgoing' and move.product_id.type == 'product':
                qty = move.product_uom_qty
                product_context = dict(self._context, location=move.location_id.id)
                product_quantity = move.product_id.with_context(product_context)._product_available()
                product_quantity = product_quantity[move.product_id.id]['qty_available']
                if product_quantity < qty:
                    msg = 'Please verify the product %s quantity which is more than available Quanity.' % (move.product_id.display_name)
                    raise ValidationError(_(msg))

    @api.multi
    def action_done(self):
        res = super(StockMove,self).action_done()
        for picking_id in self.mapped('picking_id'):
            if picking_id and picking_id.picking_type_code == 'incoming' and picking_id.purchase_id:
                picking_id.generate_vendor_bill()
        return res

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            if self.product_id.cost_method == 'average':
                valuation_amount = cost if self.location_id.usage in ['supplier', 'production'] and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
            else:
                valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount * qty)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            if self.product_id.cost_method == 'standard':
                raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
            return []
        credit_value = debit_value

        if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
            # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
            # account books the real purchase price, while the stock account books the average price. The difference is
            # booked in the dedicated price difference account.
            if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
            # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
            # is made using the original average price to negate the delivery effect.
            if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
                credit_value = debit_value
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
            'sub_work_order_id':self.picking_id.sub_work_order_id.name if self.picking_id and self.picking_id.sub_work_order_id else False,
            'project_id':self.picking_id.project_id.id if self.picking_id and self.picking_id.project_id else False,
            
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
            'sub_work_order_id':self.picking_id.sub_work_order_id.name if self.picking_id and self.picking_id.sub_work_order_id else False,
            'project_id':self.picking_id.project_id.id if self.picking_id and self.picking_id.project_id else False,
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': self.picking_id.name,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
                'sub_work_order_id':self.picking_id.sub_work_order_id.name if self.picking_id and self.picking_id.sub_work_order_id else False,
                'project_id':self.picking_id.project_id.id if self.picking_id and self.picking_id.project_id else False,
            }
            res.append((0, 0, price_diff_line))
        return res


class PackOperation(models.Model):
    _inherit='stock.pack.operation'

    @api.onchange('qty_done')
    def onchange_qty_done(self):
        if self.product_id and self.picking_id:
            picking_type_id = self.picking_id.picking_type_id
            if picking_type_id and picking_type_id.code =='incoming':
                if self.qty_done > self.product_qty:
                    msg = "You can't placed more than ordered quanity for %s." % (self.product_id.display_name)
                    raise ValidationError(_(msg))

    @api.constrains('qty_done')
    def check_received_qty_done(self):
        for op in self:
            if op.picking_id.picking_type_id.code == 'incoming' and op.product_id:
                if op.qty_done > op.product_qty:
                    msg = "You can't placed more than ordered quanity for %s." % (op.product_id.display_name)
                    raise ValidationError(_(msg))


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])
        new_picking, picking_type_id = super(ReturnPicking,self)._create_returns()
        if new_picking:
            new_picking_id = self.env['stock.picking'].browse(new_picking)
            new_picking_id.return_picking = True
            if picking and picking.project_id:
                new_picking_id.project_id = picking.project_id.id
        return new_picking, picking_type_id


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        res = super(ProductProduct,self)._convert_prepared_anglosaxon_line(line,partner)
        # invoice_id = self.env['account.invoice'].browse(line.get('invoice_id))
        if line.get('project_id'):
            res['project_id'] = line.get('project_id')
        if line.get('sub_work_order_id'):
            res['sub_work_order_id'] = line.get('sub_work_order_id')
        return res


class res_partner(models.Model):
    _inherit = "res.partner"

    vendor_type = fields.Selection([('Services','Services'),('Goods','Goods'),
        ('Third Party Construction','Third Party Construction'),
        ('House Sold','House Sold')],string="Vendor Type")
    fax = fields.Char(string="CNIC")


class picking_multi_product_selection(models.TransientModel):
    _name = 'picking.multi.product.selection'

    product_ids = fields.Many2many('product.product',string="Products")
    picking_id = fields.Many2one('stock.picking',string="Picking")

    @api.multi
    def do_confirm(self):
        if not self.picking_id:
            return
        lst = []
        for product in self.product_ids:
            ref = product.default_code
            name = '[' + ref + ']' + ' ' + product.name if ref else product.name
            vals = {
                'picking_id': self.picking_id.id,'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.picking_id.location_dest_id.id,'product_id': product.id,
                'product_uom': product.uom_id.id,'product_uom_qty': abs(product.qty_available),
                'name': name,'state': 'draft','group_id': self.picking_id.group_id.id
                }
            lst.append((0,0,vals))
        if lst:
            self.picking_id.write({'move_lines':lst})
