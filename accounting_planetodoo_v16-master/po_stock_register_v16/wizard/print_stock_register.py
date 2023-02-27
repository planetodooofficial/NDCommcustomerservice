from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import csv
import xlwt
from io import BytesIO
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta

class StockRegister(models.TransientModel):
    _name = "stock.reg.wiz"
    _description = "Stock Register"

    from_date = fields.Date()
    to_date = fields.Date()
    location_id = fields.Many2one('stock.location')

    def print_stock_register(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Stock register')
        fp = BytesIO()

        main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1, vert centre, horiz center; borders: bottom thick, top thick, left thick, right thick')
        header_style = xlwt.easyxf(
            'font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin')
        base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')

        worksheet.write_merge(0, 1, 0, 20,("%s (%s - %s)" %self.location_id.name,self.from_date,self.to_date), main_style)

        worksheet.col(0).width = 8000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000

        row_index = 2
        header_fields = ['Product','Opening Qty','Purchased Qty','Sale Qty','Balance Qty']
        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        products = self.env['product.product'].sudo().search([('detailed_type','=','product')])
        for product in products:
            in_qty = out_qty = opening_qty = closing_qty = 0.0
            move_lines = self.env['stock.move.line'].sudo().search([('date','<=',self.from_date),('date','>=',self.to_date),('state','=','done'),
                                                                     ('product_id','=',product.id),
                                                                 '|',('location_id','=',self.location_id.id),('location_dest_id','=',self.location_id.id)])
            for line in move_lines:
                if self.location_id == line.location_id:
                    out_qty += line.qty_done
                    if line.date == self.from_date:
                        opening_qty -= line.qty_done
                    if line.date == self.to_date:
                        closing_qty -= line.qty_done

                elif self.location_id == line.location_dest_id:
                    in_qty +=line.qty_done
                    if line.date == self.from_date:
                        opening_qty += line.qty_done
                    if line.date == self.to_date:
                        opening_qty += line.qty_done
