from odoo import models, fields, api

import time
from dateutil import relativedelta
import dateutil.relativedelta
import datetime
from datetime import date
from datetime import datetime , timedelta
#from odoo.addons.web.controllers
# def clean_action(action):
#     action.setdefault('flags', {})
#     action_type = action.setdefault('type', 'ir.actions.act_window_close')
#     if action_type == 'ir.actions.act_window':
#         return fix_view_modes(action)
#     return action


class StockReport(models.TransientModel):
    _name = "wizard.stock.history"
    _description = "Current Stock History"

    warehouse = fields.Many2one('stock.warehouse', string='Warehouse')
    product_categ = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz', string='Warehouse')
#     location = fields.Many2many('stock.location',default=lambda self: self.env['stock.location'].search([('usage','not in',['view','internal'])]))
    location = fields.Many2many('stock.location')
    product =fields.Many2many('product.product', string='Product')
    check = fields.Boolean(default=False,help='This will bring cost of Products only')
#     me
    date_from = fields.Date('Date From:',default=time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To:',default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],)
    
#     @api.multi
#     @api.depends('category')
#     def pr(self):
#         
#         pass
    
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'product.product'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    #'type': 'set_scrollTop',
                    #'type':'ir.actions.act_multi',
                    'report_name': 'export_stockinfo_xls.stock_report_xls.xlsx',
                    'datas': datas,
                    'name': 'Current Stock',
                   
                    }
            #return self.env['report'].get_action(self, 'export_stockinfo_xls.stock_report_xls.xlsx',datas)
              # return self.env['report'].get_action([],'export_stockinfo_xls.stock_report_xls.xlsx',datas)
