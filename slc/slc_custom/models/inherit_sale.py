from odoo import fields, api, models
from odoo.exceptions import UserError, ValidationError

class LogisticSale(models.Model):
    _inherit = 'sale.order'

    receipt_id = fields.Many2one('stock.picking')
    exim_txn_category = fields.Selection(
        [('moowr', 'MOOWR'), ('import', 'Import'), ('export', 'Export')], string='Exim Txn Type')
    exim_txn_subcategory_id = fields.Many2one('exim.sub.category', string='Exim txn subcategory')
    mode = fields.Selection([('air', 'Air'), ('sea', 'Sea')])
    boe = fields.Char(string='BOE#')
    boe_date = fields.Date(string='BOE Date')
    erp_job_number = fields.Char(string='ERP Job number')
    inventory_interface = fields.Many2one('stock.picking')
    is_sale = fields.Boolean(default=False)

    # fields for New Attachment page
    bill_of_entry = fields.Binary(string='Bill of Entry')
    awb = fields.Binary(string='AWB/HBL')
    mawb = fields.Binary(string='MAWB/MBL')
    packing_list = fields.Binary(string='Packing List')
    duty_payment_challan = fields.Binary(string='Duty Payment Challan')

    # One2many fields for notebook in purchase order line
    invoice_tab_ids = fields.One2many('invoice.order.line', 'order_id')

    # inventory_tab_ids = fields.One2many('purchase.order.line', 'inventory_tab_id')

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

    @api.onchange('exim_txn_category')
    def exim_sub_category_change_according_to_category(self):
        if self.exim_txn_category:
            var = {'domain': {
                'exim_txn_subcategory_id': [('category_name', '=', self.exim_txn_category)]}}
            return var

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.order_line:
                line.sequence = current_sequence
                current_sequence += 1

    def write(self, line_values):
        res = super(LogisticSale, self).write(line_values)
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(LogisticSale,
                     self.with_context(keep_line_sequence=True)).copy(default)

    # Function to create receipt only when the selection is MOOWR
    # def action_confirm(self):
    #     for rec in self:
    #         if rec.receipt_id.picking_type_code == 'incoming' or rec.receipt_id.picking_type_code == 'outgoing':
    #             self.env['stock.picking'].sudo().create({
    #                 'picking_type_id': rec.picking_type_id.id,
    #             })
    #     return super(LogisticSale, self).action_confirm()

    def action_confirm(self):
        for rec in self:
            if rec.receipt_id.state == 'cancel':
                raise ValidationError('Move of this Sale order is Cancelled')
            if self.is_sale == True:
                self.state = 'sale'
                return False
        return super(LogisticSale, self).action_confirm()


class LogisticSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # field for Product page
    invoice_no = fields.Char(string='Invoice No')
    be_line_no = fields.Char(string='BE Line No')
    lot_id = fields.Char(string='Lot/Serial Number')
    sequence_no = fields.Integer(string='Sr no.')
    material_code = fields.Char(string='Material Code')
    unit = fields.Char(string='Unit')
    cth = fields.Char(string='CTH')

    # fields for New Inventory page
    inventory_tab_id = fields.Many2one('purchase.order')
    linked_inventory = fields.Char(string='Linked Inventory Txn')

    # fields to hide and display only when needed for Product page
    health_cess = fields.Char(string='Health Cess')
    nccd = fields.Char(string='NCCD')
    acd = fields.Char(string='ACD')
    sad = fields.Char(string='SAD')
    g_cess = fields.Char(string='G.Cess')
    add = fields.Char(string='ADD')
    cvd = fields.Char(string='CVD')
    sg = fields.Char(string='SG')
    saed = fields.Char(string='SAED')
    gsia = fields.Char(string='GSIA')
    spexd = fields.Char(string='SPEXD')
    chcess = fields.Char(string='CHCESS')
    cess = fields.Char(string='Cess')
    caidc = fields.Char(string='CAIDC')
    eaidc = fields.Char(string='EAIDC')
    cusedc = fields.Char(string='CUSEDC')
    cushec = fields.Char(string='CUSHEC')
    ncd = fields.Char(string='NCD')
    aggr = fields.Char(string='AGGR')

    invoice_currency = fields.Char(string='Invoice Currency')
    exchange_rate = fields.Char(string='Exchange Rate')
    cif_value = fields.Char(string='CIF Value(INR)')
    assessable_value = fields.Char(string='Assessable Value(INR)')
    basic_duty_rate = fields.Char(string='Basic Duty Rate')
    total_basic_duty = fields.Float(string='Total Basic Duty(INR)')
    sws_rate = fields.Char(string='SWS Rate')
    sws_duty_amt = fields.Char(string='SWS Duty Amt')
    igst_rate = fields.Char(string='IGST Rate')
    igst_amount = fields.Char(string='IGST Amount')
    total_duty = fields.Char(string='Total Duty(INR)')
    country_of_origin = fields.Char(string='Country of Origin')
    purchase_order_line_connection = fields.Many2one('stock.move')
    invsno = fields.Integer(string="INVSNO")
    itemsn = fields.Integer(string="ITEMSN")

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

    def view_order_line(self):
        return {
            'name': "Order Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'view_id': self.env.ref('slc_custom.sale_order_line_view_form').id,
            'res_id': self.id,
            'target': 'new',
        }

    @api.model
    def create(self, values):
        line = super(LogisticSaleOrderLine, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get('keep_line_sequence'):
            line.order_id._reset_sequence()
        return line
