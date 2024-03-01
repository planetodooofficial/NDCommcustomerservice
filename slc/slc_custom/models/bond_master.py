from odoo import models, api, fields, _


class BondMaster(models.Model):
    _name = 'bond.master'
    _rec_name = 'bond_number'

    bond_number = fields.Integer(string='Bond Number', required=True)
    bond_type = fields.Selection([('pd', 'PD'), ('wh', 'WH')], string='Bond Type')
    issue_date = fields.Date(string='Issue Date')
    validity_date = fields.Date(string='Validity Date')
    value = fields.Char(string='Value')
    customs_station = fields.Many2one('customs.station', string='Customer Station')
    is_edit = fields.Boolean(default=False)

    def edit_only_button(self):
        self.is_edit = True

    def readonly_button(self):
        self.is_edit = False


class CommisionerateMaster(models.Model):
    _name = 'commisionerate.master'
    _rec_name = 'commisionerate_name'

    commisionerate_name = fields.Char(string='Commisionerate Name', required=True)
    commisionerate_address = fields.Char(string='Commisionerate Address')
    commisionerate_state = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                                           domain="[('country_id', '=', country)]")
    country = fields.Many2one('res.country', string='Country', default=lambda self: self._default_country())

    def _default_country(self):
        return self.env['res.country'].search([('name', '=', 'India')], limit=1).id


class CustomsStation(models.Model):
    _name = 'customs.station'
    _rec_name = 'custom_station_name'

    custom_station_name = fields.Char(string='Custom Station Name', required=True)
    commisionerate_station = fields.Many2one('commisionerate.master', string='Commisionerate Name')


class EximSubCategory(models.Model):
    _name = 'exim.sub.category'
    _rec_name = 'sub_category_name'

    category_name = fields.Selection([('moowr', 'MOOWR'), ('import', 'Import'), ('export', 'Export')])
    sub_category_name = fields.Char(string='Sub Category Name', required=True)


class HsnMaster(models.Model):
    _name = 'hsn.master'
    _rec_name = 'hsn_number'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    hsn_country = fields.Many2one('res.country', string='HSN Country', default=lambda self: self._default_country(),
                                  tracking=True)
    hsn_number = fields.Char(string='HSN Number', size=8, required=True, tracking=True)
    digit_heading_4 = fields.Char(string='4 Digit Heading', tracking=True)
    digit_heading_6 = fields.Char(string='6 Digit Heading', tracking=True)
    digit_heading_8 = fields.Char(string='8 Digit Heading', tracking=True)
    ccr_notes = fields.Char(string='CCR Notes', tracking=True)
    hsn_remarks = fields.Char(string='Remarks', tracking=True)
    hsn_last_update_date = fields.Date(string='HSN Last Update Date', tracking=True)

    _sql_constraints = [
        ('hsn_number_uniq', 'UNIQUE (hsn_number)', 'You must have unique HSN no!')]

    def _default_country(self):
        return self.env['res.country'].search([('name', '=', 'India')], limit=1).id

