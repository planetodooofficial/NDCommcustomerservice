from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ReconciliationTool(models.Model):
    _name = "reconciliation.tool"
    _description = "Reconciliation Tool"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reconciliation')
    from_period_id = fields.Many2one(
        'account.period', string='From Period')

    to_period_id = fields.Many2one(
        'account.period', string='To Period')

    journal_id = fields.Many2one('account.journal')

    reconciliation_partial_line_ids = fields.One2many('reconciliation.tool.partial.line', 'reconciliation_id', 'Reconciliation Partial Matched Line')
    reconciliation_missing_odoo_line_ids = fields.One2many('reconciliation.tool.missing.odoo.line', 'reconciliation_id', 'Reconciliation Missing Odoo Line')

    invoice_lines = fields.Many2many('account.move', 'reconciliation_account_invoice', 'reconciliation_id', 'account_inv_id',
                                     string='Vendor Invoices', help="Invoices belong to selected period.")
    missing_in_file_invoice_lines = fields.Many2many('account.move', 'missing_in_file_account_invoice', 'reconciliation_id',
                                     'account_inv_id',
                                     string='Missing In File Invoices', help="Invoices belong to selected period.")

    select_p_inv = fields.Integer(string='Total Selected Period Invoice', store=True, readonly=True, compute='_compute_total')
    reconciled_inv = fields.Integer(string='Total Reconciled Invoice', store=True, readonly=True, compute='_compute_total')
    missing_odoo = fields.Integer(string='Total Missing In Odoo', store=True, readonly=True, compute='_compute_total')
    missing_file = fields.Integer(string='Total Missing In File', store=True, readonly=True, compute='_compute_total')
    partial_matched = fields.Integer(string='Total Partial Matched', store=True, readonly=True, compute='_compute_total')

    @api.depends('invoice_lines','missing_in_file_invoice_lines', 'reconciliation_partial_line_ids','reconciliation_missing_odoo_line_ids',)
    def _compute_total(self):
        for reconciliation in self:
            reconciliation.select_p_inv = len(reconciliation.invoice_lines)
            reconciliation.reconciled_inv =len(reconciliation.invoice_lines.filtered(lambda i: i.reconciled == True))
            reconciliation.missing_odoo =len(reconciliation.reconciliation_missing_odoo_line_ids)
            reconciliation.missing_file =len(reconciliation.missing_in_file_invoice_lines)
            reconciliation.partial_matched =len(reconciliation.reconciliation_partial_line_ids)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('reconciliation.tool')
        return super(ReconciliationTool, self).create(vals)

    def getInvoiceObjs(self, extrafilter=[], invoiceType=[]):
        invoiceObjs = self.env['account.move']
        gstObjs = self.search(extrafilter)
        invoiceIds = gstObjs and gstObjs.mapped(
            'invoice_lines') and gstObjs.mapped('invoice_lines').ids or []
        if self.from_period_id and self.to_period_id:
            filter = ['|',
                      '&', '&', ('move_type', 'in', ['out_invoice', 'out_refund']),
                      ('invoice_date', '>=', self.from_period_id.date_start),
                      ('invoice_date', '<=', self.to_period_id.date_stop),
                      '&', '&', ('move_type', 'in', ['in_invoice', 'in_refund']),
                      ('date', '>=', self.from_period_id.date_start),
                      ('date', '<=', self.to_period_id.date_stop),
                      ('gst_status', '=', 'not_uploaded'),
                      ('move_type', 'in', invoiceType),
                      ('journal_id', '=', self.journal_id.id),
                      ('state', 'in', ['posted']),
                      ]
            if self.from_period_id.date_start > self.to_period_id.date_stop:
                raise UserError(
                    "End date should greater than or equal to starting date")
            if invoiceIds:
                filter.append(('id', 'not in', invoiceIds))
            invoiceObjs = invoiceObjs.search(filter)
        return invoiceObjs

    def fetchSupplierInvoices(self):
        filter = [('id', '!=', self.id)]
        invoiceObjs = self.getInvoiceObjs(filter, ['in_invoice', 'in_refund'])
        # self.invoice_lines = [(6, 0, invoiceObjs.ids)]
        return invoiceObjs

# add new class for domain not working
class ReconciliationToolPartialLine(models.Model):
    _name = "reconciliation.tool.partial.line"
    _description = "Reconciliation Tool Partial Matched Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    linked_date = fields.Date(
        string='Linked Date')
    linked_invoice_id = fields.Many2one(
        'account.move', string='Linked Invoiced')
    linked_vendor_id = fields.Many2one(
        'res.partner', string='Linked Vendor')

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

    reconciliation_id = fields.Many2one('reconciliation.tool', string='Reconciliation Invoiced')

    @api.onchange('linked_invoice_id')
    def onchange_linked_invoice(self):
        if self.linked_invoice_id:
            self.linked_date = self.linked_invoice_id.date
            self.linked_vendor_id = self.linked_invoice_id.partner_id.id
            self.inv_amt = self.linked_invoice_id.amount_total
            self.diff_amt = self.inv_amt  - self.file_amt

    def action_reconcile_recorde(self):
        if not self.linked_invoice_id:
            raise UserError("Plese Select Linked Invoice")
        self.linked_invoice_id.write({'reconciled': True})
        self.unlink()
        return True


class ReconciliationToolMissingOdooLine(models.Model):
    _name = "reconciliation.tool.missing.odoo.line"
    _description = "Reconciliation Tool Missing Odoo Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    linked_date = fields.Date(
        string='Linked Date')
    linked_invoice_id = fields.Many2one(
        'account.move', string='Linked Invoiced')
    linked_vendor_id = fields.Many2one(
        'res.partner', string='Linked Vendor')

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

    reconciliation_id = fields.Many2one('reconciliation.tool', string='Reconciliation Invoiced')

    @api.onchange('linked_invoice_id')
    def onchange_linked_invoice(self):
        if self.linked_invoice_id:
            self.linked_date = self.linked_invoice_id.date
            self.linked_vendor_id = self.linked_invoice_id.partner_id.id
            self.inv_amt = self.linked_invoice_id.amount_total
            self.diff_amt = self.inv_amt  - self.file_amt

    def action_reconcile_recorde(self):
        if not self.linked_invoice_id:
            raise UserError("Plese Select Linked Invoice")
        self.linked_invoice_id.write({'reconciled': True})
        self.unlink()
        return True
