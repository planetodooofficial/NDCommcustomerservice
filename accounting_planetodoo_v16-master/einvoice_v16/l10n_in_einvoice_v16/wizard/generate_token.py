# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class L10nInEInvoiceServiceSetupWizard(models.TransientModel):
    _name = "l10n.in.einvoice.service.setup.wizard"

    partner_id = fields.Many2one('res.partner', 'GSTN Partner',
        domain=lambda self: ['|',('id', 'in', self.env['account.journal'].search([]).mapped('l10n_in_gstin_partner_id.id')),
        ('id','=', self.env.company.partner_id.id)])
    gstn_username = fields.Char('Username')
    gstn_password = fields.Char('Password')
    save_password = fields.Boolean('Save Password')

    def register_service(self):
        service = self.env['l10n.in.einvoice.service']
        service_id = service.search([('partner_id','=',self.partner_id.id),
            ('gstin','=', self.partner_id.vat),
            ('gstn_username','=', self.gstn_username)])
        if not service_id:
            service_id = service.create({
                'partner_id': self.partner_id.id,
                'gstn_username': self.gstn_username,
                'gstin': self.partner_id.vat,
            })
        if self.save_password:
                service_id.gstn_password = self.gstn_password
        service_id.setup(self.gstn_password)
