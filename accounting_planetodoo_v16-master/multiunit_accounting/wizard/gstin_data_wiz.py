from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
class GSTINUnitData(models.TransientModel):
    _name = 'gstinunit.data'

    gstin_o2m = fields.One2many('gstin.o2m','wiz_id',string="GSTIN Units")
    sale_taxes = fields.Many2many('account.tax','gstin_sale_rel',string="Sale Taxes")
    po_taxes = fields.Many2many('account.tax','gstin_po_rel',string="Purchase Taxes")
    journal_ids = fields.Many2many('account.journal', 'gstin_journal_rel', string="Journals")

    def create_ledgers(self,unit,account,type):
        def_account = self.env['account.account'].sudo().search([('name','=',account.name + "(" + str(unit.code) + ")"),
                                                                 ('company_id', '=', self.env.company.id)],limit=1)

        if type == 'interbranch':
            interbranch_coa = "Interbranch "+account.name + "(" + str(unit.code) + ")"
            search_interbranch_coa = self.env['account.account'].sudo().search(
                [('name', '=', interbranch_coa),
                 ('company_id', '=', self.env.company.id)], limit=1)

            if not search_interbranch_coa:
                def_account = account.copy({
                        'name': interbranch_coa,
                        'gstin_unit_id':unit.gstin_id.id,
                        'is_a_default':False,
                        'company_id': self.env.company.id,})
        else:
            if not def_account:
                def_account = account.copy({
                        'name':account.name + "(" + str(unit.code) + ")",
                        'gstin_unit_id':unit.gstin_id.id,
                        'is_a_default':False,
                        'company_id': self.env.company.id,})

        return def_account.id

    def create_journals(self,unit):
        journals = self.env['account.journal'].search([('type','in',('sale','purchase','general')),
                                                           ('is_a_default','=',True), ('company_id', '=', self.env.company.id)]) if not self.journal_ids else self.journal_ids
        journal_list = []
        # for multiunits
        for rec in journals:
            unit_journal = rec.sudo().copy({
                'name':rec.name + "(" + str(unit.code) + ")",
                'code':rec.code + str(unit.code),
                'l10n_in_gstin_partner_id':unit.gstin_id.id,
                'is_a_default':False,
                'default_account_id': self.create_ledgers(unit,rec.default_account_id,'gst_unit') if rec.default_account_id else False,
                'loss_account_id': self.create_ledgers(unit,rec.loss_account_id,'gst_unit') if rec.loss_account_id else False,
                'profit_account_id': self.create_ledgers(unit,rec.profit_account_id,'gst_unit') if rec.profit_account_id else False,
                'suspense_account_id': self.create_ledgers(unit,rec.suspense_account_id,'gst_unit') if rec.suspense_account_id else False,
                'company_id': self.env.company.id,
                })
            unit_journal.name=rec.name + "(" + str(unit.code) + ")"
            unit_journal.code=rec.code + str(unit.code)
            # if unit_journal.alias_id:
            unit_journal.alias_id.alias_name = self.env.company.name + unit_journal.name
            unit_journal.alias_name = self.env.company.name + unit_journal.name
            journal_list.append(unit_journal)

            # for interjournals
            interbranch_journal_name = "Interbranch " + rec.name + "(" + str(unit.code) + ")"
            interbranch_journal_code = "T-" + rec.code + "(" + str(unit.code) + ")"
            search_interbranch_journal = self.env['account.journal'].sudo().search([('name', '=', interbranch_journal_name),
                                                                                ('company_id', '=', self.env.company.id),
                                                                                ('type', 'in',('sale','purchase','general'))], limit=1)

            if not search_interbranch_journal:
                interbranch_journal = rec.sudo().copy({
                    'name': interbranch_journal_name,
                    'code': interbranch_journal_code,
                    'l10n_in_gstin_partner_id': unit.gstin_id.id,
                    'is_a_default': False,
                    'interbranch': True,
                    'default_account_id': self.create_ledgers(unit, rec.default_account_id,
                                                              'interbranch') if rec.default_account_id else False,
                    'loss_account_id': self.create_ledgers(unit, rec.loss_account_id,
                                                           'interbranch') if rec.loss_account_id else False,
                    'profit_account_id': self.create_ledgers(unit, rec.profit_account_id,
                                                             'interbranch') if rec.profit_account_id else False,
                    'suspense_account_id': self.create_ledgers(unit, rec.suspense_account_id,
                                                               'interbranch') if rec.suspense_account_id else False,
                    'company_id': self.env.company.id,
                })
                interbranch_journal.name = interbranch_journal_name
                interbranch_journal.code = interbranch_journal_code
                # if interbranch_journal.alias_id:
                interbranch_journal.alias_id.alias_name = self.env.company.name + interbranch_journal.name
                interbranch_journal.alias_name = self.env.company.name + interbranch_journal.name
                journal_list.append(interbranch_journal)

        return journal_list

    def create_taxes(self,unit,taxes):
        tax_list = []
        for tax in taxes:
            unit_tax = tax.sudo().copy({'name':tax.name + "(" + str(unit.code) + ")",
                                             'gstin_unit_id':unit.gstin_id.id,
                                             'is_a_default':False, 'company_id': self.env.company.id})
            for invoice_tax_line in unit_tax.invoice_repartition_line_ids:
                invoice_tax_line.account_id = self.create_ledgers(unit,invoice_tax_line.account_id,'gst_unit') if invoice_tax_line.account_id else False

            for refund_tax_line in unit_tax.refund_repartition_line_ids:
                refund_tax_line.account_id = self.create_ledgers(unit,refund_tax_line.account_id,'gst_unit') if refund_tax_line.account_id else False
            child_ids = []
            if unit_tax.children_tax_ids:
                child = self.create_taxes(unit,unit_tax.children_tax_ids)
                # unit_tax.children_tax_ids = (5)
                if child:
                    child_ids = [rec.id for rec in child]
                    unit_tax.children_tax_ids = [(6,0,child_ids)]
            tax_list.append(unit_tax)
        return tax_list

    def create_fiscal_positions(self,unit,taxes):
        fiscal_types = {'inter':"Inter",'intra':"Intra"}
        gst_taxes = taxes.sudo().search([('is_a_default','=',True),'|',('tax_group_id.name','=',"GST"),('tax_group_id.name','=',"gst")
                                        ,('name','not like','(RC)'), ('company_id', '=', self.env.company.id)])
        fiscal_lists = []
        fiscal_obj = self.env['account.fiscal.position']
        for type in fiscal_types:
            mapping_list = []
            for tax in gst_taxes:
                igst_tax = self.env['account.tax'].sudo().search([('gstin_unit_id','=',unit.gstin_id.id),('is_a_default','=',False),('amount','=',tax.amount),
                                                                  '|',('tax_group_id.name','=',"IGST"),('tax_group_id.name','=',"igst")
                                                                     ,('type_tax_use','=',tax.type_tax_use),('name','not like','(RC)'), ('company_id', '=', self.env.company.id)])
                gst_tax = self.env['account.tax'].sudo().search(
                    [('gstin_unit_id', '=', unit.gstin_id.id), ('is_a_default', '=', False),
                     ('amount', '=', tax.amount),
                     '|', ('tax_group_id.name', '=', "GST"), ('tax_group_id.name', '=', "gst")
                        , ('type_tax_use', '=', tax.type_tax_use), ('name', 'not like', '(RC)'),
                     ('company_id', '=', self.env.company.id)])
                mapping_list.append((0,0,{
                    'tax_src_id':tax.id,
                    'tax_dest_id':igst_tax.id if type == 'inter' and igst_tax else gst_tax.id,
                    'company_id': self.env.company.id,
                }))
            fiscal_lists.append(fiscal_obj.sudo().create({
                'name':unit.code + "-" +str(fiscal_types[type]),
                'gstin_unit':unit.gstin_id.id,
                'state':type,
                'company_id': self.env.company.id,
                'tax_ids':mapping_list,

            }))
        return fiscal_lists


    def create_gstin_unit_data(self):
        for unit in self.gstin_o2m:
            self.create_journals(unit)
            self.create_taxes(unit,self.sale_taxes + self.po_taxes)
            self.create_fiscal_positions(unit,self.sale_taxes + self.po_taxes)
            coa = self.env['account.account'].sudo().search(
                [('account_type', '=', 'liability_current'), ('is_a_default', '=', True),
                 ('company_id', '=', self.env.company.id)], limit=1)

            coa_name = str(self.env.company.name) + " " + unit.code + " (Settlement)"
            search_coa = self.env['account.account'].sudo().search(
                [('name', '=', coa_name), ('account_type', '=', 'liability_current'), ('is_a_default', '=', True),
                 ('company_id', '=', self.env.company.id)], limit=1)

            if not search_coa:
                coa.copy({
                    'name': coa_name,
                    'account_type': 'liability_current',
                    'interbranch_settlement': True,
                    'gstin_unit_id': unit.gstin_id.id,
                    'is_a_default': False,
                    'company_id': self.env.company.id
                })

            #######################Interbranch Payment##############
            general_journal = self.env['account.journal'].sudo().search([('is_a_default', '=', True),
                 ('company_id', '=', self.env.company.id),('type','=','general')],limit=1)

            interbranch_payment_name = "Interbranch Payment (" + str(unit.code) + ")"
            interbranch_payment_code = "IP(" + general_journal.code + str(unit.code) + ")"
            search_interbranch_payment_journal = self.env['account.journal'].sudo().search([('name', '=', interbranch_payment_name),
                                                                                ('company_id', '=', self.env.company.id),('type','=','general')],limit=1)

            if not search_interbranch_payment_journal:
                interbrach_payment = general_journal.sudo().copy({
                    'name': interbranch_payment_name,
                    'code': interbranch_payment_code,
                    'l10n_in_gstin_partner_id': unit.gstin_id.id,
                    'is_a_default': False,
                    'company_id': self.env.company.id,
                })
                interbrach_payment.name = interbranch_payment_name
                interbrach_payment.code = interbranch_payment_code
                # interbrach_payment.alias_id.alias_name = interbrach_payment.name


class GSTINO2m(models.TransientModel):
    _name = 'gstin.o2m'

    wiz_id = fields.Many2one('gstinunit.data')
    gstin_id = fields.Many2one('res.partner',"GSTIN Unit")
    code = fields.Char("Code")

