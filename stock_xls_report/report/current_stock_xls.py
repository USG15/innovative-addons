from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx



class StockReportXls(ReportXlsx):

    def get_warehouse(self, data):
#         if data.get('form', False) and data['form'].get('warehouse', False):
            l1 = []
            l2 = []
            l3 = []
            if data['form']['warehouse']:
                obj = self.env['stock.warehouse'].search([('id', '=', data['form']['warehouse'])])
                loc = self.env['stock.location'].search([('id', 'in', data['form']['location'])])
            else:
                obj = self.env['stock.warehouse'].search([])[0]
                loc = self.env['stock.location'].search([('id', 'in', data['form']['location'])])
            for j in obj:
                l1.append(j.name)
                l2.append(j.id)
            
            for j2 in loc:
                l3.append(j2.name)
            return l1, l2,l3

    def get_location(self, data):
        if data.get('form', False) and data['form'].get('category', False):
        
            l3=[]
            if data['form']['location']:
                loc = self.env['stock.location'].search([('id', 'in', data['form']['location'])])
#             elif data['form']['warehouse']:
#                 obj_wr = self.env['stock.warehouse'].search([('id', '=', data['form']['warehouse'])])
#                 loc = self.env['stock.location'].search([])
#                 loc = self.env['stock.location'].search([('Wr_id','=',obj_wr.id)])
            
            if not data['form']['warehouse']:
                loc = self.env['stock.location'].search([])
               
            for k in loc:
                l3.append(k.id)
            return l3
        
            
        return ''
    def get_category(self, data):
        if data.get('form', False) and data['form'].get('category', False):
            l2 = []
            obj = self.env['product.category'].search([('id', 'in', data['form']['category'])])
           
            for j in obj:
                l2.append(j.id)
            return l2
        
            
        return ''

    def get_lines(self, data, warehouse):
        lines = []
        
        check = 0
        purchase=0
        sales=0
        production=0
        issue_sale=0
        adjustment=0
        
        categ = self.get_category(data)
        location = self.get_location(data)

        if categ:
            if(data['form']['product']):
                stock_history = self.env['product.product'].search([('categ_id', 'in', categ),('id','in',data['form']['product'])])
            else:
                stock_history = self.env['product.product'].search([('categ_id', 'in', categ)])
#         else:
#             if data['form']['location']:
#                 stock_history = self.env['product.product'].search([('stock_quant_ids.location_id','in',data['form']['location'])])
#             
#             else:
        else:
            stock_history = self.env['product.product'].search([])
        
            
        for obj in stock_history:
            sale_value = 0
            purchase_value = 0
           
#             product = self.env['product.product'].search([('id','=',obj.id),('create_date','<=',data['form']['date_from'])])
            product = self.env['product.product'].search([('id','=',obj.id)])

            
           
            
