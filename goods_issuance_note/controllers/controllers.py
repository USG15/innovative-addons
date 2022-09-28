# -*- coding: utf-8 -*-
from odoo import http

# class GoodsIssuanceNote(http.Controller):
#     @http.route('/goods_issuance_note/goods_issuance_note/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/goods_issuance_note/goods_issuance_note/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('goods_issuance_note.listing', {
#             'root': '/goods_issuance_note/goods_issuance_note',
#             'objects': http.request.env['goods_issuance_note.goods_issuance_note'].search([]),
#         })

#     @http.route('/goods_issuance_note/goods_issuance_note/objects/<model("goods_issuance_note.goods_issuance_note"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('goods_issuance_note.object', {
#             'object': obj
#         })