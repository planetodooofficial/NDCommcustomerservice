from odoo import api, fields, models

class GSTRReconciliation(models.Model):
    _name = "gstr.reconciliation"
    _description = "Reconciliation Tool"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reconciliation')
    from_period_id = fields.Many2one(
        'account.period', string='From Period')

    to_period_id = fields.Many2one(
        'account.period', string='To Period')

    journal_id = fields.Many2one('account.journal',required=True)

    reconciled_moves = fields.One2many('reconciled.move.line','gstr_reco_id',copy=False)
    odoo_missing_moves = fields.One2many('odoo.missing.move.line','gstr_reco_id',copy=False)
    file_missing_moves = fields.One2many('file.missing.move.line','gstr_reco_id',copy=False)
    # partial_matched_moves = fields.One2many('partial.matched.move.line','gstr_reco_id')

    select_p_inv = fields.Integer(string='Total Selected Period Invoice', compute='compute_reconcilliation_count',readonly=True)
    reconciled_inv = fields.Integer(string='Total Reconciled Invoice', compute='compute_reconcilliation_count',readonly=True)
    missing_odoo = fields.Integer(string='Total Missing In Odoo', compute='compute_reconcilliation_count',readonly=True)
    missing_file = fields.Integer(string='Total Missing In File', compute='compute_reconcilliation_count',readonly=True)
    partial_matched = fields.Integer(string='Total Partial Matched', readonly=True)

    reco_type = fields.Selection([('gstr1',"GSTR1"),('gstr2',"GSTR2"),('gstr3',"GSTR3")])
    file_data = fields.Binary("File")

    @api.depends('reconciled_moves','odoo_missing_moves','file_missing_moves')
    def compute_reconcilliation_count(self):
        for rec in self:
            reconciled_inv_len = len(rec.reconciled_moves) or 0
            missing_odoo_len = len(rec.odoo_missing_moves) or 0
            missing_file_len = len(rec.file_missing_moves) or 0
            rec.reconciled_inv = reconciled_inv_len
            rec.missing_odoo = missing_odoo_len
            rec.missing_file = missing_file_len
            rec.select_p_inv = reconciled_inv_len + missing_file_len + missing_odoo_len

class ReconciledMovesLine(models.Model):
    _name = 'reconciled.move.line'

    inv_date = fields.Date("Invoice Date")
    move_id = fields.Many2one('account.move',"Invoice")
    partner_id = fields.Many2one('res.partner',"Vendor")
    inv_amt = fields.Float(string='Invoice Amount')
    state = fields.Selection(selection=[('draft', 'Draft'),('posted', 'Posted'),('cancel', 'Cancelled')],string='Status')
    move_type = fields.Selection(selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),],string='Type')
    invoice_type = fields.Selection([
        ('b2b', 'B2B'),
        ('b2cl', 'B2CL'),
        ('b2cs', 'B2CS'),
        ('b2bur', 'B2BUR'),
        ('import', 'IMPS/IMPG'),
        ('export', 'Export'),
        ('cdnr', 'CDNR'),
        ('cdnur', 'CDNUR'),
    ],string='Invoice Type')
    currency_id = fields.Many2one('res.currency',string='Currency')
    file_date = fields.Date(string='File Date')
    file_invoice = fields.Char(string='File Invoice')
    file_vendor = fields.Char(string='File Vendor')
    file_amt = fields.Float(string='File Amount')
    diff_amt = fields.Float(string='Difference Amount')

    gstr_reco_id = fields.Many2one('gstr.reconciliation')

class OdooMissingMoveLine(models.Model):
    _name = 'odoo.missing.move.line'

    inv_date = fields.Date("Invoice Date")
    move_id = fields.Many2one('account.move', "Invoice")
    partner_id = fields.Many2one('res.partner', "Vendor")

    file_date = fields.Date(
        string='File Date')
    file_invoice = fields.Char(
        string='File Invoice')
    file_vendor = fields.Char(
        string='File Vendor')
    file_amt = fields.Float(
        string='File Amount')
    inv_amt = fields.Float(
        string='Invoice Amount')
    diff_amt = fields.Float(
        string='Difference Amount')

    gstr_reco_id = fields.Many2one('gstr.reconciliation')

class FileMissingMoveLine(models.Model):
    _name = 'file.missing.move.line'

    inv_date = fields.Date("Invoice Date")
    move_id = fields.Many2one('account.move', "Invoice")
    partner_id = fields.Many2one('res.partner', "Vendor")
    inv_amt = fields.Float(string='Invoice Amount')
    state = fields.Selection(selection=[('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled')],
                             string='Status')
    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'), ], string='Type')
    invoice_type = fields.Selection([
        ('b2b', 'B2B'),
        ('b2cl', 'B2CL'),
        ('b2cs', 'B2CS'),
        ('b2bur', 'B2BUR'),
        ('import', 'IMPS/IMPG'),
        ('export', 'Export'),
        ('cdnr', 'CDNR'),
        ('cdnur', 'CDNUR'),
    ],string='Invoice Type')
    currency_id = fields.Many2one('res.currency', string='Currency')
    # file_date = fields.Date(
    #     string='File Date')
    # file_invoice = fields.Char(
    #     string='File Invoice')
    # file_vendor = fields.Char(
    #     string='File Vendor')
    # file_amt = fields.Float(
    #     string='File Amount')
    # diff_amt = fields.Float(
    #     string='Difference Amount')

    gstr_reco_id = fields.Many2one('gstr.reconciliation')