#             pr_hist =self.env['stock.history'].search([('product_id','=',obj.id),('move_id.location_id.usage','=','supplier'),('date','>=',data['form']['date_from']),('date','<=',data['form']['date_to'])])
#             pr_hist =self.env['purchase.order.line'].search([('product_id','=',obj.id),('state','=','done'),('date_planned','>=',data['form']['date_from']),('date_planned','<=',data['form']['date_to'])])
            pr_hist =self.env['stock.pack.operation'].search([('product_id','=',obj.id),('state','=','done'),('picking_id.location_id','in',location),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to']),('location_dest_id','in',location)])
            pr_hist = pr_hist.filtered(lambda r: r.from_loc == 'Vendors')
            
            pr_return_hist =self.env['stock.pack.operation'].search([('product_id','=',obj.id),('state','=','done'),('picking_id.location_id','in',location),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to']),('location_dest_id','in',location)])
            pr_return_hist = pr_return_hist.filtered(lambda r: r.to_loc == 'Vendors')
            
#             production_hist = self.env['stock.history'].search([('product_id','=',obj.id),('move_id.location_id.usage','=','production')])
            production_hist = self.env['mrp.production'].search([('location_dest_id','in',location),('product_id','=',obj.id),('date_planned_start','>=',data['form']['date_from']),('date_planned_start','<=',data['form']['date_to'])])
#             sales_hist = self.env['sale.order.line'].search([('product_id','=',obj.id),('state','=','done'),('order_id.confirmation_date','>=',data['form']['date_from']),('order_id.confirmation_date','<=',data['form']['date_to'])])
#             sales_hist = self.env['product.product'].search([('id','=',obj.id)]).stock_quant_ids #self.env['stock.history'].search([('product_id','=',obj.id)])
            sales_hist = self.env['stock.pack.operation'].search([('product_id','=',obj.id),('state','=','done'),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to']),('location_dest_id','in',location),('picking_id.location_id','in',location),])
            sales_hist = sales_hist.filtered(lambda r: r.to_loc == 'Customers')
            
            return_sales = self.env['stock.pack.operation'].search([('product_id','=',obj.id),('state','=','done'),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to']),('location_dest_id','in',location),('picking_id.location_id','in',location),])
            return_sales = return_sales.filtered(lambda r: r.from_loc == 'Customers')
#             issue_sale_stock_produ = self.env['stock.history'].search([('product_id','=',obj.id),('move_id.location_id.usage','=','internal'),('move_id.quant_ids.location_id.usage','=','production')])
#             issue_sale_stock_produ = self.env['sale.order.line'].search([('product_id','=',obj.id),('state','=','done'),('order_id.confirmation_date','>=',data['form']['date_from']),('order_id.confirmation_date','<=',data['form']['date_to'])])
            issue_sale_stock_produ = self.env['stock.move'].search([('product_id','=',obj.id),('location_id','in',location),('location_dest_id','in',location),('raw_material_production_id.date_planned_start','>=',data['form']['date_from']),('raw_material_production_id.date_planned_start','<=',data['form']['date_to'])])
#             all_trnsfr_in = self.env['stock.move'].search([('product_id','=',obj.id),('picking_id.location_id.usage','=','inventory'),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to'])])
#             all_trnsfr_out = self.env['stock.move'].search([('product_id','=',obj.id),('picking_id.location_dest_id.usage','=','inventory'),('picking_id.min_date','>=',data['form']['date_from']),('picking_id.min_date','<=',data['form']['date_to'])])
            all_trnsfr_in = self.env['stock.move'].search([('product_id','=',obj.id),('location_id.usage','=','inventory'),('location_dest_id','in',location),('date','>=',data['form']['date_from']),('date','<=',data['form']['date_to'])])
            all_trnsfr_out = self.env['stock.move'].search([('product_id','=',obj.id),('location_dest_id.usage','=','inventory'),('location_dest_id','in',location),('date','>=',data['form']['date_from']),('date','<=',data['form']['date_to'])])
            
            all_trn_in =0
            all_trn_out =0
            all_transfr =0
            return_pur =0
            purchase=0
            return_sale=0
            sales=0
            production=0
            issue_sale=0
            adjustment=0
            
#             for issp in issue_sale_stock_produ:
# #                 sales = sales + issp.product_uom_qty
#                 issue_sale = issue_sale+issp.product_uom_qty
           
            for issp in issue_sale_stock_produ:
#                 move_id.
                issue_sale = issue_sale+issp.product_uom_qty
                
            for smov in pr_return_hist:
                return_pur =  return_pur + smov.qty_done
                
            for smov in pr_hist:
                purchase = purchase + smov.qty_done
            purchase = purchase - return_pur  
#                 
            for smov in production_hist:
                production = production + smov.product_qty
#                 production = production + smov.move_id.product_qty
             
            for smov in return_sales:
                return_sale = return_sale + smov.qty_done 
                                    
            for smov in sales_hist:
                sales = sales + smov.qty_done 
            sales = sales - return_sale
            
            
            for trsfr in all_trnsfr_in:
                all_trn_in = all_trn_in + trsfr.product_uom_qty
                # print trsfr.name
                # print trsfr.product_uom_qty
            for trsfr_out in all_trnsfr_out:
#                 move_id.
                all_trn_out = all_trn_out + trsfr_out.product_uom_qty 
       
            all_transfr = all_trn_in - all_trn_out
             
       
#             adjustment is really transfer
            ob = self.get_ob(obj,data['form']['date_from'],location,data['form']['product'])
            cb = self.get_cb(obj,data['form']['date_to'],location,data['form']['product'])
# - cb
            adjustment =  -1*(ob + purchase  + production + all_transfr - issue_sale - sales -cb)
            

           
                
            sale_obj = self.env['sale.order.line'].search([('order_id.state', '=', 'done'),
                                                           ('product_id', '=', product.id),
                                                           ('order_id.warehouse_id', '=', warehouse)])
            for i in sale_obj:
                sale_value = sale_value + i.product_uom_qty
            purchase_obj = self.env['purchase.order.line'].search([('order_id.state', '=', 'done'),('product_id', '=', product.id),('order_id.picking_type_id', '=', warehouse),('date_planned','>=',data['form']['date_from']),('date_planned','<=',data['form']['date_to'])])
            for i in purchase_obj:
                purchase_value = purchase_value + i.product_qty
            
            
            
#             print loc
            if(sales != 0 or purchase!=0 or self.get_ob(obj,data['form']['date_from'],location,data['form']['product']) !=0 or
               self.get_cb(obj,data['form']['date_to'],location,data['form']['product']) !=0 or all_transfr !=0 or production!=0 or issue_sale !=0 or adjustment != 0):
                if(data['form']['check'] == True):
                    vals = {
                        'sku': obj.default_code,
                        'name': obj.name+' '+obj.attribute_value_ids.name,
                        'category': obj.categ_id.name,
                        'sale_value': sales*obj.standard_price,#product.sales_count,
                        'purchase_value':purchase*obj.standard_price, #product.purchase_count, 
                        'ob': self.get_ob(obj,data['form']['date_from'],location,data['form']['product'])*obj.standard_price,#product.with_context({'warehouse': warehouse}).qty_available,
                        'cb': self.get_cb(obj,data['form']['date_to'],location,data['form']['product'])*obj.standard_price,#product_close.with_context({'warehouse': warehouse}).qty_available,
                        
                        
                        'adjustment':all_transfr*obj.standard_price,#adjustment,#sumadj,
                        'production':production*obj.standard_price,
                        'issue_sale':issue_sale*obj.standard_price,
                        'transfers':adjustment*obj.standard_price,
                    }
                    lines.append(vals)
                else:
                    print(str(obj.name))
                    print(str(obj.attribute_value_ids.name))
                    vals = {
                    'sku': obj.default_code,
                    'name': (str(obj.name))+' '+(str(obj.attribute_value_ids.name) ),
                    'category': obj.categ_id.name,
                    'sale_value': sales,#product.sales_count,
                    'purchase_value':purchase, #product.purchase_count, 
                    'ob': self.get_ob(obj,data['form']['date_from'],location,data['form']['product']),#product.with_context({'warehouse': warehouse}).qty_available,
                    'cb': self.get_cb(obj,data['form']['date_to'],location,data['form']['product']),#product_close.with_context({'warehouse': warehouse}).qty_available,

                    
                    'adjustment':all_transfr,#adjustment,#sumadj,
                    'production':production,
                    'issue_sale':issue_sale,
                    'transfers':adjustment,
                }
                    lines.append(vals)
    
        return lines
    
    #opening Balance
    def get_ob(self,product,date_from,location,product_field):
        if product_field:
            product_ob_ids = self.env['stock.history'].search([('location_id','in',location),('product_id','=',product.name),('date','<=',date_from)])
        else:
            all_location = self.env['stock.location'].search([('id','in',location)])
            for l in all_location:
                loc = self.env['stock.warehouse'].search([('name','=',l.Wr_id.name)])
                print (loc.name)
                if loc.name:
                    warehouse = loc.name
            product_ob_ids = self.env['stock.quant'].search([('location_id.Wr_id.name', '=', warehouse), ('product_id', '=', product.id),
                                        ('create_date', '<=', date_from)])
        # product_ob_ids = self.env['stock.history'].search([('location_id','in',location),('product_id','=',product.name),('date','<=',date_from)])
        ob_quantity =0.0

        for product_ob_id in product_ob_ids:
            if product_field:
                ob_quantity += product_ob_id.quantity
            else:
                ob_quantity += product_ob_id.qty
        return ob_quantity
    
    #clossing Balan
    def get_cb(self,product,date_to,location,product_field):
        if product_field:
            product_ob_ids = self.env['stock.history'].search([('location_id','in',location),('product_id','=',product.name),('date','<=',date_to)])
        else:
            all_location = self.env['stock.location'].search([('id','in',location)])
            for l in all_location:
                loc = self.env['stock.warehouse'].search([('name','=',l.Wr_id.name)])
                print (loc.name)
                if loc.name:
                    warehouse = loc.name
            product_ob_ids = self.env['stock.quant'].search([('location_id.Wr_id.name', '=', warehouse), ('product_id', '=', product.id),
                                        ('create_date', '<=', date_to)])
        ob_quantity =0.0
        
        for product_ob_id in product_ob_ids:
            if product_field:
                ob_quantity += product_ob_id.quantity
            else:
                ob_quantity += product_ob_id.qty
        return ob_quantity
    


    def generate_xlsx_report(self, workbook, data, lines):
        get_warehouse = self.get_warehouse(data)
        data1=data
        sheet = workbook.add_worksheet("get_warehouse")
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        formatblack = workbook.add_format({'font_size': 8, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        underline = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True,'underline':True})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')#                         sheet.write(prod_row, prod_col + 4, each['cost_price'], font_size_8)
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range('A2:G2', 'Brand Wise Summary of Stock Movement', underline)
        sheet.merge_range('A3:G3', 'Period From: ' + data['form']['date_from']+' To '+data['form']['date_to'], font_size_8)        
#         sheet.merge_range(2, 7, 2, count, 'Warehouses', format1)
        sheet.merge_range(2, 7, 2,'Warehouses', format1)

        
        
        def footertable():
            return
        
        def headertable(prod_row):
            print('sss')
            print(data1)
            sheet.merge_range('A'+str(prod_row)+':B'+str(prod_row), 'Category', format21)
            w_col_no = 6
            w_col_no1 = 7
            for i in get_warehouse[0]:
                w_col_no = w_col_no + 11
                sheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                w_col_no1 = w_col_no1 + 11
            sheet.merge_range(prod_row+1, 0,prod_row,0, 'Code', format21)
            sheet.merge_range(prod_row+1, 1, prod_row, 3, 'Name', format21)

            p_col_no1 = 4
            p_col_inc = 10
            for i in get_warehouse[0]:
                if(data1['form']['check'] == True):
                    sheet.merge_range(prod_row+1, p_col_no1,prod_row, p_col_no1+1, 'Opening Balance/Rs', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 2,prod_row, p_col_no1+3, 'Purchase/Rs', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 4,prod_row, p_col_no1+5, 'Production/Rs', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 6,prod_row, p_col_no1+7, 'Transfers/Rs', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 8,prod_row, p_col_no1+9, 'Adjustments (+/-)/Rs', format21)
                  
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc, prod_row+1, p_col_no1 + p_col_inc+1, 'Issue to Production/Rs', format21)
                    
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc+2, prod_row+1, p_col_no1 + p_col_inc+3, 'Sale/Rs', format21)
    
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc+4, prod_row+1, p_col_no1 + p_col_inc+5,  'Closing Balance/Rs', format21)

                    
                else:
                    sheet.merge_range(prod_row+1, p_col_no1,prod_row, p_col_no1+1, 'Opening Balance', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 2,prod_row, p_col_no1+3, 'Purchase', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 4,prod_row, p_col_no1+5, 'Production', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 6,prod_row, p_col_no1+7, 'Transfers', format21)
                    sheet.merge_range(prod_row+1, p_col_no1 + 8,prod_row, p_col_no1+9, 'Adjustments (+/-)', format21)
                  
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc, prod_row+1, p_col_no1 + p_col_inc+1, 'Issue to Production', format21)
                    
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc+2, prod_row+1, p_col_no1 + p_col_inc+3, 'Sale', format21)
    
                    sheet.merge_range(prod_row, p_col_no1 + p_col_inc+4, prod_row+1, p_col_no1 + p_col_inc+5,  'Closing Balance', format21)

                p_col_no1 = p_col_no1 + 11
            
      
        
                
#             Loading data
        prod_row =6
        prod_col = 0
        headertable(prod_row-1)
        
        headertable(5)
        for i in get_warehouse[1]:
            
            get_line = self.get_lines(data, i)
#             if not get_line:
#                 get_line = self.parentline(data, i)
            
            rem_dup = set()
            for ech in get_line:
                if ech['category'] not in rem_dup:
                    rem_dup.add(ech['category'])
                else:
                    pass
            for uniq in rem_dup:
                check=0
                headertable(prod_row-1)
                for each in get_line:
                      
                    if each['category'] == uniq:  
                        if(check < 1):
                            sheet.merge_range('C'+str(prod_row-1)+':F'+str(prod_row-1) ,each['category'], format21)
                            check = check +1   
                        sheet.write(prod_row+1, prod_col, each['sku'], font_size_8)
                        sheet.merge_range(prod_row+1, prod_col + 1, prod_row+1, prod_col + 3, each['name'], font_size_8)
                          
#                         sheet.write(prod_row, prod_col + 4, each['cost_price'], font_size_8)
                        prod_row = prod_row + 1
#                 headertable(prod_row+2)
                prod_row = prod_row +6
#                 break
            break
        prod_row = 6
        prod_col = 4
        ro_inc = 0
        
        avail1=[]
        
        purvalue1=[]
        prodct1=[]
        adjt1=[]
        iq1=[]
        sq1=[]
        
        tq1=[]
        trfs1=[]
        
        for i in get_warehouse[1]:
            get_line = self.get_lines(data, i)
#             if not get_line:
#                 get_line = self.parentline(data, i)
            
            
            rem_dup = set()
            for ech in get_line:
                if ech['category'] not in rem_dup:
                    rem_dup.add(ech['category'])
                else:
                    pass
            
            for uniq in rem_dup:
                avail=[]
                
                purvalue=[]
                prodct=[]
                adjt=[]
                iq=[]
                sq=[]
               
                tq=[]
                trfs=[]
                
                
                if(ro_inc > 0):
                    prod_row = prod_row +6
#                     sheet.merge_range(prod_row+2, prod_col-2,prod_row+2, prod_col-1, 'Grand Total', font_size_8)
                      
                for each in get_line:
                    
                    if each['category'] == uniq:  
#                          opening
                        sheet.merge_range(prod_row+2, prod_col-2,prod_row+2, prod_col-1, 'Sub Total', formatblack)
                        if(data['form']['check'] == True):
                            if each['ob'] < 0:
                                sheet.merge_range(prod_row+1, prod_col,prod_row+1,prod_col+1, '{0:,.2f}'.format(each['ob']), red_mark)
                                avail.append(each['ob'])
                                avail1.append(each['ob'])
                                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1, '{0:,.2f}'.format(sum(avail)), font_size_8)
                            else:
                                avail.append(each['ob'])
                                avail1.append(each['ob'])
                                sheet.merge_range(prod_row+1, prod_col,prod_row+1,prod_col+1, '{0:,.2f}'.format(each['ob']), font_size_8)
                                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1, '{0:,.2f}'.format(sum(avail)), font_size_8)
    #                        Total
                            if each['purchase_value'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 2,prod_row+1, prod_col + 3, '{0:,.2f}'.format(each['purchase_value']), red_mark)
                                purvalue.append(each['purchase_value'])
                                purvalue1.append(each['purchase_value'])
                                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3, '{0:,.2f}'.format(sum(purvalue)), font_size_8)
                        
                            else:
                                sheet.merge_range(prod_row+1, prod_col + 2,prod_row+1, prod_col + 3, '{0:,.2f}'.format(each['purchase_value']), font_size_8)
                                purvalue.append(each['purchase_value'])
                                purvalue1.append(each['purchase_value'])
                                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3, '{0:,.2f}'.format(sum(purvalue)), font_size_8)
                        
                            
                            if each['production'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 4,prod_row+1, prod_col + 5, '{0:,.2f}'.format(each['production']), red_mark)
                                prodct.append(each['production'])
                                prodct1.append(each['production'])
                                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5, '{0:,.2f}'.format(sum(prodct)), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+4, prod_row+1, prod_col + 5,'{0:,.2f}'.format(each['production']), font_size_8)
                                prodct.append(each['production'])
                                prodct1.append(each['production'])
                                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5, '{0:,.2f}'.format(sum(prodct)), font_size_8)
                         
                            if each['transfers'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 6,prod_row+1, prod_col + 7,'{0:,.2f}'.format(each['transfers']), red_mark)
                                trfs.append(each['transfers'])
                                trfs1.append(each['transfers'])
                                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7, '{0:,.2f}'.format(sum(trfs)), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+6, prod_row+1, prod_col + 7,'{0:,.2f}'.format(each['transfers']), font_size_8)
                                trfs.append(each['transfers'])
                                trfs1.append(each['transfers'])
                                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7,'{0:,.2f}'.format(sum(trfs)), font_size_8) 
                             
                            if each['adjustment'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 8,prod_row+1, prod_col + 9,'{0:,.2f}'.format(each['adjustment']), red_mark)
                                adjt.append(each['adjustment'])
                                adjt1.append(each['adjustment'])
                                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9,'{0:,.2f}'.format(sum(adjt)), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+8, prod_row+1, prod_col + 9,'{0:,.2f}'.format(each['adjustment']), font_size_8)
                                adjt.append(each['adjustment'])
                                adjt1.append(each['adjustment'])
                                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9,'{0:,.2f}'.format(sum(adjt)), font_size_8)
                                                
                          
                            if each['issue_sale'] < 0:
                                iq.append(each['issue_sale'])
                                iq1.append(each['issue_sale'])
                                sheet.merge_range(prod_row+1,prod_col+10,prod_row+1,prod_col + 11,'{0:,.2f}'.format(each['issue_sale']), red_mark)
                                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11,'{0:,.2f}'.format(sum(iq)), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1,prod_col+10,prod_row+1,prod_col +11,'{0:,.2f}'.format(each['issue_sale']), font_size_8)
                                iq.append(each['issue_sale'])
                                iq1.append(each['issue_sale'])
                                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11,'{0:,.2f}'.format(sum(iq)), font_size_8)
                         
     
    #                         #for sale qty     
                            if each['sale_value'] < 0:
                                sq.append(each['sale_value'])
                                sq1.append(each['sale_value'])
                                sheet.merge_range(prod_row+1,prod_col+12,prod_row+1,prod_col + 13,'{0:,.2f}'.format(each['sale_value']), red_mark)
                                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13,'{0:,.2f}'.format(sum(sq)), font_size_8)
                         
                            else:
                                sq.append(each['sale_value'])
                                sq1.append(each['sale_value'])
                                sheet.merge_range(prod_row+1,prod_col+12,prod_row+1,prod_col + 13,'{0:,.2f}'.format(each['sale_value']), font_size_8)
                                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13,'{0:,.2f}'.format(sum(sq)), font_size_8)
                        
                            if each['cb'] < 0:
                                tq.append(each['cb'])
                                tq1.append(each['cb'])
                                sheet.merge_range(prod_row+1, prod_col+14,prod_row+1, prod_col+ 15,'{0:,.2f}'.format(each['cb']), red_mark)
                                sheet.merge_range(prod_row+2, prod_col+14,prod_row+2, prod_col+15,'{0:,.2f}'.format(sum(tq)), font_size_8)
                            
                            else:
                                tq.append(each['cb'])
                                tq1.append(each['cb'])
                                sheet.merge_range(prod_row+1, prod_col + 14,prod_row+1, prod_col+  15, '{0:,.2f}'.format(each['cb']), font_size_8)
                                sheet.merge_range(prod_row+2, prod_col+ 14,prod_row+2, prod_col+ 15, '{0:,.2f}'.format(sum(tq)), font_size_8)
                        else:
                            if each['ob'] < 0:
                                sheet.merge_range(prod_row+1, prod_col,prod_row+1,prod_col+1, each['ob'], red_mark)
                                avail.append(each['ob'])
                                avail1.append(each['ob'])
                                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1, sum(avail), font_size_8)
                            else:
                                avail.append(each['ob'])
                                avail1.append(each['ob'])
                                sheet.merge_range(prod_row+1, prod_col,prod_row+1,prod_col+1, each['ob'], font_size_8)
                                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1,sum(avail), font_size_8)
    #                        Total
                            if each['purchase_value'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 2,prod_row+1, prod_col + 3, each['purchase_value'], red_mark)
                                purvalue.append(each['purchase_value'])
                                purvalue1.append(each['purchase_value'])
                                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3, sum(purvalue), font_size_8)
                        
                            else:
                                sheet.merge_range(prod_row+1, prod_col + 2,prod_row+1, prod_col + 3,each['purchase_value'], font_size_8)
                                purvalue.append(each['purchase_value'])
                                purvalue1.append(each['purchase_value'])
                                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3,sum(purvalue), font_size_8)
                        
                            
                            if each['production'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 4,prod_row+1, prod_col + 5, each['production'], red_mark)
                                prodct.append(each['production'])
                                prodct1.append(each['production'])
                                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5,sum(prodct), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+4, prod_row+1, prod_col + 5,each['production'], font_size_8)
                                prodct.append(each['production'])
                                prodct1.append(each['production'])
                                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5,sum(prodct), font_size_8)
                         
                            if each['transfers'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 6,prod_row+1, prod_col + 7, each['transfers'], red_mark)
                                trfs.append(each['transfers'])
                                trfs1.append(each['transfers'])
                                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7,sum(trfs), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+6, prod_row+1, prod_col + 7,each['transfers'], font_size_8)
                                trfs.append(each['transfers'])
                                trfs1.append(each['transfers'])
                                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7,sum(trfs), font_size_8) 
                             
                            if each['adjustment'] < 0:
                                sheet.merge_range(prod_row+1, prod_col + 8,prod_row+1, prod_col + 9,  each['adjustment'], red_mark)
                                adjt.append(each['adjustment'])
                                adjt1.append(each['adjustment'])
                                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9, sum(adjt), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1, prod_col+8, prod_row+1, prod_col + 9,each['adjustment'], font_size_8)
                                adjt.append(each['adjustment'])
                                adjt1.append(each['adjustment'])
                                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9, sum(adjt), font_size_8)
                                                
                          
                            if each['issue_sale'] < 0:
                                iq.append(each['issue_sale'])
                                iq1.append(each['issue_sale'])
                                sheet.merge_range(prod_row+1,prod_col+10,prod_row+1,prod_col + 11, each['issue_sale'], red_mark)
                                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11, sum(iq), font_size_8)
                         
                            else:
                                sheet.merge_range(prod_row+1,prod_col+10,prod_row+1,prod_col +11,each['issue_sale'], font_size_8)
                                iq.append(each['issue_sale'])
                                iq1.append(each['issue_sale'])
                                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11,sum(iq), font_size_8)
                         
     
    #                         #for sale qty     
                            if each['sale_value'] < 0:
                                sq.append(each['sale_value'])
                                sq1.append(each['sale_value'])
                                sheet.merge_range(prod_row+1,prod_col+12,prod_row+1,prod_col + 13, each['sale_value'], red_mark)
                                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13, sum(sq), font_size_8)
                         
                            else:
                                sq.append(each['sale_value'])
                                sq1.append(each['sale_value'])
                                sheet.merge_range(prod_row+1,prod_col+12,prod_row+1,prod_col + 13,each['sale_value'], font_size_8)
                                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13, sum(sq), font_size_8)
                        
                            if each['cb'] < 0:
                                tq.append(each['cb'])
                                tq1.append(each['cb'])
                                sheet.merge_range(prod_row+1, prod_col+14,prod_row+1, prod_col+ 15, each['cb'], red_mark)
                                sheet.merge_range(prod_row+2, prod_col+14,prod_row+2, prod_col+15, sum(tq), font_size_8)
                            
                            else:
                                tq.append(each['cb'])
                                tq1.append(each['cb'])
                                sheet.merge_range(prod_row+1, prod_col + 14,prod_row+1, prod_col+  15, each['cb'], font_size_8)
                                sheet.merge_range(prod_row+2, prod_col+ 14,prod_row+2, prod_col+ 15,sum(tq), font_size_8)
