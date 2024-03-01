from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
from odoo.exceptions import ValidationError
import datetime
from datetime import datetime


class BoeHeader(models.Model):
    _name = 'boe.header'

    upload_purchase_header = fields.Binary('Boe Header')

    def convert_to_df(self):
        csv_data = self.upload_purchase_header
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_payment_header(self):
        df = self.convert_to_df()
        data = df.to_dict('index')
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []
        partner_id = self.env['res.partner']
        purchase_order_id = self.env['non.moowr']
        for rec in b:
            # partner = rec.get('Customer')
            # exim_txn_category = rec.get('Category')
            # exim_txn_subcategory = rec.get('Sub Category')
            # unit_name = rec.get('Company/Unit Name')
            # mode_new = rec.get('Mode')
            # erp_job_number = rec.get('ERP Job number')
            # client_ref_number = rec.get('Client Ref Number')
            port_code = rec.get('Port Code')
            be = str(rec.get('BE No'))
            be_date = rec.get('BE Date')
            be_type = rec.get('BE Type')
            iec = rec.get('IEC')
            iec_br_code = rec.get('IEC Br code')
            status = rec.get('Status')
            gstin = rec.get('GSTIN')
            cb_code = rec.get('CB Code')
            invoice_count_new = rec.get('Invoice Count')
            item_count = rec.get('Item Count')
            container = rec.get('Container')
            pkgs = rec.get('Pkgs')
            gwt = rec.get('G.WT (KGS)')
            be_status = rec.get('BE Status')
            mode_new = rec.get('Mode')
            def_be = rec.get('DEF BE')
            kacha = rec.get('KACHA')
            sec = rec.get('SEC 48')
            reimp = rec.get('REIMP')
            adv_be = rec.get('ADV BE (Y/N/P)')
            assess = rec.get('ASSESS')
            exam = rec.get('EXAM')
            hss = rec.get('HSS')
            first_check = rec.get('FIRST CHECK')
            prov_final = rec.get('PROV/FINAL')
            country_of_origin = rec.get('COUNTRY OF ORIGIN')
            country_of_consignment = rec.get('COUNTRY OF CONSIGNMENT')
            port_of_loading = rec.get('PORT OF LOADING')
            port_of_shipment = rec.get('PORT OF SHIPMENT')
            importner_name = rec.get('IMPORTER NAME')
            importer_address = rec.get('IMPORTER ADDRESS')
            cb_name = rec.get('CB NAME')
            ad_code = rec.get('AD CODE')
            aeo = rec.get('AEO')
            ucr = rec.get('UCR')
            bcd = rec.get('BCD')
            acd = rec.get('ACD')
            sws = rec.get('SWS')
            nccd = rec.get('NCCD')
            add = rec.get('ADD')
            cvd = rec.get('CVD')
            igst = rec.get('IGST')
            g_cess = rec.get('G.CESS')
            tot_ass_val = rec.get('TOT.ASS VAL')
            sg = rec.get('SG')
            saed = rec.get('SAED')
            gsia = rec.get('GSIA')
            tta = rec.get('TTA')
            health = rec.get('HEALTH')
            total_duty = rec.get('TOTAL DUTY')
            int = rec.get('INT')
            pnlty = rec.get('PNLTY')
            fine = rec.get('FINE')
            tot_amount = rec.get('TOT. AMOUNT')
            bond_no_1 = rec.get('BOND NO 1')
            port_1 = rec.get('PORT 1')
            bond_cd_1 = rec.get('BOND CD 1')
            debt_amt_1 = rec.get('DEBT AMT 1')
            bg_amt_1 = rec.get('BG AMT 1')
            bond_no_2 = rec.get('BOND NO 2')
            port_2 = rec.get('PORT 2')
            bond_cd_2 = rec.get('BOND CD 2')
            debt_amt_2 = rec.get('DEBT AMT 2')
            bg_amt_2 = rec.get('BG AMT 2')
            sr_no_1 = rec.get('SR. NO. 1')
            challan_no_1 = rec.get('CHALLAN NO 1')
            paid_on_1 = rec.get('PAID ON 1')
            amount_rs_1 = rec.get('AMOUNT Rs. 1')
            sr_no_2 = rec.get('SR. NO. 2')
            challan_no_2 = rec.get('CHALLAN NO 2')
            paid_no_2 = rec.get('PAID ON 2')
            amount_rs_2 = rec.get('AMOUNT Rs. 2')
            wbe_no = rec.get('WBE NO.')
            date = rec.get('DATE')
            wbe_site = rec.get('WBE SITE')
            wh_code = rec.get('WH CODE')
            submission_date = rec.get('Submission Date')
            submission_time = rec.get('Submission Time')
            assessment_date = rec.get('Assessment Date')
            assessment_time = rec.get('Assessment Time')
            examination_date = rec.get('Examination Date')
            examination_time = rec.get('Examination Time')
            ooc_date = rec.get('OOC Date')
            occ_time = rec.get('OOC Time')
            occ_no = rec.get('OOC NO')

            be_number = self.env['non.moowr'].search([('be', '=', be), ('id', '!=', self.id)])

            if total_duty:
                total_duty_float = float(total_duty)

            be_date_convert = False
            if be_date:
                be_date_convert = datetime.strptime(be_date, '%d/%m/%Y')

            submission_date_convert = False
            if submission_date:
                submission_date_convert = datetime.strptime(submission_date, '%d/%m/%Y')

            assessment_date_convert = False
            if assessment_date:
                assessment_date_convert = datetime.strptime(assessment_date, '%d/%m/%Y')

            examination_date_convert = False
            if examination_date:
                examination_date_convert = datetime.strptime(examination_date, '%d/%m/%Y')

            ooc_date_convert = False
            if ooc_date:
                ooc_date_convert = datetime.strptime(ooc_date, '%d/%m/%Y')

            # if be_number:
            #     raise ValidationError('BE No already exist')

            purchase_order_details = {
                'port_code': port_code,
                'be': be,
                'be_date': be_date_convert if be_date_convert else False,
                'be_type': be_type,
                'iec': iec,
                'iec_br_code': iec_br_code,
                'status': status,
                'gstin': gstin,
                'cb_code': cb_code,
                'invoice_count_new': invoice_count_new,
                'item_count': item_count,
                'container': container,
                'pkgs': pkgs,
                'gwt': gwt,
                'be_status': be_status,
                'mode_new': mode_new,
                'def_be': def_be,
                'kacha': kacha,
                'sec': sec,
                'reimp': reimp,
                'adv_be': adv_be,
                'assess': assess,
                'exam': exam,
                'hss': hss,
                'first_check': first_check,
                'prov_final': prov_final,
                'country_of_origin': country_of_origin,
                'country_of_consignment': country_of_consignment,
                'port_of_loading': port_of_loading,
                'port_of_shipment': port_of_shipment,
                'importner_name': importner_name,
                'importer_address': importer_address,
                'cb_name': cb_name,
                'ad_code': ad_code,
                'aeo': aeo,
                'ucr': ucr,
                'bcd': bcd,
                'acd': acd,
                'sws': sws,
                'nccd': nccd,
                'add': add,
                'cvd': cvd,
                'igst': igst,
                'g_cess': g_cess,
                'tot_ass_val': tot_ass_val,
                'sg': sg,
                'saed': saed,
                'gsia': gsia,
                'tta': tta,
                'health': health,
                'total_duty': total_duty_float,
                'int': int,
                'pnlty': pnlty,
                'fine': fine,
                'tot_amount': tot_amount,
                'bond_no_1': bond_no_1,
                'port_1': port_1,
                'bond_cd_1': bond_cd_1,
                'debt_amt_1': debt_amt_1,
                'bg_amt_1': bg_amt_1,
                'bond_no_2': bond_no_2,
                'port_2': port_2,
                'bond_cd_2': bond_cd_2,
                'debt_amt_2': debt_amt_2,
                'bg_amt_2': bg_amt_2,
                'sr_no_1': sr_no_1,
                'challan_no_1': challan_no_1,
                'paid_on_1': paid_on_1,
                'amount_rs_1': amount_rs_1,
                'sr_no_2': sr_no_2,
                'challan_no_2': challan_no_2,
                'paid_no_2': paid_no_2,
                'amount_rs_2': amount_rs_2,
                'wbe_no': wbe_no,
                'date': date,
                'wbe_site': wbe_site,
                'wh_code': wh_code,
                'submission_date': submission_date_convert if submission_date_convert else False,
                'submission_time': submission_time,
                'assessment_date': assessment_date_convert if assessment_date_convert else False,
                'assessment_time': assessment_time,
                'examination_date': examination_date_convert if examination_date_convert else False,
                'examination_time': examination_time,
                'ooc_date': ooc_date_convert if ooc_date_convert else False,
                'occ_time': occ_time,
                'occ_no': occ_no,
            }
            if not be_number:
                if be:
                    purchase_order_id.create(purchase_order_details)
            else:
                raise ValidationError(f'BE No {be} already exist')

        message = _("Upload Successfull")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }



