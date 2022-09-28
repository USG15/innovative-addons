# -*- coding: utf-8 -*-
from odoo import http

# class GoodsReceiveNote(http.Controller):
#     @http.route('/goods_receive_note/goods_receive_note/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/goods_receive_note/goods_receive_note/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('goods_receive_note.listing', {
#             'root': '/goods_receive_note/goods_receive_note',
#             'objects': http.request.env['goods_receive_note.goods_receive_note'].search([]),
#         })

#     @http.route('/goods_receive_note/goods_receive_note/objects/<model("goods_receive_note.goods_receive_note"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('goods_receive_note.object', {
#             'object': obj
#         })