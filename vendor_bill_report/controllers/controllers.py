# -*- coding: utf-8 -*-
from odoo import http

# class VendorBillReport(http.Controller):
#     @http.route('/vendor_bill_report/vendor_bill_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vendor_bill_report/vendor_bill_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vendor_bill_report.listing', {
#             'root': '/vendor_bill_report/vendor_bill_report',
#             'objects': http.request.env['vendor_bill_report.vendor_bill_report'].search([]),
#         })

#     @http.route('/vendor_bill_report/vendor_bill_report/objects/<model("vendor_bill_report.vendor_bill_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vendor_bill_report.object', {
#             'object': obj
#         })