class BoePurchaseLine(models.Model):
    _name = 'boe.product.line'

    upload_purchase_order_line = fields.Binary('Boe Product Line')

    def convert_to_df(self):
        csv_data = self.upload_purchase_order_line
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_payment_order_line(self):
        df = self.convert_to_df()
        data = df.to_dict('index')
        count = len(data.keys())
        print(count)
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []
        for rec in b:
            # product = rec.get('Product')
            invsno = rec.get('INVSNO')
            itemsn = rec.get('ITEMSN')
            invoice_no_new = rec.get('INVOICE NO')
            part_code = rec.get('PART CODE')
            cth = rec.get('CTH')
            # product_id = rec.get('Product')
            ceth = rec.get('CETH')
            item_description = rec.get('ITEM DESCRIPTION')
            fs = rec.get('FS')
            pq = rec.get('PQ')
            dc = rec.get('DC')
            wc = rec.get('WC')
            aq = rec.get('AQ')
            upi = rec.get('UPI')
            coo = rec.get('COO')
            cqty = rec.get('C.QTY')
            cuqc = rec.get('C.UQC')
            sqty = rec.get('S.QTY')
            suqc = rec.get('S.UQC')
            sch = rec.get('SCH')
            stnd_pr = rec.get('STND/PR')
            rsp = rec.get('RSP')
            reimp = rec.get('REIMP')
            prov = rec.get('PROV')
            end_use = rec.get('END USE')
            prodn = rec.get('PRODN')
            cntrl = rec.get('CNTRL')
            qualfr = rec.get('QUALFR')
            contnt = rec.get('CONTNT')
            stmnt = rec.get('STMNT')
            sub_docs = rec.get('SUB DOCS')
            assess_value = rec.get('ASSESS VALUE')
            total_duty = rec.get('TOTAL DUTY')
            bcd_notn_no = rec.get('BCD NOTN NO')
            acd_notn_no = rec.get('ACD  NOTN NO')
            sws_notn_no = rec.get('SWS NOTN NO')
            sad_notn_no = rec.get('SAD NOTN NO')
            igst_notn_no = rec.get('IGST NOTN NO')
            g_cess_notn_no = rec.get('G. CESS  NOTN NO')
            add_notn_no = rec.get('ADD NOTN NO')
            cvd_notn_no = rec.get('CVD NOTN NO')
            sg_notn_no = rec.get('SG  NOTN NO')
            t_value_notn_no = rec.get('T. VALUE  NOTN NO')
            bcd_notn_sno = rec.get('BCD NOTN SNO')
            acd_notn_sno = rec.get('ACD  NOTN SNO')
            sws_notn_sno = rec.get('SWS NOTN SNO')
            sad_notn_sno = rec.get('SAD NOTN SNO')
            igst_notn_sno = rec.get('IGST NOTN SNO')
            g_cess_notn_sno = rec.get('G. CESS  NOTN SNO')
            add_notn_sno = rec.get('ADD NOTN SNO')
            cvd_notn_sno = rec.get('CVD NOTN SNO')
            sg_notn_sno = rec.get('SG  NOTN SNO')
            t_value_notn_sno = rec.get('T. VALUE  NOTN SNO')
            bcd_rate = rec.get('BCD RATE')
            acd_rate = rec.get('ACD  RATE')
            sws_rate = rec.get('SWS RATE')
            sad_rate = rec.get('SAD RATE')
            igst_rate = rec.get('IGST RATE')
            g_cess_rate = rec.get('G. CESS  RATE')
            add_rate = rec.get('ADD RATE')
            cvd_rate = rec.get('CVD RATE')
            sg_rate = rec.get('SG  RATE')
            t_value_rate = rec.get('T. VALUE  RATE')
            bcd_amount = rec.get('BCD AMOUNT')
            acd_amount = rec.get('ACD  AMOUNT')
            sws_amount = rec.get('SWS AMOUNT')
            sad_amount = rec.get('SAD AMOUNT')
            igst_amount = rec.get('IGST AMOUNT')
            g_cess_amount = rec.get('G. CESS  AMOUNT')
            add_amount = rec.get('ADD AMOUNT')
            cvd_amount = rec.get('CVD AMOUNT')
            sg_amount = rec.get('SG  AMOUNT')
            t_value_amount = rec.get('T. VALUE  AMOUNT')
            bcd_duty_fg = rec.get('BCD Duty FG')
            acd_duty_fg = rec.get('ACD  Duty FG')
            sws_duty_fg = rec.get('SWS Duty FG')
            sad_duty_fg = rec.get('SAD Duty FG')
            igst_duty_fg = rec.get('IGST Duty FG')
            g_cess_duty_fg = rec.get('G. CESS  Duty FG')
            add_duty_fg = rec.get('ADD Duty FG')
            cvd_duty_fg = rec.get('CVD Duty FG')
            sg_duty_fg = rec.get('SG  Duty FG')
            t_value_duty_fg = rec.get('T. VALUE  Duty FG')
            sp_exd_notn_no = rec.get('SP EXD NOTN NO')
            chcess_notn_no = rec.get('CHCESS NOTN NO')
            tta_notn_no = rec.get('TTA NOTN NO')
            cess_notn_no = rec.get('CESS NOTN NO')
            caidc_notn_no = rec.get('CAIDC NOTN NO')
            eaidc_notn_no = rec.get('EAIDC NOTN NO')
            cus_edc_notn_no = rec.get('CUS EDC NOTN NO')
            cus_hec_notn_no = rec.get('CUS HEC NOTN NO')
            ncd_notn_no = rec.get('NCD NOTN NO')
            aggr_notn_no = rec.get('AGGR NOTN NO')
            sp_exd_notn_sno = rec.get('SP EXD NOTN SNO')
            chcess_notn_sno = rec.get('CHCESS NOTN SNO')
            tta_notn_sno = rec.get('TTA NOTN SNO')
            cess_notn_sno = rec.get('CESS NOTN SNO')
            caidc_notn_sno = rec.get('CAIDC NOTN SNO')
            eaidc_notn_sno = rec.get('EAIDC NOTN SNO')
            cus_edc_notn_sno = rec.get('CUS EDC NOTN SNO')
            cus_hec_notn_sno = rec.get('CUS HEC NOTN SNO')
            ncd_notn_sno = rec.get('NCD NOTN SNO')
            aggr_notn_sno = rec.get('AGGR NOTN SNO')
            sp_exd_rate = rec.get('SP EXD RATE')
            chcess_rate = rec.get('CHCESS RATE')
            tta_rate = rec.get('TTA RATE')
            cess_rate = rec.get('CESS RATE')
            caidc_rate = rec.get('CAIDC RATE')
            eaidc_rate = rec.get('EAIDC RATE')
            cus_edc_rate = rec.get('CUS EDC RATE')
            cus_hec_rate = rec.get('CUS HEC RATE')
            ncd_rate = rec.get('NCD RATE')
            aggr_rate = rec.get('AGGR RATE')
            sp_exd_amount = rec.get('SP EXD Amount')
            chcess_amount = rec.get('CHCESS Amount')
            tta_amount = rec.get('TTA Amount')
            cess_amount = rec.get('CESS Amount')
            caidc_amount = rec.get('CAIDC Amount')
            eaidc_amount = rec.get('EAIDC Amount')
            cus_edc_amount = rec.get('CUS EDC Amount')
            cus_hec_amount = rec.get('CUS HEC Amount')
            ncd_amount = rec.get('NCD Amount')
            aggr_amount = rec.get('AGGR Amount')
            sp_exd_duty_fg = rec.get('SP EXD Duty Fg')
            chcess_duty_fg = rec.get('CHCESS Duty Fg')
            tta_duty_fg = rec.get('TTA Duty Fg')
            cess_duty_fg = rec.get('CESS Duty Fg')
            caidc_duty_fg = rec.get('CAIDC Duty Fg')
            eaidc_duty_fg = rec.get('EAIDC Duty Fg')
            cus_edc_duty_fg = rec.get('CUS EDC Duty Fg')
            cus_hec_duty_fg = rec.get('CUS HEC Duty Fg')
            ncd_duty_fg = rec.get('NCD Duty Fg')
            aggr_duty_fg = rec.get('AGGR Duty Fg')
            ref_no = rec.get('REF NO')
            ref_dt = rec.get('REF DT')
            prt_cd = rec.get('PRT CD')
            lab = rec.get('LAB')
            load_date = rec.get('LOAD DATE')
            load_pf = rec.get('P/F')
            p_f = rec.get('P/F')
            be_no = str(rec.get('BE No'))
            prev_be_no = str(rec.get('PREV BE NO'))
            be_date = rec.get('BE DATE')
            prt_cd_new = rec.get('PREV PRT CD')
            prev_unitprice = rec.get('UNITPRICE') if rec.get('UNITPRICE') else False
            prev_currency_code = rec.get('CURRENCY CODE')
            notn_no = rec.get('NOTN NO')
            slno = rec.get('SLNO')
            frt = rec.get('FRT')
            ins = rec.get('INS')
            duty = rec.get('DUTY')
            sb_no = rec.get('SB NO')
            sb_dt = rec.get('SB DT')
            port_cd = rec.get('PORT CD')
            sinv = rec.get('SINV')
            simtemn = rec.get('SIMTEMN')
            type = rec.get('TYPE')
            manufact_cd = rec.get('MANUFACT CD')
            source_cy = rec.get('SOURCE CY')
            trans_cy = rec.get('TRANS CY')
            address = rec.get('ADDRESS')
            accessory_item_details = rec.get('ACCESSORY ITEM DETAILS')
            lic_slno = rec.get('LIC SLNO')
            lic_no = rec.get('LIC NO')
            lic_date = rec.get('LIC DATE')
            code = rec.get('CODE')
            port = rec.get('PORT')
            debit_value = rec.get('DEBIT VALUE')
            qty = rec.get('QTY')
            debit_qty = rec.get('DEBIT QTY')
            certificate_number = rec.get('CERTIFICATE NUMBER')
            date = rec.get('DATE')
            type_new = rec.get('TYPE')
            prc_level = rec.get('PRC LEVEL')
            iec = rec.get('IEC')
            branch_slno = rec.get('BRANCH SLNO')
            info_type = rec.get('INFO TYPE')
            qualifier = rec.get('QUALIFIER')
            info_cd = rec.get('INFO CD')
            info_text = rec.get('INFO TEXT')
            info_msr = rec.get('INFO MSR')
            uqc = rec.get('UQC')
            c_sno = rec.get('C SNO')
            new_name = rec.get('NAME')
            code_new = rec.get('CODE')
            percentage = rec.get('PERCENTAGE')
            yield_pct = rec.get('YIELD PCT')
            ing = rec.get('ING')
            control_type = rec.get('CONTROL TYPE')
            location = rec.get('LOCATION')
            srt_dt = rec.get('SRT DT')
            end_dt = rec.get('END DT')
            res_cd = rec.get('RES CD')
            res_text = rec.get('RES TEXT')

            order_line_list = []
            order_line_details = (0, 0, {
                # 'product_id': search_product.id,
                'invsno': invsno,
                'itemsn': itemsn,
                'invoice_no_new': invoice_no_new,
                'part_code': part_code,
                'cth': cth,
                # 'product_id': product,
                'ceth': ceth,
                'item_description': item_description,
                'fs': fs,
                'pq': pq,
                'dc': dc,
                'wc': wc,
                'aq': aq,
                'upi': upi,
                'coo': coo,
                'cqty': cqty,
                'cuqc': cuqc,
                'sqty': sqty,
                'suqc': suqc,
                'sch': sch,
                'stnd_pr': stnd_pr,
                'rsp': rsp,
                'reimp': reimp,
                'prov': prov,
                'end_use': end_use,
                'prodn': prodn,
                'cntrl': cntrl,
                'qualfr': qualfr,
                'contnt': contnt,
                'stmnt': stmnt,
                'sub_docs': sub_docs,
                'assess_value': assess_value,
                'total_duty': float(total_duty),
                'bcd_notn_no': bcd_notn_no,
                'acd_notn_no': acd_notn_no,
                'sws_notn_no': sws_notn_no,
                'sad_notn_no': sad_notn_no,
                'igst_notn_no': igst_notn_no,
                'g_cess_notn_no': g_cess_notn_no,
                'add_notn_no': add_notn_no,
                'cvd_notn_no': cvd_notn_no,
                'sg_notn_no': sg_notn_no,
                't_value_notn_no': t_value_notn_no,
                'bcd_notn_sno': bcd_notn_sno,
                'acd_notn_sno': acd_notn_sno,
                'sws_notn_sno': sws_notn_sno,
                'sad_notn_sno': sad_notn_sno,
                'igst_notn_sno': igst_notn_sno,
                'g_cess_notn_sno': g_cess_notn_sno,
                'add_notn_sno': add_notn_sno,
                'cvd_notn_sno': cvd_notn_sno,
                'sg_notn_sno': sg_notn_sno,
                't_value_notn_sno': t_value_notn_sno,
                'bcd_rate': bcd_rate,
                'acd_rate': acd_rate,
                'sws_rate': sws_rate,
                'sad_rate': sad_rate,
                'igst_rate': igst_rate,
                'g_cess_rate': g_cess_rate,
                'add_rate': add_rate,
                'cvd_rate': cvd_rate,
                'sg_rate': sg_rate,
                't_value_rate': t_value_rate,
                'bcd_amount': bcd_amount,
                'acd_amount': acd_amount,
                'sws_amount': sws_amount,
                'sad_amount': sad_amount,
                'igst_amount': igst_amount,
                'g_cess_amount': g_cess_amount,
                'add_amount': add_amount,
                'cvd_amount': cvd_amount,
                'sg_amount': sg_amount,
                't_value_amount': t_value_amount,
                'bcd_duty_fg': bcd_duty_fg,
                'acd_duty_fg': acd_duty_fg,
                'sws_duty_fg': sws_duty_fg,
                'sad_duty_fg': sad_duty_fg,
                'igst_duty_fg': igst_duty_fg,
                'g_cess_duty_fg': g_cess_duty_fg,
                'add_duty_fg': add_duty_fg,
                'cvd_duty_fg': cvd_duty_fg,
                'sg_duty_fg': sg_duty_fg,
                't_value_duty_fg': t_value_duty_fg,
                'sp_exd_notn_no': sp_exd_notn_no,
                'chcess_notn_no': chcess_notn_no,
                'tta_notn_no': tta_notn_no,
                'cess_notn_no': cess_notn_no,
                'caidc_notn_no': caidc_notn_no,
                'eaidc_notn_no': eaidc_notn_no,
                'cus_edc_notn_no': cus_edc_notn_no,
                'cus_hec_notn_no': cus_hec_notn_no,
                'ncd_notn_no': ncd_notn_no,
                'aggr_notn_no': aggr_notn_no,
                'sp_exd_notn_sno': sp_exd_notn_sno,
                'chcess_notn_sno': chcess_notn_sno,
                'tta_notn_sno': tta_notn_sno,
                'cess_notn_sno': cess_notn_sno,
                'caidc_notn_sno': caidc_notn_sno,
                'eaidc_notn_sno': eaidc_notn_sno,
                'cus_edc_notn_sno': cus_edc_notn_sno,
                'cus_hec_notn_sno': cus_hec_notn_sno,
                'ncd_notn_sno': ncd_notn_sno,
                'aggr_notn_sno': aggr_notn_sno,
                'sp_exd_rate': sp_exd_rate,
                'chcess_rate': chcess_rate,
                'tta_rate': tta_rate,
                'cess_rate': cess_rate,
                'caidc_rate': caidc_rate,
                'eaidc_rate': eaidc_rate,
                'cus_edc_rate': cus_edc_rate,
                'cus_hec_rate': cus_hec_rate,
                'ncd_rate': ncd_rate,
                'aggr_rate': aggr_rate,
                'sp_exd_amount': sp_exd_amount,
                'chcess_amount': chcess_amount,
                'tta_amount': tta_amount,
                'cess_amount': cess_amount,
                'caidc_amount': caidc_amount,
                'eaidc_amount': eaidc_amount,
                'cus_edc_amount': cus_edc_amount,
                'cus_hec_amount': cus_hec_amount,
                'ncd_amount': ncd_amount,
                'aggr_amount': aggr_amount,
                'sp_exd_duty_fg': sp_exd_duty_fg,
                'chcess_duty_fg': chcess_duty_fg,
                'tta_duty_fg': tta_duty_fg,
                'cess_duty_fg': cess_duty_fg,
                'caidc_duty_fg': caidc_duty_fg,
                'eaidc_duty_fg': eaidc_duty_fg,
                'cus_edc_duty_fg': cus_edc_duty_fg,
                'cus_hec_duty_fg': cus_hec_duty_fg,
                'ncd_duty_fg': ncd_duty_fg,
                'aggr_duty_fg': aggr_duty_fg,
                'ref_no': ref_no,
                'ref_dt': ref_dt,
                'prt_cd': prt_cd,
                'lab': lab,
                'p_f': p_f,
                'load_date': load_date,
                'load_pf': load_pf,
                'be_no': be_no,
                'prev_be_no': prev_be_no,
                'be_date': be_date,
                'prt_cd_new': prt_cd_new,
                'prev_unitprice': prev_unitprice,
                'prev_currency_code': prev_currency_code,
                'notn_no': notn_no,
                'slno': slno,
                'frt': frt,
                'ins': ins,
                'duty': duty,
                'sb_no': sb_no,
                'sb_dt': sb_dt,
                'port_cd': port_cd,
                'sinv': sinv,
                'simtemn': simtemn,
                'type': type,
                'manufact_cd': manufact_cd,
                'source_cy': source_cy,
                'trans_cy': trans_cy,
                'address': address,
                'accessory_item_details': accessory_item_details,
                'lic_slno': lic_slno,
                'lic_no': lic_no,
                'lic_date': lic_date,
                'code': code,
                'port': port,
                'debit_value': debit_value,
                'qty': qty,
                'debit_qty': debit_qty,
                'certificate_number': certificate_number,
                'date': date,
                'type_new': type_new,
                'prc_level': prc_level,
                'iec': iec,
                'branch_slno': branch_slno,
                'info_type': info_type,
                'qualifier': qualifier,
                'info_cd': info_cd,
                'info_text': info_text,
                'info_msr': info_msr,
                'uqc': uqc,
                'c_sno': c_sno,
                'new_name': new_name,
                'code_new': code_new,
                'percentage': percentage,
                'yield_pct': yield_pct,
                'ing': ing,
                'control_type': control_type,
                'location': location,
                'srt_dt': srt_dt,
                'end_dt': end_dt,
                'res_cd': res_cd,
                'res_text': res_text,
            })
            search_po = self.env['non.moowr'].search([('be', '=', be_no)])
            if search_po:
                search_invoice = self.env['invoice.nonmoowr.line'].search([('invoice_no', '=', invoice_no_new)])
                if search_invoice:
                    order_line_list.append(order_line_details)
                    # if int(search_po.item_count) == count:
                    search_po.with_context(Product=True).write({'order_line': order_line_list})
                    # else:
                    #     raise ValidationError('Item lines does not match with item counts')
            else:
                raise ValidationError("BE No doesn't exist")
        message = _("Upload Successfull")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }


