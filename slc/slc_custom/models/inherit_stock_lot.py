from odoo import models, api, fields, _
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError


class InheritStockLot(models.Model):
    _inherit = 'stock.lot'

    source_document = fields.Many2one('purchase.order', string='Source Document', readonly=False)
    product_qty = fields.Float('Quantity', compute='_product_qty', readonly=False)
    boe_source_document = fields.Many2one('non.moowr', string= 'BOE Source Document', readonly=False)
    date = fields.Date(string='Date')
    customer_ref = fields.Char(string='Customer Reference', readonly=True)
    health_cess = fields.Float(string='Health Cess', digits=(12, 4), readonly=True)
    nccd = fields.Float(string='NCCD', digits=(12, 4), readonly=True)
    acd = fields.Float(string='ACD', digits=(12, 4), readonly=True)
    sad = fields.Float(string='SAD', digits=(12, 4), readonly=True)
    g_cess = fields.Float(string='G.Cess', digits=(12, 4), readonly=True)
    add = fields.Float(string='ADD', digits=(12, 4), readonly=True)
    cvd = fields.Float(string='CVD', digits=(12, 4), readonly=True)
    sg = fields.Float(string='SG', digits=(12, 4), readonly=True)
    saed = fields.Float(string='SAED', digits=(12, 4), readonly=True)
    gsia = fields.Float(string='GSIA', digits=(12, 4), readonly=True)
    spexd = fields.Float(string='SPEXD', digits=(12, 4), readonly=True)
    chcess = fields.Float(string='CHCESS', digits=(12, 4), readonly=True)
    cess = fields.Float(string='Cess', digits=(12, 4), readonly=True)
    caidc = fields.Float(string='CAIDC', digits=(12, 4), readonly=True)
    eaidc = fields.Float(string='EAIDC', digits=(12, 4), readonly=True)
    cusedc = fields.Float(string='CUSEDC', digits=(12, 4), readonly=True)
    cushec = fields.Float(string='CUSHEC', digits=(12, 4), readonly=True)
    ncd = fields.Float(string='NCD', digits=(12, 4), readonly=True)
    aggr = fields.Float(string='AGGR', digits=(12, 4), readonly=True)
    invsno = fields.Integer(string="INVSNO", readonly=False)
    itemsn = fields.Integer(string="ITEMSN", readonly=False)

    invoice_currency = fields.Many2one('res.currency', string='Invoice Currency', readonly=True)
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 4), readonly=True)
    cif_value = fields.Float(string='CIF Value(INR)', digits=(12, 4), readonly=True)
    assessable_value = fields.Float(string='Assessable Value(INR)', digits=(12, 4), readonly=True)
    basic_duty_rate = fields.Float(string='Basic Duty Rate', digits=(12, 4), readonly=True)
    total_basic_duty = fields.Float(string='Total Basic Duty(INR)', digits=(12, 4), readonly=True)
    sws_rate = fields.Float(string='SWS Rate', digits=(12, 4), readonly=True)
    sws_duty_amt = fields.Float(string='SWS Duty Amt', digits=(12, 4), readonly=True)
    igst_rate = fields.Float(string='IGST Rate', digits=(12, 4), readonly=True)
    igst_amount = fields.Float(string='IGST Amount', digits=(12, 4), readonly=True)
    total_duty = fields.Float(string='Total Duty(INR)', digits=(12, 4), readonly=True)
    country_of_origin = fields.Char(string='Country of Origin', readonly=True)


class InheritStockLocation(models.Model):
    _inherit = 'stock.location'

    is_production_location = fields.Boolean(default=False, string='Is Production Location')
    is_virtual_location = fields.Boolean(default=False, string='Virtual Location')


class InheritStockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_fg = fields.Boolean(default=False, string="Is FG")
    is_so = fields.Boolean(default=False, string="Create Multiple Sale Order")
    is_single_so = fields.Boolean(default=False, string="Create Single Sale Order")

    @api.constrains('is_so', 'is_single_so')
    def validate_sale_order_button(self):
        if self.is_so == True and self.is_single_so == True:
            raise ValidationError('Only one can be selected from create single and multiple sale order')




class InheritStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True,
                                       compute="_compute_location_id", store=True, readonly=False, precompute=True)

    move_id = fields.Many2one(
        'stock.move', 'Stock Operation',
        check_company=True, index=True)
    lot_name = fields.Char(related='move_id.lot_id', string='Lot/Serial Number Name')

    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure', required=False, domain="[('category_id', '=', product_uom_category_id)]",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True, )

    def _create_and_assign_production_lot(self):
        """ Creates and assign new production lots for move lines."""
        lot_vals = []
        # It is possible to have multiple time the same lot to create & assign,
        # so we handle the case with 2 dictionaries.
        key_to_index = {}  # key to index of the lot
        key_to_mls = defaultdict(lambda: self.env['stock.move.line'])  # key to all mls
        for ml in self:

            key = (ml.company_id.id, ml.product_id.id, ml.lot_name)
            key_to_mls[key] |= ml
            if ml.tracking != 'lot' or key not in key_to_index:
                key_to_index[key] = len(lot_vals)
                lot_no_details = {
                    'nccd': ml.move_id.nccd
                }
                print(ml.move_id.purchase_line_id.order_id, 'nccd')
                a = ml._get_value_production_lot()
                a['source_document'] = ml.move_id.purchase_line_id.order_id.id
                a['boe_source_document'] = ml.move_id.purchase_line_id.order_id.source_document.id
                a['invsno'] = ml.move_id.invsno
                a['itemsn'] = ml.move_id.itemsn
                a['health_cess'] = ml.move_id.health_cess
                a['nccd'] = ml.move_id.nccd
                a['acd'] = ml.move_id.acd
                a['sad'] = ml.move_id.sad
                a['g_cess'] = ml.move_id.g_cess
                a['add'] = ml.move_id.add
                a['cvd'] = ml.move_id.cvd
                a['sg'] = ml.move_id.sg
                a['saed'] = ml.move_id.saed
                a['gsia'] = ml.move_id.gsia
                a['spexd'] = ml.move_id.spexd
                a['chcess'] = ml.move_id.chcess
                a['cess'] = ml.move_id.cess
                a['caidc'] = ml.move_id.caidc
                a['eaidc'] = ml.move_id.eaidc
                a['cusedc'] = ml.move_id.cusedc
                a['cushec'] = ml.move_id.cushec
                a['ncd'] = ml.move_id.ncd
                a['aggr'] = ml.move_id.aggr
                a['invoice_currency'] = ml.move_id.invoice_currency
                a['exchange_rate'] = ml.move_id.exchange_rate
                a['cif_value'] = ml.move_id.cif_value
                a['assessable_value'] = ml.move_id.assessable_value
                a['basic_duty_rate'] = ml.move_id.basic_duty_rate
                a['total_basic_duty'] = ml.move_id.total_basic_duty
                a['sws_rate'] = ml.move_id.sws_rate
                a['sws_duty_amt'] = ml.move_id.sws_duty_amt
                a['igst_rate'] = ml.move_id.igst_rate
                a['igst_amount'] = ml.move_id.igst_amount
                a['total_duty'] = ml.move_id.total_duty
                a['country_of_origin'] = ml.move_id.country_of_origin

                lot_vals.append(a)
        lots = self.env['stock.lot'].create(lot_vals)
        for key, mls in key_to_mls.items():
            lot = lots[key_to_index[key]].with_prefetch(
                lots._ids)  # With prefetch to reconstruct the ones broke by accessing by index
            mls.write({'lot_id': lot.id})

    @api.model_create_multi
    def create(self, values):
        res = super(InheritStockMoveLine, self).create(values)
        for line in res:
            # If the line is added in a done production, we need to map it
            # manually to the produced move lines in order to see them in the
            # traceability report
            if line.move_id.raw_material_production_id and line.state == 'done':
                mo = line.move_id.raw_material_production_id
                finished_lots = mo.lot_producing_id
                finished_lots |= mo.move_finished_ids.filtered(
                    lambda m: m.product_id != mo.product_id).move_line_ids.lot_id
                if finished_lots:
                    produced_move_lines = mo.move_finished_ids.move_line_ids.filtered(
                        lambda sml: sml.lot_id in finished_lots)
                    line.produce_line_ids = [(6, 0, produced_move_lines.ids)]
                else:
                    produced_move_lines = mo.move_finished_ids.move_line_ids
                    line.produce_line_ids = [(6, 0, produced_move_lines.ids)]
        return res

