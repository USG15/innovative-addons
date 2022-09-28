# -*- coding: utf-8 -*-

from odoo import api, fields, models, modules, _
from odoo.exceptions import UserError

# Test Picking print
class TestStockPicking(models.Model):
	_inherit = 'stock.picking'

	# PRINT example2
	@api.multi
	def action_to_print(self):
		model_id = self.env['ir.model'].search([('model','=','stock.picking')], limit=1)
		template = self.env['pdf.template.generator'].search([
			('model_id','=',model_id.id),
			('name','=','stock_picking_ready')], limit=1)
		
		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(_('Not found print template, Contact to your administrator!'))   

	# PRINT example
	@api.multi
	def action_to_print_move(self):
		model_id = self.env['ir.model'].search([('model','=','stock.picking')], limit=1)

		template = False
		# If choose language
		template = self.env['pdf.template.generator'].search([
			('model_id','=',model_id.id),
			('lang_id.code','=',self.env.user.lang),
			('name','=','stock_picking_move')], limit=1)
		if template:
			res = template.print_template(self.id)
			return res
		else:
			# No language 
			template = self.env['pdf.template.generator'].search([
				('model_id','=',model_id.id),
				('lang_id','=',False),
				('name','=','stock_picking_move')], limit=1)
		
		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(_('Not found print template, Contact to your administrator!'))   

	# FUNCTION_SIMPLE example
	@api.multi
	def _get_total_qty(self, ids):
		obj = self.env['stock.picking'].browse(ids)
		tot = sum(obj.move_lines.mapped('product_uom_qty'))
		return str(round(tot,3))
