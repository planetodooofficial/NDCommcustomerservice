from odoo import api, fields, models


class InheritAccountJournal(models.Model):
    _inherit = 'account.journal'

    cust_gst = fields.Char('GST Number', related='l10n_in_gstin_partner_id.vat',readonly=True)
