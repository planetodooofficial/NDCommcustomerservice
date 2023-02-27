from odoo import models, api, fields, _
from odoo import fields as odoo_fields, http, tools
from odoo.http import Controller, route, request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError
import base64


class InheritContracts(models.Model):
    _inherit = ['res.partner']

    is_approved = fields.Boolean('Approved', default=False, tracking=True)
    cancelled_cheque = fields.Binary('Cancelled Cheque', attachment=True, copy=False)
    pan_no = fields.Char('PAN NO')
    pan_card = fields.Binary('PAN Card', attachment=True, copy=False)
    gst_doc = fields.Binary('GST', attachment=True, copy=False)
    iec_number = fields.Char('IEC Number')
    cin = fields.Char('CIN')
    gst_doc_name = fields.Char("")
    pan_file_name = fields.Char("")
    check_file_name = fields.Char("")
    entity_type = fields.Selection(
        [('select', 'select...'), ('Sole Proprietorships', 'Sole Proprietorships'), ('Partnership', 'Partnership'),
         ('LLP', 'LLP'),
         ('PVT LTD', 'PVT LTD'), ('Public LTD', 'Public LTD')])
    vat = fields.Char(required=False)
    is_msme = fields.Selection([('yes', 'YES'), ('no', 'NO')], string='MSME Registered')
    msme_doc = fields.Binary('MSME CERTIFICATE', attachment=True, copy=False)
    msme_doc_name = fields.Char()

    # entity = fields.Char('Entity Type')

    # country_id = fields.Many2one('res.country', 'Country', readonly=True)

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        return country

    country_id = fields.Many2one('res.country', string='Country', default=_get_default_country)

    @property
    def download_pan(self):
        return "/web/content/?model=res.partner&id=" + str(self.id) + \
               "&filename_field=pan_file_name&field=pan_card&download=true&name=" + 'test'

    @property
    def download_cheque(self):
        return "/web/content/?model=res.partner&id=" + str(self.id) + \
               "&filename_field=check_file_name&field=cancelled_cheque&download=true&name=" + 'test'

    @property
    def download_gst(self):
        return "/web/content/?model=res.partner&id=" + str(self.id) + \
               "&filename_field=gst_doc_name&field=gst_doc&download=true&name=" + 'test'

    @property
    def download_msme(self):
        return "/web/content/?model=res.partner&id=" + str(self.id) + \
               "&filename_field=msme_file_name&field=msme_doc&download=true&name=" + 'test'