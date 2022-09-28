from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import fields, models,api
from collections import OrderedDict
import datetime
from datetime import date, datetime
#from bs4 import BeautifulSoup

class StockReportXls(ReportXlsx):
    @api.multi
    def get_lines(self, date_from, date_to, product_categ, product, cat, warehouse,locations,check):
         
        lines = []
        imf=[]
        if product:
            product_ids = self.env['product.product'].search([('categ_id','=',cat.id),('id','in',product)])
        else:
            product_ids = self.env['product.product'].search([('categ_id','=',cat.id)])
        
        array = []
        for lo in locations:
            array.append(lo.id)
        for product in product_ids:
            cost = product.standard_price
            sale_price = product.list_price
#             product_source =  self.env['stock.move'].search([('date', '>=',date_from),('date', '<=',date_to),('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
#             product_dest =  self.env['stock.move'].search([('date', '>=',date_from),('date', '<=',date_to),('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])
            product_source =  self.env['stock.move'].search([('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
            product_dest =  self.env['stock.move'].search([('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])
            
            #product_dest[10].quant_ids.filtered(lambda x: (x.in_date).split(' ')[0] == '2019-07-01')
            production = 0.0
            itp = 0.0
            sale = 0.0
            inventory_loss = 0.0
            inventory_loss1 = 0.0
            transfer = 0.0
            purchase =0.0 
            transfer_two = 0.0
            purchase_return = 0.0
            sale_return = 0.0
            array_location = []
            
            
            
            if (check == False):
            
                for prod in product_source:
                    #pr_srdate=prod.quant_ids.filtered(lambda x, dt_from=date_from , dt_to= date_to: (x.in_date).split(' ')[0] >= dt_from   and (x.in_date).split(' ')[0] <= dt_to)
                    
                    
                    for qa in prod.quant_ids:
                        if qa.in_date.split(' ')[0]  >=  date_from and  qa.in_date.split(' ')[0]  <=  date_to:
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                                itp += qa.qty
                        #pr_date=prod.quant_ids.filtered(lambda x, dt_from=date_from , dt_to= date_to: (x.in_date).split(' ')[0] >= dt_from   and (x.in_date).split(' ')[0] <= dt_to)
                        
#                         for rec in pr_srdate:
#                             itp += rec.qty
                            
                        
                        
                        
                        #itp += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
#                                 for rec in pr_srdate:
                                    sale += qa.qty
                                    
                                #sale += prod.product_uom_qty
            #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
#                                 for rec in pr_srdate:
                                    inventory_loss += qa.qty
                                
                                
                                #inventory_loss += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
#                                 for rec in pr_srdate:
                                    transfer += qa.qty
                                
                                #transfer = transfer+prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
#                                 for rec in pr_srdate:
                                    purchase_return += qa.qty
                        #purchase_return += prod.product_uom_qty
                for dest in product_dest:
                    #pr_destdate=dest.quant_ids.filtered(lambda x, dt_from=date_from , dt_to= date_to: (x.in_date).split(' ')[0] >= dt_from   and (x.in_date).split(' ')[0] <= dt_to)
                    for qa in dest.quant_ids:
                        if qa.in_date.split(' ')[0]  >=  date_from and  qa.in_date.split(' ')[0]  <=  date_to:
                    
                    
                    
                            
                            if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate:
                                    purchase += qa.qty
                                    continue
                                #purchase += dest.product_uom_qty
                            if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate:
                                    production += qa.qty
                                #production += dest.product_uom_qty 
                            if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate:
                                    transfer_two += qa.qty
                                #transfer_two += dest.product_uom_qty
                            if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate:
                                    sale_return += qa.qty
                                
                                #sale_return += dest.product_uom_qty
                            if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                                
                                #for rec in pr_destdate:
                                    inventory_loss1 += qa.qty
                        #inventory_loss1 += dest.product_uom_qty
            
            else:
                if(check == True):
                    for prod in product_source:
                        if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                            
                            for inpr in prod.quant_ids:
                                if inpr.in_date.split(' ')[0]  >=  date_from and  inpr.in_date.split(' ')[0]  <=  date_to:
                                    itp += inpr.inventory_value
                                
                        if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
                            
                            for ci in prod.quant_ids:
                                if ci.in_date.split(' ')[0]  >=  date_from and  ci.in_date.split(' ')[0]  <=  date_to:

                                
                                    sale += ci.inventory_value
        #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                        if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
                            
                            for invnt_in in prod.quant_ids:
                                if invnt_in.in_date.split(' ')[0]  >=  date_from and  invnt_in.in_date.split(' ')[0]  <=  date_to:

                                    inventory_loss += invnt_in.inventory_value
                                
                        if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
                            
                            for int_it in prod.quant_ids:
                                if int_it.in_date.split(' ')[0]  >=  date_from and  int_it.in_date.split(' ')[0]  <=  date_to:

                                
                                    transfer = transfer + int_it.inventory_value
                                 
                        if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
                            
                            for isup in prod.quant_ids:
                                if isup.in_date.split(' ')[0]  >=  date_from and  isup.in_date.split(' ')[0]  <=  date_to:

                                    purchase_return += isup.inventory_value
                            
                    for dest in product_dest:
                        if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                            
                            for supl in dest.quant_ids:
                                if supl.in_date.split(' ')[0]  >=  date_from and  supl.in_date.split(' ')[0]  <=  date_to:

                                    purchase += supl.inventory_value
                            
                        if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                            
                            for pr in dest.quant_ids:
                                if pr.in_date.split(' ')[0]  >=  date_from and  pr.in_date.split(' ')[0]  <=  date_to:

                                
                                    production += pr.inventory_value
                             
                        if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                            
                            for int_trns in dest.quant_ids:
                                if int_trns.in_date.split(' ')[0]  >=  date_from and  int_trns.in_date.split(' ')[0]  <=  date_to:

                                    transfer_two += int_trns.inventory_value
                                
                        if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                            
                            for cst in dest.quant_ids:
                                if cst.in_date.split(' ')[0]  >=  date_from and  cst.in_date.split(' ')[0]  <=  date_to:

                                    sale_return += cst.inventory_value
                                
                        if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                            
                            for invnt in dest.quant_ids:
                                if invnt.in_date.split(' ')[0]  >=  date_from and  invnt.in_date.split(' ')[0]  <=  date_to:

                                    inventory_loss1 += invnt.inventory_value
            
                    
                        
            #for opening bal
#             product_source1 =  self.env['stock.move'].search([('date', '<',date_from),('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
#             product_dest1 =  self.env['stock.move'].search([('date', '<',date_from),('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])
#             
            product_source1 =  self.env['stock.move'].search([('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
            product_dest1 =  self.env['stock.move'].search([('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])

            
            
            ob_production = 0.0
            ob_itp = 0.0
            ob_sale = 0.0
            ob_inventory_loss = 0.0
            ob_inventory_loss1 = 0.0
            ob_transfer = 0.0
            ob_purchase =0.0 
            ob_transfer_two = 0.0
            opening_bal= 0.0
            ob_purchase_return = 0.0
            ob_sale_return = 0.0
            closing_bal= 0.0
            
            
            
            if(check == False):
                for prod in product_source1:
                    
                    pr_srcdate=prod.quant_ids.filtered(lambda x, dt_from=date_from : (x.in_date).split(' ')[0] < dt_from )
                    
                    for qa in prod.quant_ids:
                        if qa.in_date.split(' ')[0]  <  date_from:
                        
                    
                    
                    
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                                
                                #for rec in pr_srcdate:
                                    ob_itp += qa.qty
                                #ob_itp += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
                                
                                #for rec in pr_srcdate:
                                    ob_sale += qa.qty
                                
                                #ob_sale += prod.product_uom_qty
            #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
                                
                                #for rec in pr_srcdate:
                                    ob_inventory_loss += qa.qty
                                #ob_inventory_loss += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
                                     
                                    #for rec in pr_srcdate:
                                        ob_transfer += qa.qty 
                                    #ob_transfer += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
                                
                                #for rec in pr_srcdate:
                                    ob_purchase_return += qa.qty 
                        #ob_purchase_return += prod.product_uom_qty
                for dest in product_dest1:
                    
                    pr_destdate1=dest.quant_ids.filtered(lambda x, dt_from=date_from : (x.in_date).split(' ')[0] < dt_from )
                    
                    
                    
                    for qa in dest.quant_ids:
                        if qa.in_date.split(' ')[0]  <  date_from:
                        
                    
                    
                            if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate1:
                                    ob_purchase += qa.qty
                                #ob_purchase += dest.product_uom_qty
                            if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                                
                                #for rec in pr_destdate1:
                                    ob_production += qa.qty
                                #ob_production += dest.product_uom_qty 
                            if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                                #for rec in pr_destdate1:
                                    ob_transfer_two += qa.qty
                                #ob_transfer_two += dest.product_uom_qty
                            if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                                
                                #for rec in pr_destdate1:
                                    ob_sale_return += qa.qty
                                #ob_sale_return += dest.product_uom_qty
                            if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                                
                                #for rec in pr_destdate1:
                                    ob_inventory_loss1 += qa.qty

                        #ob_inventory_loss1 += dest.product_uom_qty
            
            elif(check == True):
                for prod in product_source1:
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                        
                        for prd in prod.quant_ids:
                            if prd.in_date.split(' ')[0]  <  date_from:
                            
                                ob_itp += prd.inventory_value
                        
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
                        
                        for icust in prod.quant_ids:
                            if icust.in_date.split(' ')[0]  <  date_from:
                                ob_sale += icust.inventory_value
    #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
                        
                        for invt in prod.quant_ids:
                            if invt.in_date.split(' ')[0]  <  date_from:
                                ob_inventory_loss += invt.inventory_value
                        
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
                        
                        for in_int in prod.quant_ids: 
                            if in_int.in_date.split(' ')[0]  <  date_from:  
                                ob_transfer += in_int.inventory_value
                            
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
                        
                        for insupl in prod.quant_ids:
                            if insupl.in_date.split(' ')[0]  <  date_from: 
                                ob_purchase_return += insupl.inventory_value
                        
                        
                for dest in product_dest1:
                    if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                        
                        for  supl_int in dest.quant_ids:
                            if supl_int.in_date.split(' ')[0]  <  date_from: 
                                ob_purchase += supl_int.inventory_value
                            
                    if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                        
                        for prd_int in dest.quant_ids:
                            if prd_int.in_date.split(' ')[0]  <  date_from:
                                ob_production += prd_int.inventory_value 
                            
                    if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                        
                        for i_int in dest.quant_ids:
                            if i_int.in_date.split(' ')[0]  <  date_from:
                                ob_transfer_two += i_int.inventory_value
                            
                    if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                        
                        for cust_in in dest.quant_ids:
                            if cust_in.in_date.split(' ')[0]  <  date_from:
                                ob_sale_return +=  cust_in.inventory_value
                            
                    if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                        
                        for invnt_intl in dest.quant_ids:
                            if invnt_intl.in_date.split(' ')[0]  <  date_from:
                                ob_inventory_loss1 += invnt_intl.inventory_value
                            
                
            opening_bal= ob_purchase - ob_sale + (ob_inventory_loss1 - ob_inventory_loss) + ob_sale_return - ob_purchase_return + ob_production - ob_itp
            #closing_bal = opening_bal + purchase + production + transfer + inventory_loss1 - inventory_loss - itp - sale
            closing_bal = opening_bal + purchase + production - transfer + inventory_loss1 - inventory_loss - itp - sale + transfer_two
            #or
            #correct value for closing balance
            #closing_bal= opening_bal + purchase + production - transfer + inventory_loss1 - inventory_loss - itp - sale + transfer_two + sale_return
            #closing_bal = opening_bal + purchase + production +(transfer_two - transfer)  + (inventory_loss1 - inventory_loss) - itp - sale 
#                 if 'MO' in prod.name:
            
            
            #direct closing bal
#             product_source1_cb =  self.env['stock.move'].search([('date', '<',date_to),('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
#             product_dest1_cb =  self.env['stock.move'].search([('date', '<',date_to),('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])
#              |
#             \_/
            product_source1_cb =  self.env['stock.move'].search([('product_id', '=',product.id),('location_id','in',array),('state','=','done')])
            product_dest1_cb =  self.env['stock.move'].search([('product_id', '=',product.id),('location_dest_id','in',array),('state','=','done')])
            
            
            production_cb = 0.0
            itp_cb = 0.0
            sale_cb = 0.0
            inventory_loss_cb = 0.0
            inventory_loss1_cb = 0.0
            transfer_cb = 0.0
            purchase_cb =0.0 
            transfer_two_cb = 0.0
            purchase_return_cb = 0.0
            sale_return_cb = 0.0
            closing_bal_cb=0.0
            
            
            if(check == False):
            
                for prod in product_source1_cb:
                    pr_srcdate_cb=prod.quant_ids.filtered(lambda x, dt_to=date_to : (x.in_date).split(' ')[0] < dt_to )
                    
                    
                    
                    for qa in prod.quant_ids:
                        if qa.in_date.split(' ')[0]  <=  date_to:
                    
                    
                     
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                                
                                #for rec in pr_srcdate_cb:
                                    itp_cb += qa.qty
                                #itp_cb += prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
                                
                                #for rec in pr_srcdate_cb:
                                    sale_cb += qa.qty
                                #sale_cb += prod.product_uom_qty
            #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
                                
                                #for rec in pr_srcdate_cb:
                                    inventory_loss_cb += qa.qty
                                #inventory_loss_cb += prod.product_uom_qty
                                
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
                                
                                #for rec in pr_srcdate_cb:
                                    transfer_cb += qa.qty
                                #transfer_cb = transfer_cb+prod.product_uom_qty
                            if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
                                
                                #for rec in pr_srcdate_cb:
                                    purchase_return_cb += qa.qty
                        #purchase_return_cb += prod.product_uom_qty
                for dest in product_dest1_cb:
                    
                    #pr_destdate_cb=dest.quant_ids.filtered(lambda x, dt_to=date_to : (x.in_date).split(' ')[0] < dt_to )
                    for qa in dest.quant_ids:
                        if qa.in_date.split(' ')[0]  <=  date_to:
                    
                    
                      
                    
                            if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                                
                                
                                #for rec in pr_destdate_cb:
                                    purchase_cb += qa.qty
                                    
                                #purchase_cb += dest.product_uom_qty
                            if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                                
                                #for rec in pr_destdate_cb:
                                    production_cb += qa.qty
                                #production_cb += dest.product_uom_qty 
                            if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                                
                                #for rec in pr_destdate_cb:
                                    transfer_two_cb += qa.qty
                                #transfer_two_cb += dest.product_uom_qty
                                
                            if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                                
                                #for rec in pr_destdate_cb:
                                    sale_return_cb += qa.qty
                                #sale_return_cb += dest.product_uom_qty
                            if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                                
                                #for rec in pr_destdate_cb:
                                    inventory_loss1_cb += qa.qty
                        #inventory_loss1_cb += dest.product_uom_qty
            
            elif(check == True):
                for prod in product_source1_cb:
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='production':
                        
                        for ip in prod.quant_ids:
                            if ip.in_date.split(' ')[0]  <=  date_to:
                                itp_cb += ip.inventory_value
                        
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='customer':
                        
                        for ict in prod.quant_ids:
                            if ict.in_date.split(' ')[0]  <=  date_to:
                                sale_cb += ict.inventory_value
    #                     or prod.location_dest_id.usage =='view' or prod.location_dest_id.usage =='procurement' or prod.location_dest_id.usage =='transit'
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='inventory':
                        
                        for intl_int in prod.quant_ids:
                            if intl_int.in_date.split(' ')[0]  <=  date_to:
                                inventory_loss_cb += intl_int.inventory_value
                            
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='internal':
                        
                        for inl_intl in prod.quant_ids:
                            if inl_intl.in_date.split(' ')[0]  <=  date_to:
                                transfer_cb = transfer_cb + inl_intl.inventory_value
                             
                    if prod.location_id.usage == 'internal' and prod.location_dest_id.usage =='supplier':
                        
                        for int_sp in prod.quant_ids:
                            if int_sp.in_date.split(' ')[0]  <=  date_to:
                                purchase_return_cb += int_sp.inventory_value
                        
                        
                for dest in product_dest1_cb:
                    if dest.location_id.usage == 'supplier' and dest.location_dest_id.usage == 'internal':
                        
                        for dt_si in dest.quant_ids:
                            if dt_si.in_date.split(' ')[0]  <=  date_to:
                                purchase_cb += dt_si.inventory_value
                            
                    if dest.location_id.usage == 'production' and dest.location_dest_id.usage == 'internal':
                        
                        for dt_pi in dest.quant_ids:
                            if dt_pi.in_date.split(' ')[0]  <=  date_to:
                                production_cb += dt_pi.inventory_value
                             
                    if dest.location_id.usage == 'internal' and dest.location_dest_id.usage == 'internal':
                        
                        for dt_int in dest.quant_ids:
                            if dt_int.in_date.split(' ')[0]  <=  date_to:
                                transfer_two_cb += dt_int.inventory_value
                            
                    if dest.location_id.usage == 'customer' and dest.location_dest_id.usage == 'internal':
                        
                        for dt_ci in dest.quant_ids:
                            if dt_ci.in_date.split(' ')[0]  <=  date_to:
                                sale_return_cb += dt_ci.inventory_value
                            
                            
                    if dest.location_id.usage == 'inventory' and dest.location_dest_id.usage =='internal':
                        
                        for dt_invnt in dest.quant_ids:
                            if dt_invnt.in_date.split(' ')[0]  <=  date_to:
                                inventory_loss1_cb += dt_invnt.inventory_value
            
            
            closing_bal_cb = purchase_cb + production_cb - transfer_cb + (inventory_loss1_cb - inventory_loss_cb) - itp_cb - sale_cb + transfer_two_cb + sale_return_cb -purchase_return_cb
            
            n_sale_val= sale_return - sale
            if n_sale_val < 0:
                n_sale_val = -1 *(n_sale_val)
              
            if check:
                vals = {
#                     'code': product.default_code or ' ',
#                     'name': product.name + ' ' + str(product.attribute_value_ids.name or ' '),
#                     'production': production*cost or 0,
#                     #'purchase': purchase*cost or 0,
#                     #'sale': sale*sale_price,
#                     'purchase': (purchase - purchase_return) *cost or 0,
#                     'sale': n_sale_val *sale_price,
#                     'transfer': (transfer_two - transfer)*cost,
#                     'inventory_loss': (inventory_loss1 - inventory_loss)*cost,
#                     'itp': itp*cost,
#                     'opening_bal': opening_bal*cost,
#                     #'closing_bal': closing_bal*cost
#                     'closing_bal': closing_bal_cb*cost
#                     
                    
                    
                    'code': product.default_code or ' ',
                    'name': product.name + ' ' + str(product.attribute_value_ids.name or ' '),
                    'production': production or 0,
                    #'purchase': purchase*cost or 0,
                    #'sale': sale*sale_price,
                    'purchase': (purchase - purchase_return) or 0,
                    'sale': n_sale_val *sale_price,
                    'transfer': (transfer_two - transfer),
                    'inventory_loss': (inventory_loss1 - inventory_loss),
                    'itp': itp*cost,
                    'opening_bal': opening_bal,
                    #'closing_bal': closing_bal*cost
                    'closing_bal': closing_bal_cb
                }
            else:
                vals = {
                        'code': product.default_code or ' ',
                        'name': product.name + ' ' + str(product.attribute_value_ids.name or ' '),
                        'production':production or 0,
                        #'purchase': purchase or 0,
                        #'sale': sale,
                        'purchase': (purchase - purchase_return) or 0,
                        'sale': n_sale_val,
                        'transfer': transfer_two - transfer,
                        'inventory_loss': inventory_loss1 - inventory_loss,
                        'itp': itp,
                        'opening_bal': opening_bal,
                        #'closing_bal':closing_bal
                        'closing_bal':closing_bal_cb
                        }
            lines.append(vals)
        return lines

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
#         report_name = data['form']['report_type']
        
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center', 'bold': True})
        format11 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True,})
#         format123 = workbook.set_column('A:A', 100)
        period_format= workbook.add_format({'font_size': 11, 'align': 'center', 'bold': True})

        format12 = workbook.add_format({'font_size': 11, 'align': 'center', 'bold': True,'right': True, 'left': True,'bottom': True, 'top': True})
        format21 = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'right', 'right': True, 'left': True,'bottom': True, 'top': True})
        format21.set_num_format('#,##0.00')
        qty_format = workbook.add_format({'font_size': 10, 'align': 'right', 'right': True, 'left': True,'bottom': True, 'top': True})
        qty_format.set_num_format('#,##0.000')
        Pname_format = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': True,'bottom': True, 'top': True})
        format_center = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True})
        subtotal_format = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'right', 'right': True, 'left': True,'bottom': True, 'top': True})
        subtotal_format.set_num_format('#,##0.000')
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
#         style = workbook.add_format('align: wrap yes; borders: top thin, bottom thin, left thin, right thin;')
#         style.num_format_str = '#,##0.00'
#         format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center') 
        red_mark.set_align('center')
                
        date_from = datetime.strptime(data['form']['date_from'], '%Y-%m-%d').strftime('%d/%m/%y')
        date_to = datetime.strptime(data['form']['date_to'], '%Y-%m-%d').strftime('%d/%m/%y')
#         if report_name == 'grand_production_summary':
        sheet.merge_range(0, 0, 0, 9, 'Brand Wise Summary of Stock Movement', format11)
        sheet.merge_range(1, 0, 1, 9, 'Period from: ' + (date_from) +  ' to ' + (date_to), period_format)
     
        # report start
        product_row = 5
        cat_row = 2
        warehouse = data['form']['warehouse']
        category = self.env['product.category'].search([])
        product_categ = data['form']['product_categ']
        if product_categ:
            category = self.env['product.category'].search([('id','in',product_categ)])
        else:
            category = self.env['product.category'].search([])
        if warehouse:
            warehouses = self.env['stock.warehouse'].search([('id','=',warehouse)])
               
#         else:
#             locations = self.env['stock.location'].search([])
#             warehouses = self.env['stock.warehouse'].search([])
#         if report_name == 'grand_production_summary':
        for ware in warehouses:
            
            if data['form']['location']:
                locations = self.env['stock.location'].search([('id','in',data['form']['location'])])
            else:
                locations = self.env['stock.location'].search([('Wr_id','=',warehouse)])
#             array1 = []
#             for lo in locations:
#                 array1.append(lo.id)
#             product_data=  self.env['mrp.production'].search([('create_date', '>=',data['form']['date_from']),('create_date', '<=',data['form']['date_to'])])
#             if product_data:
            sheet.merge_range(product_row-3, 0, product_row-3, 2,ware.name, format12)
        
            for cat in category:
                
                get_lines = self.get_lines(data['form']['date_from'],data['form']['date_to'],category,data['form']['product'],cat,ware,locations,data['form']['check'])
        #        
                if get_lines:  
                    total_ob = 0.0
                    total_pu=0.0
                    total_p=0.0
                    total_t=0.0
                    total_adj=0.0
                    total_itp=0.0
                    total_s=0.0
                    total_cb=0.0
                    sheet.write(product_row-2, 0, 'Category', format12)
                    sheet.merge_range(product_row-2, 1,product_row-2, 2,cat.name, format12)
                    
                    sheet.write(product_row-1, 0,'Code', format12)
                    sheet.write(product_row-1, 1,'Name', format12)
                    sheet.write(product_row-1, 2,'Opening Balance', format12)
                    sheet.write(product_row-1, 3,'Purchase', format12)
                    sheet.write(product_row-1, 4,'Production', format12)
                    sheet.write(product_row-1, 5,'Transfers', format12)
                    sheet.write(product_row-1, 6,'Adjustments (+/-)', format12)
                    sheet.write(product_row-1, 7,'Issue to Production', format12)
                    sheet.write(product_row-1, 8,'Sale', format12)
                    sheet.write(product_row-1, 9,'Closing Balance', format12)
                
                   
                    
#                     temp_code='None'
#                     product_code = []
                    for line in get_lines:
                        
                        
#                         if temp_code != line['code']:
#                             for pro_line in get_lines:
#                                 if pro_line['code'] == line['code']:
#                                     total1+=pro_line['production']
                        sheet.write(product_row, 0, line['code'], format_center)
                        sheet.write(product_row, 1, line['name'], Pname_format)
                        sheet.write(product_row, 2, line['opening_bal'], qty_format)
                        sheet.write(product_row, 3, line['purchase'], qty_format)
                        sheet.write(product_row, 4, line['production'], qty_format)
                        sheet.write(product_row, 5, line['transfer'], qty_format)
                        sheet.write(product_row, 6, line['inventory_loss'], qty_format)
                        sheet.write(product_row, 7, line['itp'], qty_format)
                        sheet.write(product_row, 8, line['sale'], qty_format)
                        sheet.write(product_row, 9, line['closing_bal'], qty_format)

                        product_row +=1
                             
#                         total1=0    
#                     total+=line['production']
#                     temp_code= line['code']
                        total_ob +=line['opening_bal']
                        total_pu += line['purchase']
                        total_p += line['production']
                        total_t += line['transfer']
                        total_adj += line['inventory_loss']
                        total_itp += line['itp']
                        total_s += line['sale']
                        total_cb += line['closing_bal']
                        
                    sheet.write(product_row, 1,'Sub Total', format21)
                    sheet.write(product_row, 2, total_ob, subtotal_format)
                    sheet.write(product_row, 3, total_pu, subtotal_format)
                    sheet.write(product_row, 4, total_p, subtotal_format)
                    sheet.write(product_row, 5, total_t, subtotal_format)
                    sheet.write(product_row, 6, total_adj, subtotal_format)
                    sheet.write(product_row, 7, total_itp, subtotal_format)
                    sheet.write(product_row, 8, total_s, subtotal_format)
                    sheet.write(product_row, 9, total_cb, subtotal_format)

                    product_row+=4

StockReportXls('report.export_stockinfo_xls.stock_report_xls.xlsx', 'product.product')
