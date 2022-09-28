# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools import frozendict


class po_approve_demand(models.Model):
    _name = "po.approve.demand"
    _description="Purchase Approved Demand"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="Name",copy=False)
    origin = fields.Char(string="Description")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",default='draft',track_visibility='onchange')
    po_approve_demand_lines = fields.One2many('po.approve.demand.line', 'po_approve_demand_id', string='Demand Lines')
    po_approve_demand_lines_new = fields.One2many('po.approve.demand.line', 'po_approve_demand_new_id', string='Demand Lines')
    comment = fields.Text(string="Comment")
    approval_date =  fields.Date(string="Approval Date")
    format_type = fields.Selection([('0','With L/W'),('1','Without L/W')],string="Format",default='0',track_visibility='onchange')
    readonly_field_by_user = fields.Boolean(string="Readonly By User",copy=False,compute='readonly_field_for_user')
    purchase_order_ids = fields.Many2many('purchase.order',string="Purchase Orders",copy=False)
    demand_approved = fields.Boolean(string="Demand Approved")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',string="Currency",store=True)

    @api.multi
    def readonly_field_for_user(self):
        readonly_field_by_user = False
        for order in self:
            if order.state != 'draft':
                if self.user_has_groups('eq_construction_mgt.group_po_demand_user'):
                    readonly_field_by_user = True
                if self.user_has_groups('eq_construction_mgt.group_po_demand_manager'):
                    readonly_field_by_user = False
            if order.state == 'finished':
                readonly_field_by_user = True
            order.readonly_field_by_user = readonly_field_by_user

    # @api.multi
    # def unlink(self):
    #     if any(self.filtered(lambda l: l.state in ('confirm','approved','finish'))):
    #         raise Warning(_('You can only delete records which are in draft stage.'))
    #     return super(po_approve_demand, self).unlink()

    @api.multi
    def do_confirm(self):
        if self.format_type == '0' and not self.po_approve_demand_lines:
            raise Warning(_('Please enter demand lines.'))
        if self.format_type == '1' and not self.po_approve_demand_lines_new:
            raise Warning(_('Please enter demand lines.'))

        self.state ='confirm'

    @api.multi
    def do_approval(self):
        if self.format_type == '0' and not self.po_approve_demand_lines:
            raise Warning(_('Please enter demand lines.'))
        if self.format_type == '1' and not self.po_approve_demand_lines_new:
            raise Warning(_('Please enter demand lines.'))

        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('po.approve.demand')

        self.write({'state':'approved','approval_date':fields.Date.today(),'demand_approved':True})

    @api.multi
    def do_finished(self):
        if self.format_type == '0' and not self.po_approve_demand_lines:
            raise Warning(_('Please enter demand lines.'))
        if self.format_type == '1' and not self.po_approve_demand_lines_new:
            raise Warning(_('Please enter demand lines.'))
        self.state = 'finished'


    @api.multi
    def open_generate_po_wizard(self):
        if self.format_type == '0' and not self.po_approve_demand_lines:
            raise Warning(_('Please enter demand lines.'))
        if self.format_type == '1' and not self.po_approve_demand_lines_new:
            raise Warning(_('Please enter demand lines.'))

        lst = []
        if self.format_type == '0':
            for line in self.po_approve_demand_lines:
                lst.append((0,0,{'product_id':line.product_id.id,'uom_id':line.uom_id.id,'qty':line.qty,
                    'total_unit':line.total_unit,'expected_rate':line.expected_rate,'total_amount':line.total_amount
                    }))

        if self.format_type == '1':
            for line in self.po_approve_demand_lines_new:
                lst.append((0,0,{'product_id':line.product_id.id,'uom_id':line.uom_id.id,'qty':line.qty,
                    'total_unit':line.total_unit,'expected_rate':line.expected_rate,'total_amount':line.total_amount
                    }))

        return{
            'name':'Approved Demand',
            'type':'ir.actions.act_window',
            'res_model':'wizard.po.approve.demand',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'context':{'default_po_approve_demand_id':self.id,'default_po_approve_demand_lines':lst}
        }

    @api.multi
    def open_multi_products_wiz(self):
        return{
            'name':'Multi Products',
            'type':'ir.actions.act_window',
            'res_model':'po.demand.multi.product.selection',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'context':{'default_po_approve_demand_id':self.id}
        }