#                             sheet.merge_range(prod_row+2, prod_col+p_col_inc + 8,prod_row+2, prod_col+p_col_inc + 9, sum(cb), font_size_8)
                        prod_row = prod_row + 1
                    ro_inc=ro_inc+1
            
#                     footertable(prod_row+1)
            if(data['form']['check'] == True):
                sheet.merge_range(prod_row+2, prod_col-2,prod_row+2, prod_col-1, 'Grand Total', formatblack)
                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1, '{0:,.2f}'.format(sum(avail1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3, '{0:,.2f}'.format(sum(purvalue1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5, '{0:,.2f}'.format(sum(prodct1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7, '{0:,.2f}'.format(sum(trfs1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9, '{0:,.2f}'.format(sum(adjt1)), font_size_8) 
                
                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11, '{0:,.2f}'.format(sum(iq1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13,'{0:,.2f}'.format( sum(sq1)), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+14,prod_row+2, prod_col+15, '{0:,.2f}'.format(sum(tq1)), font_size_8)
              
            else:
                sheet.merge_range(prod_row+2, prod_col-2,prod_row+2, prod_col-1, 'Grand Total', formatblack)
                sheet.merge_range(prod_row+2, prod_col,prod_row+2, prod_col+1, sum(avail1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+2,prod_row+2, prod_col+3, sum(purvalue1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+4,prod_row+2, prod_col+5, sum(prodct1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+6,prod_row+2, prod_col+7, sum(trfs1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+8,prod_row+2, prod_col+9, sum(adjt1), font_size_8) 
                
                sheet.merge_range(prod_row+2, prod_col+10,prod_row+2, prod_col+11, sum(iq1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+12,prod_row+2, prod_col+13, sum(sq1), font_size_8)
                sheet.merge_range(prod_row+2, prod_col+14,prod_row+2, prod_col+15, sum(tq1), font_size_8)
              
                   
            prod_row = 5
#             prod_row = prod_row +3
            prod_col = prod_col + 11

StockReportXls('report.export_stockinfo_xls.stock_report_xls.xlsx', 'product.product')
