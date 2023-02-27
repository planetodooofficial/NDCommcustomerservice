from odoo import api, fields, models
import io, base64
from tempfile import TemporaryFile
import pandas as pd
import numpy as np
import datetime
from stdnum.exceptions import ValidationError
import json

gstr_keys = {'b2b':{'type':'inv','num':'inum','date':'idt','val':'val'},
             'exp':{'type':'inv','num':'inum','date':'idt','val':'val'},
             'b2bur':{'type':'inv','num':'inum','date':'idt','val':'val'},
             'imp_s':{'num':'inum','date':'idt','val':'val'},
             'imp_g':{'num':'boe_num','date':'boe_dt','val':'boe_val'},
             'cdnr':{'type':'nt','num':'nt_num','date':'nt_dt','val':'val'},
             'cdn':{'type':'nt','num':'nt_num','date':'nt_dt','val':'val'},
             'cdnur':{'num':'nt_num','date':'nt_dt','val':'val'},
             'tcs':{'num':'inum','date':'idt','val':'val'}}

class UploadReconciliation(models.TransientModel):
    _name = "upload.gstr.reco"
    _description = "Upload Reconciliation"

    file_data = fields.Binary("File")

    def upload_file_data(self):
        json_file = base64.decodebytes(self.file_data)
        json_data = json.loads(json_file)
        active_id = self.env.context.get('active_id')
        reco_id = self.env['gstr.reconciliation'].sudo().search([('id', '=', active_id)])
        company = self.env.company
        domain = [('invoice_date', '>=', reco_id.from_period_id.date_start),
                  ('invoice_date', '<=', reco_id.to_period_id.date_stop),
                  ('journal_id', '=', reco_id.journal_id.id),('company_id','=',company.id),('state','=','posted'),
                  ('reconciled','=',False)]
        moves = self.env['account.move'].sudo().search(domain)
        if reco_id.reco_type == 'gstr1':
            self.sync_gstr_data(json_data,'b2b',reco_id,moves)
        if reco_id.reco_type == 'gstr2':
            if json_data.get('b2b'):
                self.sync_gstr_data(json_data,'b2b',reco_id,moves)
            if json_data.get('b2bur'):
                self.sync_gstr_data(json_data,'b2bur',reco_id,moves)
            if json_data.get('cdnr'):
                self.sync_gstr_data(json_data,'cdnr',reco_id,moves)
            if json_data.get('cdnr'):
                self.sync_gstr_data(json_data,'cdnr',reco_id,moves)
            if json_data.get('exp'):
                self.sync_gstr_data(json_data,'exp',reco_id,moves)
            # if json_data.get('cdnur'):
            #         self.sync_gstr_data(json_data, 'cdnur', reco_id,moves)
            # if json_data.get('imp_s'):
            #     self.sync_gstr_data(json_data,'imp_s',reco_id,moves)
            # if json_data.get('imp_g'):
            #     self.sync_gstr_data(json_data,'imp_g',reco_id,moves)
            # if json_data.get('tcs'):
            #     self.sync_gstr_data(json_data,'tcs',reco_id,moves)

    def sync_gstr_data(self, json_data,type,reco_id,moves):
        json_moves = json_data[type]
        keys = gstr_keys[type]
        reconciled_moves = []
        odoo_missing_moves = []
        file_missing_moves = []
        for rec in json_moves:
            if keys.get('type'):
                invoices = rec.get(keys.get('type'))
            else:
                invoices = rec

            if invoices:
                for inv in invoices:
                    file_inum = inv.get(keys.get('num'))
                    file_idate = datetime.datetime.strptime(str(inv.get(keys.get('date'))), '%d-%m-%Y').strftime('%Y-%m-%d')
                    file_amount = float(inv.get(keys.get('val')))
                    partner_id = self.env['res.partner'].sudo().search([('vat', '=', inv.get(keys.get('ctin')))], limit=1)
                    reconciled_move = moves.sudo().search([('name', '=', file_inum),('partner_id','=',partner_id.id),])
                    if reconciled_move:
                        moves = moves.filtered(lambda i: i.id != reconciled_move.id)
                        reconciled_moves.append((0, 0, {
                            'inv_date': reconciled_move.invoice_date,
                            'move_id': reconciled_move.id,
                            'partner_id': reconciled_move.partner_id.id,
                            'inv_amt': reconciled_move.amount_total,
                            'state': reconciled_move.state,
                            'move_type': reconciled_move.move_type,
                            'invoice_type': reconciled_move.invoice_type,
                            'currency_id': reconciled_move.currency_id.id,
                            'file_date': file_idate,
                            'file_vendor': json_data['gstin'],
                            'file_invoice':file_inum,
                            'file_amt': file_amount,
                            'gstr_reco_id': reco_id.id,
                            'diff_amt': reconciled_move.amount_total - file_amount
                        }))
                        reconciled_move.reconciled = True
                    elif not reconciled_move:
                        odoo_missing_moves.append((0, 0, {
                            'partner_id': partner_id.id,
                            'file_vendor':json_data['gstin'],
                            'file_invoice': file_inum,
                            'file_date': file_idate,
                            'file_amt': file_amount,
                            'gstr_reco_id': reco_id.id
                        }))

        for move in moves:
            file_missing_moves.append((0, 0, {
                'inv_date': move.invoice_date,
                'move_id': move.id,
                'partner_id': move.partner_id.id,
                'inv_amt': move.amount_total,
                'state': move.state,
                'move_type': move.move_type,
                'invoice_type': move.invoice_type,
                'currency_id': move.currency_id.id,
                'gstr_reco_id': reco_id.id
            }))

        if reconciled_moves:
            reco_id.reconciled_moves.unlink()
            reco_id.reconciled_moves = reconciled_moves
        if odoo_missing_moves:
            reco_id.odoo_missing_moves.unlink()
            reco_id.odoo_missing_moves = odoo_missing_moves
        if file_missing_moves:
            reco_id.file_missing_moves.unlink()
            reco_id.file_missing_moves = file_missing_moves