class po_approve_demand_line(models.Model):
    _name = "po.approve.demand.line"
    _description="Purchase Approved Demand Lines"

    product_id = fields.Many2one('product.product',string="Product")
    uom_id = fields.Many2one('product.uom',string="UOM",related="product_id.uom_id",store=True)
    qty = fields.Float(string="Qty",default="1")
    length = fields.Float(string="L")
    width = fields.Float(string="W")
    unit = fields.Float(string="Unit",store=True,compute='cal_unit')
    unit_new = fields.Float(string="Unit")
    total_unit = fields.Float(string="Total Unit",compute='cal_total_unit',store=True)
    po_approve_demand_id = fields.Many2one('po.approve.demand',string="Approve Demand")
    po_approve_demand_new_id = fields.Many2one('po.approve.demand',string="Approve Demand")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",related='po_approve_demand_id.state',store=True)
    format_type = fields.Selection([('0','With L/W'),('1','Without L/W')],string="Format",related='po_approve_demand_id.format_type',store=True)
    state_new = fields.Selection([('draft','Draft'),('confirm','Confirm'),('approved','Approved'),('finished','Finished')],string="Status",related='po_approve_demand_new_id.state',store=True)
    format_type_new = fields.Selection([('0','With L/W'),('1','Without L/W')],string="Format",related='po_approve_demand_new_id.format_type',store=True)
    expected_rate = fields.Monetary(string="Expected Rate")
    total_amount = fields.Monetary(string="Total Amount",compute='cal_total_amount',store=True)
    company_id = fields.Many2one('res.company',string="Company",related='po_approve_demand_id.company_id',store=True)
    currency_id = fields.Many2one('res.currency',related='po_approve_demand_id.currency_id',string="Currency",store=True)

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if not self.product_id:
    #         return
    #     self.uom_id = self.product_id.uom_id.id

    @api.depends('length','width','format_type_new','unit_new')
    def cal_unit(self):
        for each in self:
            if each.unit_new:
                each.unit = each.unit_new
            else:
                each.unit = (each.length * each.width)

    @api.depends('unit','qty','unit_new')
    def cal_total_unit(self):
        for each in self:
            each.total_unit = (each.unit * each.qty)

    @api.depends('qty','expected_rate','total_unit')
    def cal_total_amount(self):
        for each in self:
            if each.format_type:
                each.total_amount = (each.total_unit * each.expected_rate)
            if each.format_type_new:
                each.total_amount = (each.qty * each.expected_rate)


class wizard_po_approve_demand(models.TransientModel):
    _name = "wizard.po.approve.demand"
    _description="Wizard Purchase Approved Demand"

    vendor_id = fields.Many2one('res.partner',string="Vendor")
    select_type = fields.Selection([('0','Check All'),('1','Uncheck All')],string="Type")
    po_approve_demand_id = fields.Many2one('po.approve.demand',string="Approve Demand")
    po_approve_demand_lines = fields.One2many('wizard.po.approve.demand.line', 'wizard_po_approve_demand_id', string='Demand Lines')

    @api.onchange('select_type')
    def onchange_select_type_field(self):
        select = True if self.select_type == '0' else False
        for each in self.po_approve_demand_lines:
            each.select = select

    @api.multi
    def generate_po(self):
        lst = []
        if all(not line.select for line in self.po_approve_demand_lines):
            raise Warning(_("Please select atleast one line."))

        order_line = []
        for line in self.po_approve_demand_lines.filtered(lambda l:l.select):
            order_line.append((0,0,{
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'product_uom': line.uom_id.id,
                    'price_unit': line.expected_rate,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }))

        vals = {'partner_id':self.vendor_id.id,'order_line':order_line,'origin':self.po_approve_demand_id.name}
        purchase_order_id = self.env['purchase.order'].create(vals)
        if purchase_order_id:
            purchase_order_id.onchange_partner_id()
            purchase_order_id._onchange_picking_type_id()
            self.po_approve_demand_id.write({'purchase_order_ids':[(4,purchase_order_id.id)]})
        return


class wizard_po_approve_demand_line(models.TransientModel):
    _name = "wizard.po.approve.demand.line"
    _description="Wizard Purchase Approved Demand Line"

    product_id = fields.Many2one('product.product',string="Product")
    uom_id = fields.Many2one('product.uom',string="UOM")
    qty = fields.Float(string="Qty")
    total_unit = fields.Float(string="Total Unit")
    wizard_po_approve_demand_id = fields.Many2one('wizard.po.approve.demand',string="Approve Demand")
    expected_rate = fields.Float(string="Expected Rate")
    total_amount = fields.Float(string="Total Amount")
    select = fields.Boolean(string="Select")


