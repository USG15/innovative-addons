# -*- coding: utf-8 -*-
from odoo import http

# class ApprovedPoReport(http.Controller):
#     @http.route('/approved_po_report/approved_po_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/approved_po_report/approved_po_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('approved_po_report.listing', {
#             'root': '/approved_po_report/approved_po_report',
#             'objects': http.request.env['approved_po_report.approved_po_report'].search([]),
#         })

#     @http.route('/approved_po_report/approved_po_report/objects/<model("approved_po_report.approved_po_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('approved_po_report.object', {
#             'object': obj
#         })