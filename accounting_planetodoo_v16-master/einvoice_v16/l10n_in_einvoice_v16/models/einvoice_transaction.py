# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import re
import html2text
import logging
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nInInvoiceTransaction(models.Model):
    _name = 'l10n.in.einvoice.transaction'
    _description = 'India eInvoice Transaction'
    _rec_name ="ack_no"

    move_id = fields.Many2one('account.move', 'Invoice')
    irn = fields.Char('IRN', help='Invoice Registration Number (IRN)', compute="_get_data_from_response_json")
    ack_no = fields.Char('Ack No', compute="_get_data_from_response_json")
    ack_date = fields.Char('Ack Date', compute="_get_data_from_response_json")
    qr_code_data = fields.Char('QR Code', compute="_get_data_from_response_json")
    generation_datatime = fields.Datetime("Generation time", compute="_get_data_from_response_json")
    status = fields.Selection([('submitted', 'Submitted'),
                                ('cancel', 'Cancelled'),
                                ], string='Status')
    generate_request_json = fields.Text(
        compute='_compute_generate_request_json', string='Request', store=True)
    response_json = fields.Text('Response', default='{}')
    get_irn_by_details_request_json = fields.Text(
        compute='_compute_get_irn_by_details_request_json', string='Request', store=True)

    cancellation_datatime = fields.Datetime("Cancellation time")
    cancel_reason = fields.Selection([('1', 'Duplicate'), ('2', 'Data Entry Mistake')],
            string='Cancel reason',)
    cancel_remarks = fields.Char('Cancel Remarks')
    cancel_request_json = fields.Text(
        compute='_compute_cancel_request_json', string='Cancel request', store=True)
    cancel_response_json = fields.Text('Cancel response')

    @api.depends('response_json')
    def _get_data_from_response_json(self):
        for transaction in self:
            response_json_dir = json.loads(transaction.response_json)
            transaction.irn = response_json_dir.get('Irn')
            transaction.ack_no = response_json_dir.get('AckNo')
            transaction.ack_date = response_json_dir.get('AckDt')
            transaction.qr_code_data = response_json_dir.get('SignedQRCode')
            if response_json_dir.get('AckDt'):
                transaction.generation_datatime = fields.Datetime.to_datetime(response_json_dir.get('AckDt')) - timedelta(hours=5, minutes=30, seconds=00)
            else:
                transaction.generation_datatime = False

    @api.model
    def _get_supply_type(self, move):
        supply_type = 'B2B'
        if move.l10n_in_gst_treatment in ('overseas','special_economic_zone') and self.env.ref('l10n_in.tax_report_line_igst') in move.mapped('line_ids.tax_tag_ids.tax_report_line_ids'):
            if move.l10n_in_gst_treatment == 'overseas':
                supply_type = "EXPWP"
            if move.l10n_in_gst_treatment == 'special_economic_zone':
                supply_type = 'SEZWP'
        elif move.l10n_in_gst_treatment in ('overseas','special_economic_zone'):
            if move.l10n_in_gst_treatment == 'overseas':
                supply_type = "EXPWOP"
            if move.l10n_in_gst_treatment == 'special_economic_zone':
                supply_type = 'SEZWOP'
        elif move.l10n_in_gst_treatment in ('deemed_export'):
            supply_type = 'DEXP'
        return supply_type

    def _extract_digits(self, number):
        if number:
            matches = re.findall(r'\d+', number)
            return "".join(matches)
        return False

    def get_credit_day(self, move):
        if move:
            payment_term_line_id = move.line_ids.filtered(lambda t: t.account_id.account_type == 'asset_receivable')
            line = move.line_ids.search([('account_id', '=', account_id), ('move_id', '=', move.id)], order="date_maturity desc", limit=1)
            credit_day = line.date_maturity - move.date
            return credit_day.days
        return False

    def get_round_off_value(self, move):
        # for line in move.invoice_line_ids:
            # if line.is_rounding_line == True:
            # return line.price_subtotal
        return False

    def get_amount_in_INR(self, amount):
        if self.move_id.currency_id and self.move_id.company_id.currency_id != self.move_id.currency_id:
            return self.move_id.currency_id._convert(amount, self.move_id.company_id.currency_id, self.move_id.company_id, self.move_id.date)
        return amount

    def get_gst_rate(self, taxes_rate, line_id):
        taxes = ('SGST', 'CGST', 'IGST')
        gst_rate = float()
        for tax in taxes:
            gst_rate = gst_rate + taxes_rate.get(line_id, {}).get(tax, 0.0)
        return gst_rate

    @api.depends('move_id')
    def _compute_generate_request_json(self):
        for transaction in self.filtered(lambda t: t.move_id.state == 'posted'):
            values = {
                'invoice': transaction
            }
            ####################################################################################
            generate_request_json = self.env['ir.ui.view']._render_template("l10n_in_einvoice_v16.l10n_in_invoice_request_payload_json", values)
            generate_request_json = generate_request_json.encode().decode("utf-8")
            generate_request_json = generate_request_json.replace('&quot;', '\\"')
            # raise UserError(generate_request_json)
            #
            json_dumps = json.dumps(safe_eval(generate_request_json))
            json_dumps = html2text.html2text(json_dumps)
            json_dumps = json_dumps.replace("\n", "")
            transaction.generate_request_json = json_dumps

    @api.depends('irn', 'cancel_reason', 'cancel_remarks')
    def _compute_cancel_request_json(self):
        for transaction in self.filtered(lambda t: t.move_id.state == 'cancel'):
            transaction.cancel_request_json = json.dumps({
                "Irn": transaction.irn,
                "CnlRsn": transaction.cancel_reason,
                "CnlRem": transaction.cancel_remarks,
            })

    @api.depends('move_id','move_id.name', 'move_id.invoice_date')
    def _compute_get_irn_by_details_request_json(self):
        for transaction in self:
            move = transaction.move_id
            json_dumps = json.dumps({
                "doc_type": move.move_type == "out_refund" and "CRN" or move.move_type == "in_refund" and "DBN" or "INV",
                "doc_num": move.name,
                "doc_date": move.invoice_date and move.invoice_date.strftime('%d/%m/%Y') or False,
                })
            transaction.get_irn_by_details_request_json = json_dumps

    @api.model
    def fix_base64(self, base64_string):
        # add missed = padding
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        return base64_string

    def _process(self):
        self.ensure_one()
        service = self.env['l10n.in.einvoice.service'].get_service(self.move_id.journal_id.l10n_in_gstin_partner_id or self.move_id.company_id.partner_id)
        response = service.generate(transaction_id=self)

        response_data = response.get('data')
        _logger.info('Einvoice Json Response: %s', response_data)
        if response_data and response_data.get('Irn') and response_data.get('SignedQRCode'):
            vals = {
                'response_json': json.dumps(response_data),
                'status': 'submitted',
            }
            self.sudo().write(vals)

    def submit_invoice(self):
        for transaction in self:
            transaction._process()

    def _process_get_irn_by_details(self):
        self.ensure_one()
        service = self.env['l10n.in.einvoice.service'].get_service(self.move_id.journal_id.l10n_in_gstin_partner_id or self.move_id.company_id.partner_id)
        response = service.get_irn_by_details(transaction_id=self)
        response_data = response.get('data')
        if response_data and response_data.get('Irn') and response_data.get('SignedQRCode'):
            vals = {
                'response_json': json.dumps(response_data),
                'status': 'submitted',
            }
            self.sudo().write(vals)

    def get_irn_by_details(self):
        for transaction in self:
            transaction._process_get_irn_by_details()

    def _process_cancel(self):
        self.ensure_one()
        service = self.env['l10n.in.einvoice.service'].get_service(self.move_id.journal_id.l10n_in_gstin_partner_id or self.move_id.company_id.partner_id)
        response = service.cancel(transaction_id=self)
        vals = {
            'cancel_response_json': str(response)
        }
        response_data = response.get('data', False)
        if response_data and response_data.get('CancelDate', False):
            cancellation_datatime = fields.Datetime.to_datetime(response_data.get('CancelDate')) - timedelta(hours=5, minutes=30, seconds=00)
            vals.update({
                'cancellation_datatime': cancellation_datatime,
                'status': 'cancel'
            })
        self.sudo().write(vals)
        self.env.cr.commit()

    def cancel_invoice(self, cancel_reason, cancel_remarks):
        self.sudo().write({
            'cancel_reason': cancel_reason,
            'cancel_remarks': cancel_remarks
        })
        for transaction in self:
            transaction._process_cancel()

    def preview_qrcode(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'nrew',
            'url': "/report/barcode/?type=%s&value=%s&width=%s&height=%s&quiet=%s" % ('QR', self.qr_code_data, 200, 200, 0),
        }