class po_demand_multi_product_selection(models.TransientModel):
    _name = 'po.demand.multi.product.selection'

    product_ids = fields.Many2many('product.product',string="Products")
    po_approve_demand_id = fields.Many2one('po.approve.demand',string="PO Demand")

    @api.multi
    def do_confirm(self):
        if not self.po_approve_demand_id:
            return
        lst = []
        for product in self.product_ids:
            vals = {'product_id': product.id,'uom_id': product.uom_id.id,'qty':1}
            lst.append((0,0,vals))
        if lst:
            if self.po_approve_demand_id.format_type == '0':
                self.po_approve_demand_id.write({'po_approve_demand_lines':lst})
            else:
                self.po_approve_demand_id.write({'po_approve_demand_lines_new':lst})


class purchase_order(models.Model):
    _inherit='purchase.order'

    date_planned = fields.Datetime(string='Scheduled Date', compute='_compute_date_planned', store=True, index=True)
    state = fields.Selection([
        ('draft', 'PO'),
        ('sent', 'PO send'),
        ('to approve', 'To Approve'),
        ('purchase', 'Confirm'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    partner_ref = fields.Char('General Description', copy=False,\
        help="Reference of the sales order or bid sent by the vendor. "
             "It's used to do the matching when you receive the "
             "products as this reference is usually written on the "
             "delivery order sent by your vendor.")

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            for line in order.order_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date
            else:
                order.date_planned = fields.Date.today()

    @api.multi
    def open_multi_products_wiz(self):
        return{
            'name':'Multi Products',
            'type':'ir.actions.act_window',
            'res_model':'po.draft.multi.product.selection',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'context':{'default_draft_po_id':self.id}
        }

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """In the case that taxes rounding is set to globally, Odoo requires
        again the line price unit, and currently ORM mixes values, so the only
        way to get a proper value is to overwrite that part, losing
        inheritability.
        """
        orders2recalculate = self.filtered(lambda x: (
            x.company_id.tax_calculation_rounding_method ==
            'round_globally' and any(x.mapped('order_line.discount'))
        ))
        super(purchase_order, self)._amount_all()
        for order in orders2recalculate:
            amount_tax = 0
            for line in order.order_line:
                taxes = line.taxes_id.compute_all(
                    line._get_discounted_price_unit(),
                    line.order_id.currency_id,
                    line.product_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_id,
                )
                amount_tax += sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])
                )
            order.update({
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': order.amount_untaxed + amount_tax,
            })


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends('discount')
    def _compute_amount(self):
        """ Inject the product price with proper rounding in the context from
        which account.tax::compute_all() is able to retrieve it. The alternate
        context is patched onto self because it can be a NewId passed in the
        onchange the env of which does not support `with_context`. """
        for line in self:
            orig_context = None
            # This is always executed for allowing other modules to use this
            # with different conditions than discount != 0
            discounted_price_unit = line._get_discounted_price_unit()
            if discounted_price_unit != line.price_unit:
                precision = line.order_id.currency_id.decimal_places
                company = line.company_id or self.env.user.company_id
                if company.tax_calculation_rounding_method == 'round_globally':
                    precision += 5
                orig_context = self.env.context
                price = round(
                    line.product_qty * discounted_price_unit, precision)
                self.env.context = frozendict(
                    self.env.context, base_values=(price, price, price))
            super(PurchaseOrderLine, line)._compute_amount()
            if orig_context is not None:
                self.env.context = orig_context

    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),
    )
    copy_product_uom = fields.Many2one('product.uom', string='Product Unit of Measure', related="product_id.uom_po_id",store=True)

    _sql_constraints = [
        ('discount_limit', 'CHECK (discount <= 100.0)',
         'Discount must be lower than 100%.'),
    ]

    def _get_discounted_price_unit(self):
        """Inheritable method for getting the unit price after applying
        discount(s).

        :rtype: float
        :return: Unit price after discount(s).
        """
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    @api.multi
    def _get_stock_move_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.
        """
        price_unit = False
        price = self._get_discounted_price_unit()
        if price != self.price_unit:
            # Only change value if it's different
            price_unit = self.price_unit
            self.price_unit = price
        price = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        if price_unit:
            self.price_unit = price_unit
        return price


class po_draft_multi_product_selection(models.TransientModel):
    _name = 'po.draft.multi.product.selection'

    product_ids = fields.Many2many('product.product',string="Products")
    draft_po_id = fields.Many2one('purchase.order',string="Draft PO")

    @api.multi
    def do_confirm(self):
        if not self.draft_po_id:
            return
        lst = []
        for product in self.product_ids:
            ref = product.default_code
            name = '[' + ref + ']' + ' ' + product.name if ref else product.name
            vals = {'product_id': product.id,'product_uom': product.uom_po_id.id,
                'product_qty':1,'price_unit':0.00,'name':name,'date_planned':datetime.now()}
            lst.append((0,0,vals))
        if lst:
            self.draft_po_id.write({'order_line':lst})