class InvoiceLine(models.Model):
    _name = 'invoice.line'

    upload_invoice_line = fields.Binary('Upload Invoice Line')

    def convert_to_df(self):
        csv_data = self.upload_invoice_line
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_invoice_line(self):
        df = self.convert_to_df()
        data = df.to_dict('index')

        count = len(data.keys())
        # vals_count = data.values()
        print(count)
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []
        for rec in b:
            invsno = rec.get('INVSNO')
            invoice_no = rec.get('INVOICE NO')
            invoice_date = rec.get('INVOICE DATE')
            purchase_order_no_and_dt = rec.get('PURCHASE ORDER NO. & DT')
            lc_no_dt = rec.get('LC NO & DT')
            contract_no_date = rec.get('CONTRACT NO & DATE')
            buyers_name = rec.get("BUYER'S NAME")
            buyers_address = rec.get("BUYER'S ADDRESS")
            sellers_name = rec.get("SELLER'S NAME")
            sellers_address = rec.get("SELLER'S ADDRESS")
            suppliers_name = rec.get("SUPPLIER'S NAME")
            suppliers_address = rec.get("SUPPLIER'S ADDRESS")
            third_party_name = rec.get('THIRD PARTY NAME')
            third_party_address = rec.get('THIRD PARTY ADDRESS')
            aeo = rec.get('AEO')
            ad_code = rec.get('AD CODE')
            inv_value = rec.get('INV VALUE')
            freight = rec.get('FREIGHT')
            insurance = rec.get('INSURANCE')
            hss = rec.get('HSS')
            loading = rec.get('LOADING')
            commn = rec.get('COMMN')
            pay_terms = rec.get('PAY TERMS')
            valuation_method = rec.get('VALUATION METHOD')
            currency = rec.get('CURRENCY')
            incoterm = rec.get('INCOTERM')
            reltd = rec.get('RELTD')
            svb_ch = rec.get('SVB CH')
            svb_no = rec.get('SVB NO')
            date = rec.get('DATE')
            loa = rec.get('LOA')
            c_b = rec.get('C&B')
            coc = rec.get('CoC')
            cop = rec.get('CoP')
            hnd_chg = rec.get('HND CHG')
            gs = rec.get('G&S')
            doc_chg = rec.get('DOC CHG')
            coo = rec.get('COO')
            r_lf = rec.get('R & LF')
            oth_cost = rec.get('OTH COST')
            ld_uld = rec.get('LD/ULD')
            ws = rec.get('WS')
            otc = rec.get('OTC')
            misc_charge = rec.get('MISC CHARGE')
            ass_value = rec.get('ASS. VALUE')
            be = str(rec.get('BE No'))

            date_convert = datetime.strptime(date, '%d/%m/%Y')
            # if invsno == 0:
            #     raise ValidationError('Invoise serial no is missing')
            invoice_line_list = []
            invoice_line_details = (0, 0, {
                'invsno': invsno,
                'invoice_no': invoice_no,
                'invoice_date': invoice_date,
                'purchase_order_no_and_dt': purchase_order_no_and_dt,
                'lc_no_dt': lc_no_dt,
                'contract_no_date': contract_no_date,
                'buyers_name': buyers_name,
                'buyers_address': buyers_address,
                'sellers_name': sellers_name,
                'sellers_address': sellers_address,
                'suppliers_name': suppliers_name,
                'suppliers_address': suppliers_address,
                'third_party_name': third_party_name,
                'third_party_address': third_party_address,
                'aeo': aeo,
                'ad_code': ad_code,
                'inv_value': inv_value,
                'freight': freight,
                'insurance': insurance,
                'hss': hss,
                'loading': loading,
                'commn': commn,
                'pay_terms': pay_terms,
                'valuation_method': valuation_method,
                'currency': currency,
                'incoterm': incoterm,
                'reltd': reltd,
                'svb_ch': svb_ch,
                'svb_no': svb_no,
                'date': date_convert,
                'loa': loa,
                'c_b': c_b,
                'coc': coc,
                'cop': cop,
                'hnd_chg': hnd_chg,
                'gs': gs,
                'doc_chg': doc_chg,
                'coo': coo,
                'r_lf': r_lf,
                'oth_cost': oth_cost,
                'ld_uld': ld_uld,
                'ws': ws,
                'otc': otc,
                'misc_charge': misc_charge,
                'ass_value': ass_value,
                'be': be
            })
            search_po = self.env['non.moowr'].search([('be', '=', be)])
            if search_po:
                a = search_po.invoice_tab_ids.mapped('invoice_no')
                if invsno is None:
                    raise ValidationError('Invoice Serial Number is missing')
                if str(invoice_no) not in a:
                    invoice_line_list.append(invoice_line_details)
                    # if int(search_po.invoice_count_new) == len(search_po):
                    search_po.with_context(invoice=True).write({'invoice_tab_ids': invoice_line_list})
                    # else:
                    #     raise ValidationError('Invoice Lines does not match with invoice counts ')
                # else:
                #     raise ValidationError(f'Invoice Number {invoice_no} already exist')
            else:
                raise ValidationError("BE No doesn't exist")
        message = _("Upload Successfull")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    # def import_invoice_line(self):
    #     df = self.convert_to_df()
    #     data = df.to_dict('index')
    #
    #     count = len(data.keys())
    #     # vals_count = data.values()
    #     print(count)
    #     boe_count = {}
    #     b = []  # b is list of dictionary with data of each row
    #     number = 0
    #     for rec in data.values():
    #         boe = self.env['non.moowr'].search([('be', '=', rec.get('BE No'))])
    #         number = int(boe.invoice_count_new)
    #         pass
    #
    #     data_new = {}
    #     for rec in data.values():
    #         if number != 0:
    #             for i, j in rec.items():
    #                 if j is not False:
    #                     data_new[i] = j
    #             b.append(data_new)
    #             number -= 1
    #
    #     for rec in b:
    #         invsno = rec.get('INVSNO')
    #         invoice_no = rec.get('INVOICE NO')
    #         invoice_date = rec.get('INVOICE DATE')
    #         purchase_order_no_and_dt = rec.get('PURCHASE ORDER NO. & DT')
    #         lc_no_dt = rec.get('LC NO & DT')
    #         contract_no_date = rec.get('CONTRACT NO & DATE')
    #         buyers_name = rec.get("BUYER'S NAME")
    #         buyers_address = rec.get("BUYER'S ADDRESS")
    #         sellers_name = rec.get("SELLER'S NAME")
    #         sellers_address = rec.get("SELLER'S ADDRESS")
    #         suppliers_name = rec.get("SUPPLIER'S NAME")
    #         suppliers_address = rec.get("SUPPLIER'S ADDRESS")
    #         third_party_name = rec.get('THIRD PARTY NAME')
    #         third_party_address = rec.get('THIRD PARTY ADDRESS')
    #         aeo = rec.get('AEO')
    #         ad_code = rec.get('AD CODE')
    #         inv_value = rec.get('INV VALUE')
    #         freight = rec.get('FREIGHT')
    #         insurance = rec.get('INSURANCE')
    #         hss = rec.get('HSS')
    #         loading = rec.get('LOADING')
    #         commn = rec.get('COMMN')
    #         pay_terms = rec.get('PAY TERMS')
    #         valuation_method = rec.get('VALUATION METHOD')
    #         currency = rec.get('CURRENCY')
    #         incoterm = rec.get('INCOTERM')
    #         reltd = rec.get('RELTD')
    #         svb_ch = rec.get('SVB CH')
    #         svb_no = rec.get('SVB NO')
    #         date = rec.get('DATE')
    #         loa = rec.get('LOA')
    #         c_b = rec.get('C&B')
    #         coc = rec.get('CoC')
    #         cop = rec.get('CoP')
    #         hnd_chg = rec.get('HND CHG')
    #         gs = rec.get('G&S')
    #         doc_chg = rec.get('DOC CHG')
    #         coo = rec.get('COO')
    #         r_lf = rec.get('R & LF')
    #         oth_cost = rec.get('OTH COST')
    #         ld_uld = rec.get('LD/ULD')
    #         ws = rec.get('WS')
    #         otc = rec.get('OTC')
    #         misc_charge = rec.get('MISC CHARGE')
    #         ass_value = rec.get('ASS. VALUE')
    #         be = str(rec.get('BE No'))
    #
    #         date_convert = datetime.strptime(date, '%d/%m/%Y')
    #         # if invsno == 0:
    #         #     raise ValidationError('Invoise serial no is missing')
    #         invoice_line_list = []
    #         invoice_line_details = (0, 0, {
    #             'invsno': invsno,
    #             'invoice_no': invoice_no,
    #             'invoice_date': invoice_date,
    #             'purchase_order_no_and_dt': purchase_order_no_and_dt,
    #             'lc_no_dt': lc_no_dt,
    #             'contract_no_date': contract_no_date,
    #             'buyers_name': buyers_name,
    #             'buyers_address': buyers_address,
    #             'sellers_name': sellers_name,
    #             'sellers_address': sellers_address,
    #             'suppliers_name': suppliers_name,
    #             'suppliers_address': suppliers_address,
    #             'third_party_name': third_party_name,
    #             'third_party_address': third_party_address,
    #             'aeo': aeo,
    #             'ad_code': ad_code,
    #             'inv_value': inv_value,
    #             'freight': freight,
    #             'insurance': insurance,
    #             'hss': hss,
    #             'loading': loading,
    #             'commn': commn,
    #             'pay_terms': pay_terms,
    #             'valuation_method': valuation_method,
    #             'currency': currency,
    #             'incoterm': incoterm,
    #             'reltd': reltd,
    #             'svb_ch': svb_ch,
    #             'svb_no': svb_no,
    #             'date': date_convert,
    #             'loa': loa,
    #             'c_b': c_b,
    #             'coc': coc,
    #             'cop': cop,
    #             'hnd_chg': hnd_chg,
    #             'gs': gs,
    #             'doc_chg': doc_chg,
    #             'coo': coo,
    #             'r_lf': r_lf,
    #             'oth_cost': oth_cost,
    #             'ld_uld': ld_uld,
    #             'ws': ws,
    #             'otc': otc,
    #             'misc_charge': misc_charge,
    #             'ass_value': ass_value,
    #             'be': be
    #         })
    #         search_po = self.env['non.moowr'].search([('be', '=', be)])
    #         if search_po:
    #             a = search_po.invoice_tab_ids.mapped('invoice_no')
    #             if invsno is None:
    #                 raise ValidationError('Invoice Serial Number is missing')
    #             if str(invoice_no) not in a:
    #                 invoice_line_list.append(invoice_line_details)
    #                 # if int(search_po.invoice_count_new) == len(search_po):
    #                 search_po.with_context(invoice=True).write({'invoice_tab_ids': invoice_line_list})
    #                 # else:
    #                 #     raise ValidationError('Invoice Lines does not match with invoice counts ')
    #             # else:
    #             #     raise ValidationError(f'Invoice Number {invoice_no} already exist')
    #         else:
    #             raise ValidationError("BE No doesn't exist")
    #
    #     message = _("Upload Successfull")
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': message,
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }



