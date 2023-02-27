from odoo import api, fields, models
import io, base64
from tempfile import TemporaryFile
import pandas as pd
import numpy as np
import datetime
from stdnum.exceptions import ValidationError
import json

class UploadReconciliation(models.TransientModel):
    _name = "upload.reconciliation"
    _description = "Upload Reconciliation"

    file_data = fields.Binary(string='Upload File', required=True)


    def upload_file_data(self):
        df = self.convert_to_df()

        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        active = self.env[model].browse(active_ids)
        invoiceObjs = active.fetchSupplierInvoices()

        global found_invoice_form_p
        found_invoice_form_p = self.env['account.move']
        missing_invoice = lambda x: self.env['account.move'].search([('ref', '=', x)]).id
        # missing_in_odoo = [rec for rec in df['file_invoice'] if not missing_invoice(rec)]
        no_of_row = len(df.index)
        print('no_of_row',no_of_row)
        missing_in_odoo = [row for index, row in df.iterrows() if not missing_invoice(row['file_invoice'])]


        missing_partner = lambda x: self.env['res.partner'].search([('vat', '=',str(x))]).id if x else None
        # missing_partner_odoo = [rec['file_invoice'] for rec in df if not missing_partner(rec[['gst_no']])]
        missing_partner_odoo = [row for index, row in df.iterrows() if not missing_partner(str(row[['gst_no']]))]
        print('missing_in_odoo',missing_in_odoo)
        print('@@@@missing_partner_odoo',missing_partner_odoo)
        # final_missing_in_odoo_from_file = set(missing_in_odoo.to_list()+missing_partner_odoo.to_list()) #[2101011004,561]

        def search_partialmatched_invoice(data_fram_row):
            print('data_fram_row', data_fram_row)
            vat = data_fram_row['gst_no']
            ref = data_fram_row['file_invoice']
            amt = data_fram_row['inv_value']
            journal_id = active.journal_id.id
            global found_invoice_form_p
            partialmatched_invoice = self.env['account.move'].search([('journal_id','=',journal_id),('amount_total', '!=', float(amt)),('partner_id.vat', '=', vat), ('ref', '=', ref)])
            print('partialmatched_invoice', partialmatched_invoice)
            if partialmatched_invoice:
                found_invoice_form_p |= partialmatched_invoice
                #Partial Matched
                file_date = datetime.datetime.strptime(str(data_fram_row['file_date']),'%d-%m-%Y').strftime('%Y-%m-%d')
                vals = {
                    'linked_date': partialmatched_invoice.date,
                    'linked_invoice_id': partialmatched_invoice.id,
                    'linked_vendor_id': partialmatched_invoice.partner_id.id,
                    'file_date': file_date,
                    'file_invoice': data_fram_row['file_invoice'],
                    'file_vendor':data_fram_row['file_vendor'],
                    'file_amt': data_fram_row['inv_value'],
                    'inv_amt': partialmatched_invoice.amount_total,
                    'diff_amt': partialmatched_invoice.amount_total -data_fram_row['inv_value'] ,
                    'reconciliation_id': active.id
                }
                self.env['reconciliation.tool.partial.line'].create(vals)
            return True

        def search_reconciled_invoice(data_fram_row):
            global found_invoice_form_p
            vat = data_fram_row['gst_no']
            ref = data_fram_row['file_invoice']
            amt = data_fram_row['inv_value']
            journal_id = active.journal_id.id
            reconciled_invoice = self.env['account.move'].search([('journal_id','=',journal_id),('partner_id.vat', '=', vat), ('ref', '=', ref), ('amount_total','=', float(amt))])
            print('reconciled_invoice', reconciled_invoice)
            if reconciled_invoice:
                reconciled_invoice.write({'reconciled':True})
                found_invoice_form_p |= reconciled_invoice
            else:
                if reconciled_invoice.id not in found_invoice_form_p.ids:
                    #Missing in Odoo
                    file_date = datetime.datetime.strptime(str(data_fram_row['file_date']), '%d-%m-%Y').strftime('%Y-%m-%d')
                    vals= {
                        'file_date':file_date,
                        'file_invoice':data_fram_row['file_invoice'],
                        'file_vendor':data_fram_row['file_vendor'],
                        'file_amt':data_fram_row['inv_value'],
                        'reconciliation_id':active.id
                    }
                    self.env['reconciliation.tool.missing.odoo.line'].create(vals)
            return True

        df.apply(search_partialmatched_invoice,axis=1)
        df.apply(search_reconciled_invoice,axis=1)

        # INV Missing in File
        missing_in_file_inv = invoiceObjs - found_invoice_form_p
        active.missing_in_file_invoice_lines = [(6, 0, missing_in_file_inv.ids)]

        active.invoice_lines = [(6, 0, invoiceObjs.ids)]
        return True


    # def search_field(self, tb, col, val):
    #     return tb.filtered(lambda x: str(x.col_value) == str(val).strip() and x.col_name == col).id

    def convert_to_df(self):
        csv_data = self.file_data
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        first_row = ['gst_no', 'file_vendor', 'file_invoice', 'inv_type', 'file_date', 'inv_value', 'place_of_supply',
                     'rev_cha', 'rat','taxable_value', 'integrated_tax', 'central_tax', 'ut_tax', 'cess', 'gstr1_status',
                     'gstr1_date', 'gstr1_period', 'gstr3b_status', 'amendment_any', 'tax_period_amended',
                     'cancellation_date', 'source', 'irn', 'irn_date']
        df = pd.read_excel(file_obj,header=None,names=first_row).fillna(np.nan)
        df.dropna(subset=['file_invoice'], inplace=True)
        df.drop(df[df['file_invoice'].str.contains('-Total')].index, inplace=True)
        return df