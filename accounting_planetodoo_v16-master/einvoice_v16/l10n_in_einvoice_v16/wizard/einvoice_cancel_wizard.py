# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class L10nInEInvoiceCancelWizard(models.TransientModel):
    _name = "l10n_in.einvoice.cancel.wizard"

    @api.model
    def default_get(self, fields):
        result = super(L10nInEInvoiceCancelWizard, self).default_get(fields)
        active_model = self._context.get('active_model')
        
        if active_model != 'account.move':
            raise UserError(_('You can only apply this action from an Invoices.'))

        active_ids = self._context.get('active_ids') or [self._context.get('active_id')]
        active_move_ids = self.env[active_model].browse(active_ids)
        not_have_irn_moves = active_move_ids.filtered(lambda m: not m.l10n_in_transaction_id)
        
        if not_have_irn_moves:
            #Can we do a message like like below, instead os using join
            invoices = [(m.name, m.id) for m in not_have_irn_moves]
            raise UserError(_("Invoies %s are not subited to GSTN Portal. No need to cancel them!") % (invoices))
            #raise UserError(_("Moves %s not have IRN so can't cancel it."%(",".join("%s (%s)"%())))
        
        result['move_ids'] = active_ids
        return result

    # We need 1 and 2 as key as same has to submit to request (https://einv-apisandbox.nic.in/master-codes-list.html)
    cancel_reason = fields.Selection([('1','Duplicate'),('2','Data Entry Mistake')],
        string='Cancel reason', default="2")
    cancel_remarks = fields.Char('Cancel Remarks')
    move_ids = fields.Many2many('account.move', string="Move ids")

    def cancel_einvoice(self):
        for move in self.move_ids:
            move.l10n_in_transaction_id.cancel_invoice(self.cancel_reason, self.cancel_remarks)