class BoeShipmentTab(models.Model):
    _name = 'boe.shipment.tab'

    upload_boe_shipment = fields.Binary('Upload Boe Shipment')

    def convert_to_df(self):
        csv_data = self.upload_boe_shipment
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_boe_shipment(self):
        df = self.convert_to_df()
        data = df.to_dict('index')
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []
        for rec in b:
            igm_no = rec.get('IGM NO')
            igm_date = rec.get('IGM DATE')
            inw_date = rec.get('INW DATE')
            gigmno = rec.get('GIGMNO')
            gigmdt = rec.get('GIGMDT')
            mawb_mbl = rec.get('MAWB NO')
            mawb_date = rec.get('MAWB DATE')
            hawb_no = rec.get('HAWB NO')
            hawb_date = rec.get('HAWB DATE')
            pkg = rec.get('PKG')
            gw = rec.get('GW')
            be = str(rec.get('BE No'))

            igm_date_convert = False
            if igm_date:
                igm_date_convert = datetime.strptime(igm_date, '%d/%m/%Y')

            inw_date_convert = False
            if inw_date:
                inw_date_convert = datetime.strptime(inw_date, '%d/%m/%Y')

            gigmdt_convert = False
            if gigmdt:
                gigmdt_convert = datetime.strptime(gigmdt, '%d/%m/%Y')

            mawb_date_convert = False
            if mawb_date:
                mawb_date_convert = datetime.strptime(mawb_date, '%d/%m/%Y')

            hawb_date_convert = False
            if hawb_date:
                hawb_date_convert = datetime.strptime(hawb_date, '%d/%m/%Y')

            boe_shipment_list = []
            boe_shipment_details = (0, 0, {
                'igm_no': igm_no,
                'igm_date': igm_date_convert if igm_date_convert else False,
                'inw_date': inw_date_convert if inw_date_convert else False,
                'gigmno': gigmno,
                'gigmdt': gigmdt_convert if gigmdt_convert else False,
                'mawb_mbl': mawb_mbl,
                'mawb_date': mawb_date_convert if mawb_date_convert else False,
                'hawb_no': hawb_no,
                'hawb_date': hawb_date_convert if hawb_date_convert else False,
                'pkg': pkg,
                'gw': gw,
                'be': be
            })
            search_po = self.env['non.moowr'].search([('be', '=', be)])
            if search_po:
                a = search_po.shipment_ids.mapped('igm_no')
                if str(igm_no) not in a:
                    boe_shipment_list.append(boe_shipment_details)
                    search_po.with_context(shipment=True).write({'shipment_ids': boe_shipment_list})
            else:
                raise ValidationError("BE No doesn't exist")
        message = _("Upload Successfull")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }



class BoeContainerTab(models.Model):
    _name = 'boe.container.tab'

    upload_boe_container = fields.Binary('Upload Boe Container')

    def convert_to_df(self):
        csv_data = self.upload_boe_container
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_boe_container(self):
        df = self.convert_to_df()
        data = df.to_dict('index')
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []
        for rec in b:
            container_no = rec.get('Container Number')
            seal_no = rec.get('Seal Number')
            truck_no = rec.get('Truck Number')
            fcl_lcl = rec.get('FCL/LCL')
            be = rec.get('BE No')

            boe_container_list = []
            boe_container_details = (0, 0, {
                'container_no': container_no,
                'seal_no': seal_no,
                'truck_no': truck_no,
                'fcl_lcl': fcl_lcl,
                'be': be
            })
            search_po = self.env['non.moowr'].search([('be', '=', be)])
            if search_po:
                a = search_po.container_ids.mapped('container_no')
                if str(container_no) not in a:
                    boe_container_list.append(boe_container_details)
                    search_po.with_context(container=True).write({'container_ids': boe_container_list})

            else:
                raise ValidationError("BE No doesn't exist")
        message = _("Upload Successfull")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }


