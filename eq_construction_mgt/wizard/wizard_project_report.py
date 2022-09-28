# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import datetime
from collections import OrderedDict
from odoo import fields, models, api,tools, _
from odoo.exceptions import Warning,ValidationError,UserError


class wizard_project_report(models.TransientModel):
    _name = "wizard.project.report"

    start_date = fields.Date(string="Start Date",default=fields.Date.context_today)
    end_date = fields.Date(string="End Date",default=fields.Date.context_today)
    sorted_by = fields.Selection([('Product','Product'),('Date','Date'),('Work Order','Work Order')],
        string="Sorted By",default='Product')
    project_id = fields.Many2one('project.project',string="Project")

    @api.multi
    def do_confirm(self):
        if self.end_date < self.start_date:
            raise Warning (_('Please enter proper date range.'))
        data = self.read()[0]
        return self.env['report'].get_action(self, 'eq_construction_mgt.print_project_report_template', data=data)


class eq_construction_mgt_print_project_report_template(models.AbstractModel):
    _name = 'report.eq_construction_mgt.print_project_report_template'

    @api.model
    def render_html(self, docids, data=None):
        wizard_id = self.env['wizard.project.report'].browse(data.get('id'))
        get_report_list = {}
        get_report_list_without_sub_wo = {}

        ret_get_report_list = {}
        ret_get_report_list_without_sub_wo = {}

        if wizard_id.sorted_by =='Product':
            picking_ids = self.env['stock.picking'].search([('project_id','=',wizard_id.project_id.id),('state','=','done'),
                ('min_date','>=',wizard_id.start_date),('min_date','<=',wizard_id.end_date)])

            stock_move_ids = picking_ids.mapped('move_lines')
            product_ids = stock_move_ids.mapped('product_id')

            for move in stock_move_ids:
                get_report_list.setdefault(move.product_id,[])
                qty_in = move.product_qty if move.picking_id.picking_type_code =='outgoing' else 0.00
                qty_out = move.product_qty if move.picking_id.picking_type_code =='incoming' else 0.00
                rate = (move.product_qty * move.price_unit)
                amount_in = (rate * qty_in)
                amount_out = (rate * qty_out)
                date = datetime.datetime.strptime(move.date,'%Y-%m-%d %H:%M:%S').date()

                vals = {'date':date,'qty_in':qty_in,'qty_out':qty_out,'rate':rate,'amount_in':amount_in,'amount_out':amount_out}
                get_report_list[move.product_id].append(vals)

        if wizard_id.sorted_by =='Date':
            picking_ids = self.env['stock.picking'].search([('project_id','=',wizard_id.project_id.id),('state','=','done'),
                ('min_date','>=',wizard_id.start_date),('min_date','<=',wizard_id.end_date)])

            stock_move_ids = picking_ids.mapped('move_lines')
            product_ids = stock_move_ids.mapped('product_id')

            for move in stock_move_ids.sorted(key=lambda l:l.date):
                date = datetime.datetime.strptime(move.date,'%Y-%m-%d %H:%M:%S').date()
                date = date.strftime('%Y-%m-%d')
                get_report_list.setdefault(date,[])
                qty_in = move.product_qty if move.picking_id.picking_type_code =='outgoing' else 0.00
                qty_out = move.product_qty if move.picking_id.picking_type_code =='incoming' else 0.00
                rate = (move.product_qty * move.price_unit)
                amount_in = (rate * qty_in)
                amount_out = (rate * qty_out)

                vals = {'product_id':move.product_id.display_name,'qty_in':qty_in,'qty_out':qty_out,'rate':rate,'amount_in':amount_in,'amount_out':amount_out}
                get_report_list[date].append(vals)

            get_report_list = sorted(get_report_list.items(),key=lambda key: key)

        if wizard_id.sorted_by =='Work Order':
            picking_ids = self.env['stock.picking'].search([('project_id','=',wizard_id.project_id.id),('state','=','done'),
                ('picking_type_code','=','outgoing')])

            sub_wk_picking_ids = picking_ids.filtered(lambda l:l.sub_work_order_id and l.project_id)
            without_sub_wk_picking_ids = picking_ids.filtered(lambda l:not l.sub_work_order_id and l.project_id)

            sub_stock_move_ids = sub_wk_picking_ids.mapped('move_lines')
            without_sub_stock_move_ids = without_sub_wk_picking_ids.mapped('move_lines')
            sub_stock_move_ids = sub_stock_move_ids.sorted(key=lambda r: r.sub_work_order_id.name)
            without_sub_stock_move_ids = without_sub_stock_move_ids.sorted(key=lambda r: r.sub_work_order_id.name)

            for move in sub_stock_move_ids:
                sub_work_order_id = move.sub_work_order_id
                get_report_list.setdefault(sub_work_order_id.name,{})
                qty_out = move.product_qty if move.picking_id.picking_type_code =='outgoing' else - move.product_qty
                rate = (move.product_qty * move.price_unit)
                amount_total = (rate * qty_out)
                vals = {'work_order':sub_work_order_id.work_order_id.name,'project':sub_work_order_id.project_id.name,
                    'swo_no':sub_work_order_id.name,'swo_name':sub_work_order_id.activity_id.name,
                    'product':move.product_id.name,'qty':0.00,'total_amount':0.00
                }
                get_report_list[sub_work_order_id.name].setdefault(move.product_id,vals)
                get_report_list[sub_work_order_id.name][move.product_id]['qty'] += qty_out
                get_report_list[sub_work_order_id.name][move.product_id]['total_amount'] += amount_total

            for move in without_sub_stock_move_ids:
                sub_work_order_id = move.sub_work_order_id
                qty_out = move.product_qty if move.picking_id.picking_type_code =='outgoing' else - move.product_qty
                rate = (move.product_qty * move.price_unit)
                amount_total = (rate * qty_out)
                vals = {'work_order':'','project':move.project_id.name,
                    'swo_no':'','swo_name':'','product':move.product_id.name,'qty':0.00,'total_amount':0.00
                }
                get_report_list_without_sub_wo.setdefault(move.product_id,vals)
                get_report_list_without_sub_wo[move.product_id]['qty'] += qty_out
                get_report_list_without_sub_wo[move.product_id]['total_amount'] += amount_total

            # Return
            picking_ids = self.env['stock.picking'].search([('project_id','=',wizard_id.project_id.id),('state','=','done'),
                ('picking_type_code','=','incoming')])

            sub_wk_picking_ids = picking_ids.filtered(lambda l:l.sub_work_order_id and l.project_id)
            without_sub_wk_picking_ids = picking_ids.filtered(lambda l:not l.sub_work_order_id and l.project_id)

            sub_stock_move_ids = sub_wk_picking_ids.mapped('move_lines')
            without_sub_stock_move_ids = without_sub_wk_picking_ids.mapped('move_lines')
            sub_stock_move_ids = sub_stock_move_ids.sorted(key=lambda r: r.sub_work_order_id.name)
            without_sub_stock_move_ids = without_sub_stock_move_ids.sorted(key=lambda r: r.sub_work_order_id.name)

            for move in sub_stock_move_ids:
                sub_work_order_id = move.sub_work_order_id
                ret_get_report_list.setdefault(sub_work_order_id.name,{})
                qty_out = -move.product_qty
                rate = (move.product_qty * move.price_unit)
                amount_total = (rate * qty_out)
                vals = {'work_order':sub_work_order_id.work_order_id.name,'project':sub_work_order_id.project_id.name,
                    'swo_no':sub_work_order_id.name,'swo_name':sub_work_order_id.activity_id.name,
                    'product':move.product_id.name,'qty':0.00,'total_amount':0.00
                }
                ret_get_report_list[sub_work_order_id.name].setdefault(move.product_id,vals)
                ret_get_report_list[sub_work_order_id.name][move.product_id]['qty'] += qty_out
                ret_get_report_list[sub_work_order_id.name][move.product_id]['total_amount'] += amount_total

            for move in without_sub_stock_move_ids:
                sub_work_order_id = move.sub_work_order_id
                qty_out = - move.product_qty
                rate = (move.product_qty * move.price_unit)
                amount_total = (rate * qty_out)
                vals = {'work_order':'','project':move.project_id.name,
                    'swo_no':'','swo_name':'','product':move.product_id.name,'qty':0.00,'total_amount':0.00
                }
                ret_get_report_list_without_sub_wo.setdefault(move.product_id,vals)
                ret_get_report_list_without_sub_wo[move.product_id]['qty'] += qty_out
                ret_get_report_list_without_sub_wo[move.product_id]['total_amount'] += amount_total

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'wizard.project.report',
            'docs': wizard_id,
            'data': data,
            'get_report_list': get_report_list,
            'get_report_list_without_sub_wo':get_report_list_without_sub_wo,
            'ret_get_report_list': ret_get_report_list,
            'ret_get_report_list_without_sub_wo':ret_get_report_list_without_sub_wo,

        }
        return self.env['report'].render('eq_construction_mgt.print_project_report_template', docargs)


        
