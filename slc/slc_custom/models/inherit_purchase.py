from odoo import fields, api, models, _
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class LogisticPurchase(models.Model):
    _inherit = 'purchase.order'

    # fields for purchase order
    source_document = fields.Many2one('non.moowr',string='Source Document')
    exim_txn_category = fields.Selection(
        [('moowr', 'MOOWR'), ('import', 'Import'), ('export', 'Export')], string='Exim Txn Type')
    # exim_txn_subcategory = fields.Char(string='Exim txn subcategory')
    exim_txn_subcategory_id = fields.Many2one('exim.sub.category', string='Exim txn subcategory')
    state = fields.Selection([
        ('draft', 'EXIM Draft'),
        ('sent', 'EXIM Sent'),
        ('to approve', 'EXIM To Approve'),
        ('purchase', 'EXIM'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    unit_name = fields.Char(string='Company/Unit Name')
    mode = fields.Selection([('air', 'Air'), ('sea', 'Sea')])
    boe = fields.Char(string='BOE#')
    boe_date = fields.Date(string='BOE Date')
    erp_job_number = fields.Char(string='CB JOB Number')
    # awb_hbl = fields.Char(string='AWB/HBL')
    mawb_mbl = fields.Char(string='MAWB/MBL')
    client_ref_number = fields.Char(string='Client Ref Number')
    gross_weight = fields.Float(string='Gross Weight')
    gross_weight_uom = fields.Char(string='Gross Weight UOM')
    total_packages = fields.Integer(string='Total Packages')
    custom_stations = fields.Many2one('customs.station', string='Customs Station')
    consignor = fields.Char(string='Consignor')
    country_of_consignment = fields.Char(string='Country of consignment')
    total_duty = fields.Float(string='Total Duty')
    importer_name = fields.Char(string='Importer Name')
    foriegn_exchange_involved = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    po_bond_number_debited = fields.Many2one('bond.master', string='PD Bond number debited')
    wh_bond_number_debited = fields.Many2one('bond.master', string='WH Bond number debited')
    po_bond_debit_value = fields.Integer(string='PD Bond debit value')
    wh_bond_debit_value = fields.Integer(string='WH Bond debit value')
    provisional = fields.Boolean(string='Provisional')
    duty_under_protest = fields.Boolean(string='Duty under protest')
    duty_under_protest_amount = fields.Integer(string='Duty under protest Amount')
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    partner_id = fields.Many2one('res.partner', string='Entity', required=True, states=READONLY_STATES,
                                 change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")


    # fields for New Attachment page
    bill_of_entry = fields.Binary(string='Bill of Entry')
    awb = fields.Binary(string='AWB/HBL')
    mawb = fields.Binary(string='MAWB/MBL')
    packing_list = fields.Binary(string='Packing List')
    duty_payment_challan = fields.Binary(string='Duty Payment Challan')
    is_edit = fields.Boolean(default=False)
    is_vehicle_no = fields.Boolean(default=False)

    # One2many fields for notebook in purchase order line
    invoice_tab_ids = fields.One2many('invoice.order.line', 'invoicing_id')
    inventory_tab_ids = fields.One2many('purchase.order.line', 'inventory_tab_id')
    exim_category_connection = fields.Many2one('exim.sub.category')

    # Function to show Vehicle no field when receipt is created in transfer
    def button_confirm(self):
        self.is_vehicle_no = True
        return super(LogisticPurchase, self).button_confirm()

    # function to make fields editable on button
    def edit_only_button(self):
        self.is_edit = True

    # function to make fields readonly on button
    def readonly_button(self):
        self.is_edit = False

    # Function to show sub category of exim txn category
    @api.onchange('exim_txn_category')
    def exim_sub_category_change_according_to_category(self):
        if self.exim_txn_category:
            var = {'domain': {
                'exim_txn_subcategory_id': [('category_name', '=', self.exim_txn_category)]}}
            return var

    @api.depends('order_line')
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = (
                    max(sale.mapped('order_line.sequence') or [0]) + 1)

    max_line_sequence = fields.Integer(
        string='Max sequence in lines',
        compute='_compute_max_line_sequence',
        store=True
    )

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.order_line:
                line.sequence = current_sequence
                current_sequence += 1

    def write(self, line_values):
        res = super(LogisticPurchase, self).write(line_values)
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(LogisticPurchase,
                     self.with_context(keep_line_sequence=True)).copy(default)

    # Function to show cost record tree and form view on smart button
    def cost_record_button(self):
        tree_view_id = self.env.ref('slc_custom.view_cost_dimension_tree').id
        form_view_id = self.env.ref('slc_custom.view_cost_dimension_form').id

        return {
            'name': 'Cost Record',
            'type': 'ir.actions.act_window',
            'res_model': 'cost.dimension',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def performance_record_button(self):
        pass

    # Function to show validation if source document is duplicate, means from one BOE two EXIM cannot be created
    @api.constrains('source_document')
    def validate_boe_source_document(self):
        search_boe = self.env['purchase.order'].search([('source_document', '=', self.source_document.id), ('id', '!=', self.id)])
        if search_boe:
            raise ValidationError('BOE Source already exists')


class LogisticPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    invoice_no = fields.Char(string='Invoice No')
    lot_id = fields.Char(string='Lot/Serial Number', compute='_lot_serial_number')
    be_line_no = fields.Char(string='BE Line No')
    material_code = fields.Char(string='Material Code')
    invsno = fields.Integer(string="INVSNO", store=True)
    itemsn = fields.Integer(string="ITEMSN", store=True)
    unit = fields.Char(string='Unit')
    cth = fields.Integer(string='CTH')
    # product_id = fields.Many2one('product.product')
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 change_default=True, index='btree_not_null')
    is_edit_relate = fields.Boolean(related='order_id.is_edit')

    # fields for New Inventory page
    inventory_tab_id = fields.Many2one('purchase.order')
    linked_inventory = fields.Char(string='Linked Inventory Txn')

    # fields to hide and display only when needed for Product page
    health_cess = fields.Integer(string='Health Cess')
    nccd = fields.Integer(string='NCCD')
    acd = fields.Integer(string='ACD Amount')
    sad = fields.Integer(string='SAD Amount')
    g_cess = fields.Integer(string='G.Cess')
    add = fields.Integer(string='ADD')
    cvd = fields.Integer(string='CVD')
    sg = fields.Integer(string='SG')
    saed = fields.Integer(string='SAED')
    gsia = fields.Integer(string='GSIA')
    spexd = fields.Integer(string='SPEXD')
    chcess = fields.Integer(string='CHCESS')
    tta_amount = fields.Float(string="TTA Amount", store=True)
    cess = fields.Integer(string='Cess Amount')
    caidc = fields.Integer(string='CAIDC')
    eaidc = fields.Integer(string='EAIDC')
    cusedc = fields.Integer(string='CUSEDC')
    cushec = fields.Integer(string='CUSHEC')
    ncd = fields.Integer(string='NCD')
    aggr = fields.Integer(string='AGGR')
    tta = fields.Integer(string='TTA')

    invoice_currency = fields.Many2one('res.currency', string='Invoice Currency')
    invoice_curr = fields.Char('Invoice Currency')
    exchange_rate = fields.Integer(string='Exchange Rate')
    cif_value = fields.Integer(string='CIF Value(INR)')
    assessable_value = fields.Float(string='Assessable Value(INR)')
    basic_duty_rate = fields.Integer(string='Basic Duty Rate')
    total_basic_duty = fields.Float(string='Total Basic Duty(INR)')
    sws_rate = fields.Float(string='SWS Rate')
    sws_duty_amt = fields.Float(string='SWS Duty Amt')
    igst_rate = fields.Integer(string='IGST Rate')
    igst_amount = fields.Float(string='IGST Amount')
    total_duty = fields.Float(string='Total Duty(INR)')
    country_of_origin = fields.Char(string='Country of Origin')

    # re-defines the field to change the default
    sequence = fields.Integer(
        help="Gives the sequence of this line when displaying the sale order.",
        default=9999,
        string="Sequence"
    )

    # displays sequence on the order line
    sequence2 = fields.Integer(
        help="Shows the sequence of this line in the sale order.",
        related='sequence',
        string="Line Number",
        readonly=True,
        store=True
    )

    @api.model
    def create(self, values):
        line = super(LogisticPurchaseOrderLine, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get('keep_line_sequence'):
            line.order_id._reset_sequence()
            print(line.order_id, 'order id')
        return line

    # Function to create lot/serial number on the basis of BOE date, BOE No, Invoice Number and Item serial number
    @api.depends('order_id.boe', 'order_id.boe_date', 'invsno', 'itemsn')
    def _lot_serial_number(self):
        for rec in self:
            rec.lot_id = f"{rec.order_id.boe_date}#{rec.order_id.boe}#{rec.invsno}#{rec.itemsn}"
            return rec

    # Function to show additional fields of product line on additional fields button
    def view_order_line(self):
        return {
            'name': "Order Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'view_id': self.env.ref('slc_custom.order_line_view_form').id,
            'res_id': self.id,
            'target': 'new',
        }

    # Function to through validation if BE Line number is not filled,
    # and also through validation if BE Line number is duplicate
    @api.constrains('be_line_no')
    def validate_boe_line_number(self):
        if self.be_line_no == False:
            raise ValidationError(_('Please Fill BE Line Number'))
        search_be_line_no = self.env['purchase.order.line'].search([('be_line_no', '=', self.be_line_no), ('id', '!=', self.id)])
        if search_be_line_no:
            raise ValidationError(_('This BE Line Number already exists'))


class InvoiceOrderLine(models.Model):
    _name = 'invoice.order.line'

    invoicing_id = fields.Many2one('purchase.order')
    order_id = fields.Many2one('sale.order')

    # fields for New Invoice page
    invsno = fields.Integer(string='Inv SNO')
    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Char(string='Invoice Date')
    supplier = fields.Char(string='Consignor/Supplier')
    inco_terms = fields.Char(string='Inco Terms')
    invoice_total = fields.Float(string='Invoice Total (Cur)')
    invoice_cur = fields.Char(string='Invoice Currency')
    invoice_amount = fields.Float(string='Invoice Amoutn(INR)')
    related_party = fields.Char(string='Whether Related Party')
    invoice_attachment = fields.Char(string='Invoice Attachment')

    is_edit_only = fields.Boolean(related="invoicing_id.is_edit")
