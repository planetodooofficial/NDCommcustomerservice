from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
from odoo.exceptions import ValidationError
import datetime
from datetime import datetime
from odoo import models, api, fields, _

class CostDimension(models.Model):
    _name = "cost.dimension"
    _rec_name = 'name'

    name = fields.Char(string= 'Cost Record')
    be_no = fields.Char(string= 'BE No.')
    cb_job_number = fields.Char(string= 'CB Job number')
    hawb_hbl_no = fields.Char(string= 'HAWB/HBL No')
    hawb_hbl_date = fields.Char(string= 'HAWB/HBL Date')
    gross_weight = fields.Char(string= 'Gross Weight (kg)')
    container_count = fields.Char(string= 'Container Count')
    total_duty = fields.Char(string= 'Total Duty')
    linked_cb_partner = fields.Char(string= 'Linked CB partner')
    business_tags = fields.Char(string= 'Business tags')
    be_date = fields.Char(string= 'BE Date')
    client_ref_number = fields.Char(string= 'Client Ref Number')
    mawb_mbl_no = fields.Char(string= 'MAWB/MBL No.')
    mawb_mbl_date = fields.Char(string= 'MAWB/MBL Date')
    packages = fields.Char(string= 'Packages')
    assessable_value = fields.Char(string= 'Assessable Value')
    boe_description = fields.Char(string= 'BOE description')
    linked_ff_partner = fields.Char(string= 'Linked FF partner')
    sales_team = fields.Char(string= 'Sales team')
    source_doc = fields.Char(string= 'Source doc')
    customs_station = fields.Char(string= 'Customs Station')
    mode = fields.Char(string= 'Mode')
    linked_tpt_partner = fields.Char(string= 'Linked TPT partner')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Validated')])

    agency = fields.Char(string='Agency')
    handling = fields.Char(string='Handling')
    documentation = fields.Char(string='Documentation')
    airport_authority = fields.Char(string='Airport Authority')
    airport_demurrage = fields.Char(string='Airport Demurrage')
    cfs_h_t = fields.Char(string='CFS H&T')
    cfs_ground_rent = fields.Char(string='CFS Ground Rent')
    airline_do = fields.Char(string='Airline DO')
    shipping_line_do = fields.Char(string='Shipping line DO')
    others_cb = fields.Char(string='Others CB')
    cb_gst = fields.Char(string='CB GST')
    cb_invoice_total = fields.Char(string='CB Invoice Total')
    total_cb_ff_tpt = fields.Char(string='Total (CB+FF+TPT)')
    air_freight = fields.Char(string='Air Freight')
    sea_freight = fields.Char(string='Sea Freight')
    ex_works = fields.Char(string='ExWorks')
    others_ff = fields.Char(string='Others FF')
    ff_gst = fields.Char(string='FF GST')
    ff_invoice_total = fields.Char(string='FF Invoice Total')
    transportation = fields.Char(string='Transportation')
    transport_detention = fields.Char(string='Transport detention')
    others_tpt = fields.Char(string='Others TPT')
    tpt_gst = fields.Char(string='TPT GST')
    tpt_invoice_total = fields.Char(string='TPT Invoice Total')

    custom_broker_ids = fields.One2many('customs.broker', 'custom_broker_id')
    freight_forwarder_ids = fields.One2many('freight.forwarder', 'freight_forwarder_id')
    transporter_ids = fields.One2many('transporter.tab', 'transporter_id')
    is_state = fields.Boolean(default=False)

    def button_validate(self):
        self.state = 'confirm'
        self.is_state = True

    def cancel_button(self):
        self.state = 'draft'

class CustomsBroker(models.Model):
    _name = "customs.broker"

    custom_broker_id = fields.Many2one('cost.dimension')

    invoice_number = fields.Integer(string='Invoice Number')
    agency = fields.Integer(string='Agency')
    handling = fields.Integer(string='Handling')
    documentation = fields.Integer(string='Documentation')
    airport_authority = fields.Integer(string='Airport Authority')
    airport_demurrage = fields.Integer(string='Airport Demurrage')
    cfs_h_t = fields.Integer(string='CFS H&T')
    cfs_ground_rent = fields.Integer(string='CFS Ground Rent')
    airline_do = fields.Integer(string='Airline DO')
    shipping_line_do = fields.Integer(string='Shipping line DO')
    others_cb = fields.Integer(string='Others CB')
    cb_total = fields.Integer(string='CB Total')
    cb_gst = fields.Integer(string='CB GST')
    cb_invoice_total = fields.Integer(string='CB Invoice Total')


class FreightForwarder(models.Model):
    _name = 'freight.forwarder'

    freight_forwarder_id = fields.Many2one('cost.dimension')

    invoice_number = fields.Char(string='Air Freight')
    sea_freight = fields.Char(string='Sea Freight')
    ex_works = fields.Char(string='ExWorks')
    others_ff = fields.Char(string='Others FF')
    ff_total = fields.Char(string='FF TOTAL ')
    ff_gst = fields.Char(string='FF GST')
    ff_invoice_total = fields.Char(string='FF Invoice Total')


class Transporter(models.Model):
    _name = "transporter.tab"

    transporter_id = fields.Many2one('cost.dimension')

    invoice_number = fields.Char(string='Invoice Number')
    transportation = fields.Char(string='Transportation')
    transport_detention = fields.Char(string='Transport detention')
    others_tpt = fields.Char(string='Others TPT')
    tpt_total = fields.Char(string='TPT TOTAL')
    tpt_gst = fields.Char(string='TPT GST')
    tpt_invoice_total = fields.Char(string='TPT Invoice Total')




