# -*- coding: utf-8 -*-

from odoo import api, fields, models, modules
from odoo import _, tools
from odoo.exceptions import UserError
import time
from io import BytesIO
import base64
import pdfkit
import re
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, SUPERUSER_ID
import pytz
from datetime import datetime

class ReportPdfOutput(models.TransientModel):
    _name = 'report.pdf.output'
    _description = "Report PDF Output"
    
    name = fields.Char('Filename', readonly=True)
    data = fields.Binary('File', readonly=True, required=True)
    date = fields.Datetime(default=lambda *a: time.strftime('%Y-%m-%d H:M:S'))

class PdfTemplateGenerator(models.Model):
	_name = 'pdf.template.generator'
	_description = 'PDF template generator'
	_order = 'name'

	# Columns
	name = fields.Char(string='Template name', required=True, help="You can use when search template configuration by this name")
	model_id = fields.Many2one('ir.model', string="Model name", help="Your model name")
	template_text = fields.Html('Template', required=True, help=u'PDF template body')

	margin_top = fields.Integer('Margin top', required=True, default=10)
	margin_left = fields.Integer('Margin left', required=True, default=10)
	margin_right = fields.Integer('Margin right', required=True, default=10)
	margin_bottom = fields.Integer('Margin bottom', required=True, default=10)

	lang_id = fields.Many2one('res.lang', string="Language", )

	paper_size = fields.Selection([
						('A4', 'A4'),
						('Letter', 'Letter'),
						('A4', 'A5'),
						('A6', 'A6'),
						('A7', 'A7'),
						('A8', 'A8'),
						('A9', 'A9'),
						('A10', 'A10')], 
		default='A4', required=True, string='Paper size')

	orientation = fields.Selection([
						('Portrait', 'Portrait'),
						('Landscape', 'Landscape')], 
		default='Portrait', required=True, string='Orientation')

	# _sql_constraints = [('name_uniq', 'unique(name)', 'Must be unique name!')]

	# Get binary DATA
	@api.multi
	def get_template_data(self, ids):
		html = self.template_text
		html = self._set_function_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)
		
		html = self._set_many2one_pattern(html, ids)
		html = self._set_simple_pattern(html, ids)
		
		html = self.encode_for_xml(html, 'ascii')

		options = {
			'page-size': self.paper_size,
			'margin-top': str(self.margin_top)+'mm',
			'margin-right': str(self.margin_right)+'mm',
			'margin-bottom': str(self.margin_bottom)+'mm',
			'margin-left': str(self.margin_left)+'mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': self.orientation,
		}
		path = modules.get_module_resource('pdf_template_generator', 'static/src/froala/css/froala_style.css')
		output = BytesIO(pdfkit.from_string(html,False,options=options, css=path)) 
		out = base64.encodestring(output.getvalue())

		return out

	# Direct print PDF
	@api.multi
	def print_template(self, ids):
		html = self.template_text
		html = self._set_function_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)
		
		html = self._set_many2one_pattern(html, ids)
		html = self._set_simple_pattern(html, ids)
		
		html = self.encode_for_xml(html, 'ascii')

		options = {
			'page-size': self.paper_size,
			'margin-top': str(self.margin_top)+'mm',
			'margin-right': str(self.margin_right)+'mm',
			'margin-bottom': str(self.margin_bottom)+'mm',
			'margin-left': str(self.margin_left)+'mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': self.orientation,
		}
		path = modules.get_module_resource('pdf_template_generator', 'static/src/froala/css/froala_style.css')
		output = BytesIO(pdfkit.from_string(html,False,options=options, css=path)) 
		out = base64.encodestring(output.getvalue())

		file_name = self.name+'.pdf'
		res_id = self.env['report.pdf.output'].create({'data': out, 'name': file_name})
		return {
			'target': 'new',
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.pdf.output&id=" + str(res_id.id) + "&filename_field=filename&field=data&filename=" + file_name,
		}

	# Fixed size on image
	def _set_image_field_with_size_pattern(self, text, ids):
		match = re.findall(r'{image_field:[\w.-]+:[0-9]+:[0-9]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			width = related_fields[2]
			height = related_fields[3]
			data = '???'

			pic = self.env['ir.attachment'].sudo().search([
				('res_model','=',self.model_id.model),
				('res_field','=',field_name),
				('res_id','=',ids),
				], limit=1)
			if pic:
				pic_url = pic._full_path(pic.store_fname)
				data = '''<img border="1" name="'''+field_name+'''"
					width="'''+width+'''" height="'''+height+'''" 
					src="'''+pic_url+'''">'''

			text = text.replace(pttrn_name,data)
		return text

	# No sized image
	def _set_image_field_pattern(self, text, ids):
		match = re.findall(r'{image_field:[\w.-]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			data = '???'

			pic = self.env['ir.attachment'].sudo().search([
				('res_model','=',self.model_id.model),
				('res_field','=',field_name),
				('res_id','=',ids),
				], limit=1)
			if pic:
				pic_url = pic._full_path(pic.store_fname)
				data = '''<img border="1" name="'''+field_name+'''"
					src="'''+pic_url+'''">'''

			text = text.replace(pttrn_name,data)
		return text

	# Print image by URLs
	# You can set many image's url
	# Data format
	# Ex: ['img.domain.mn/uploads/20160626/6f6bfbfa73e662c1505ab5858a14c3c2.jpg', 'img.domain.mn/uploads/order_note/20170928/74594d9c9904a50374b71b4bcc4d83e7.jpg', 'img.domain.mn/uploads/order_note/20170928/3195fdb649288984ae092ceff1fc6372.png']
	def _set_image_field_urls_pattern(self, text, ids):
		match = re.findall(r'{image_field_urls:[\w.-]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			images = ""
			urls = obj.sudo().read([field_name])[0][field_name] if obj.sudo().read([field_name])[0][field_name] else ''	
			if urls:
				urls = urls.replace('[','')
				urls = urls.replace(']','')
				urls = urls.replace("'",'')
				urls = urls.replace("'",'')
				urls = urls.replace(" ",'')
				urls = urls.strip()
				urls = urls.split(',')
				for url in urls:
					img = '''<img border="1" name="'''+field_name+'''"
						src="http://'''+url+'''"><br>'''
					images += img
			text = text.replace(pttrn_name,images)
		return text

	# Local image on template 
	def _set_out_img_src_pattern(self, text, ids):
		match = re.findall(r'/web/image/[0-9]+', text)
		for patern_name in match:
			pic_id = patern_name.split('/')[3]
			pic = self.env['ir.attachment'].sudo().search([('id','=',pic_id)], limit=1)
			text = text.replace(patern_name, pic._full_path(pic.store_fname))
		return text

	# Default WEB images
	def _set_img_src_pattern(self, text, ids):
		match = re.findall(r'/website/static/src/img/library', text)

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		if not base_url:
			raise UserError(u'Base URL тохиргоо хийгдээгүй байна! (ir.config_parameter:web.base.url)')

		array_match = []
		for item in match:
			array_match.append(item)

		for patern_name in array_match:
			text = text.replace(patern_name, base_url+patern_name)
		return text

	# Simple function
	def _set_function_simple_pattern(self, text, ids):
		match = re.findall(r'{function_simple:[\w.-]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')

			model = self.env[ self.model_id.model ]
			method_name = related_fields[1]
			data =  getattr(model, method_name)(ids)
			if type(data) in [float, int]:
				data = "{:,}".format(data)
			text = text.replace(pttrn_name,data)
		return text

	# Draw table by data
	# Call function then return DATA
	# Data format
	# return {'header':['col1','col2'],'data':[[112323,435345.5],[23.4,56]]}
	def _set_function_pattern(self, text, ids):
		match = re.findall(r'{function:[\w.-]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)
		
		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')

			model = self.env[ self.model_id.model ]
			method_name = related_fields[1]
			data =  getattr(model, method_name)(ids)
########
			table_lines = '<table style="border: 1px solid #dddddd;width:100%; font-size: 13pt; border-collapse: collapse; ">'
			# table_lines = '<table style="border:1px solid #dddddd;border-collapse: collapse;width:100%;font-size: 13pt;">'
			# Table ийн толгой зурах
			table_header = ''
			for th in data['header']:
				table_header += '<th>'+th+'</th>'
			table_lines += table_header

			for line in data['data']:
				row = '<tr>'
				for td in line:
					row += '<td style="border: 1px solid #dddddd;padding:1px; text-align:center;">'+ td +'</td>'
				table_lines += row +'</tr>'
			table_lines += '</table>'

			text = text.replace(pttrn_name, table_lines)
		return text

	# Simple fields, many2one, datetime
	def _set_simple_pattern(self, text, ids):
		data = self.env[ self.model_id.model ].sudo().fields_get()
		match = re.findall(r'{\w+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)
		
		for field_name in array_match:
			field = '{'+field_name+'}'
			if field_name in data:
				value = ''
				if str(data[field_name]['type'])=='many2one':
					value = obj.sudo().read([field_name])[0][field_name][1] if obj.sudo().read([field_name])[0][field_name] else ''	
				elif str(data[field_name]['type'])=='date':
					value = str(obj.sudo().read([field_name])[0][field_name]) if obj.sudo().read([field_name])[0][field_name] else ''
					value = value
				elif str(data[field_name]['type'])=='datetime':
					value = str(obj.sudo().read([field_name])[0][field_name]) if obj.sudo().read([field_name])[0][field_name] else ''
					
					tz = self.env['res.users'].sudo().browse(SUPERUSER_ID).tz
					timezone = pytz.timezone(tz)
					f_date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
					f_date = f_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)
					f_date = datetime.strftime(f_date, '%Y-%m-%d %H:%M:%S')

					value = f_date
				else:
					if obj.sudo().read([field_name])[0][field_name]:
						try:
							value1 = obj.sudo().read([field_name])[0][field_name]
							if type(value1) in [float, int]:
								value = "{:,}".format(value1)
							else:
								value = str(value1)
						except ValueError:
							value=str(obj.sudo().read([field_name])[0][field_name].encode('utf-8'))
					else:
						value = ''
				try:
					text = text.replace(field,value)
				except ValueError:
					text = text.replace(field,value.decode('utf-8'))
			else:
				text = text.replace(field,'...............')
		return text

	# Many2one field's field
	def _set_many2one_pattern(self, text, ids):
		field_names = self.env[ self.model_id.model ].sudo().fields_get()
		match = re.findall(r'{[\w.-]+:[\w.-]+}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)
		
		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[0]
			field_name2 = related_fields[1]
			if field_name in field_names:
				value = ''
				if str(field_names[field_name]['type'])=='many2one':
					sub_obj_id = obj.sudo().read([field_name])[0][field_name][0]
					sub_obj = self.env[ field_names[field_name]['relation'] ].sudo().search([('id','=',sub_obj_id)])
					value = sub_obj.sudo().read([field_name2])[0][field_name2] if sub_obj.sudo().read([field_name2])[0][field_name2] else u'Хоосон'	
					if type(value) in [float, int]:
						value = "{:,}".format(value)
					else:
						value = value
				text = text.replace(pttrn_name,value)
			else:
				text = text.replace(pttrn_name,'...............')
		return text

	# One2many field's data into table
	def _set_one2many_pattern(self, text, ids):
		field_names = self.env[ self.model_id.model ].sudo().fields_get()
		match = re.findall(r'{[\w.-]+:{[\w,]+}}', text)
		obj = self.env[ self.model_id.model ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)
		
		for patern_name in array_match:
			related_fields = patern_name.split(':')
			field_name = related_fields[0]
			one2many_fields = related_fields[1].split(',')
			pttrn_name = '{'+field_name+':{'+related_fields[1]+'}}'
			if field_name in field_names:
				value = ''
				if str(field_names[field_name]['type'])=='one2many':
					o2m_ids = obj.sudo().read([field_name])[0][field_name]
					o2m_field_names = self.env[ field_names[field_name]['relation'] ].sudo().fields_get()
					
					data = False

					table_lines = '<table style="border:1px solid #dddddd;border-collapse: collapse;width:100%;font-size: 11pt;">'
					# Table ийн толгой зурах
					table_header = ''
					for fn in one2many_fields:
						table_header += '<th style="border:1px solid #dddddd;text-align: center;">'+o2m_field_names[fn]['string']+'</th>'
					table_lines += table_header

					for o2m_id in o2m_ids:
						row = '<tr style="border: 1px solid #dddddd;padding:1px">'
						o2m_obj = self.env[ field_names[field_name]['relation'] ].sudo().search([('id','=',o2m_id)])
						data = o2m_obj.sudo().read(one2many_fields)[0]

						for fn in one2many_fields:
							td = '<td style="border: 1px solid #dddddd;padding:1px">'
							if type(data[fn]) is tuple:
								td += data[fn][1]
							elif type(data[fn]) in [float, int]:
								td += "{:,}".format(data[fn])
							else:
								td += unicode(data[fn])
							row += td + '</td>'
						table_lines += row + '</tr>'
					table_lines += '</table>'

				text = text.replace(pttrn_name, table_lines)
			else:
				text = text.replace(pttrn_name,'...............')
		return text

	def encode_for_xml(self, unicode_data, encoding='ascii'):
		try:
			return unicode_data.encode(encoding, 'xmlcharrefreplace')
		except ValueError:
			return self._xmlcharref_encode(unicode_data, encoding)

	def _xmlcharref_encode(self, unicode_data, encoding):
		chars = []
		for char in unicode_data:
			try:
				chars.append(char.encode(encoding, 'strict'))
			except UnicodeError:
				chars.append('&#%i;' % ord(char))
		return ''.join(chars)
