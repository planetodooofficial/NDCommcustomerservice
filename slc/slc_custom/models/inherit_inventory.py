from odoo import fields, api, models
from odoo.exceptions import UserError, ValidationError


class InventoryProductPicking(models.Model):
    _inherit = 'stock.picking'

    is_so = fields.Boolean(default=False, compute='compute_so_creation')  # Create Multiple sale order boolean button
    is_single_so = fields.Boolean(default=False,
                                  compute='compute_single_so_creation')  # Create Multiple sale order boolean button
    manufacturing_fg_ids = fields.One2many('stock.move', 'manufacturing_fg_id')
    manufacturing_component_ids = fields.One2many('component.stock.move', 'component_id')
    finished_good_connection = fields.Boolean(string="FG", related='picking_type_id.finished_goods')
    sale_order_id = fields.Many2one('sale.order')
    sale_count = fields.Integer(compute='_compute_sale_order_count')
    sale_single_count = fields.Integer(compute='_compute_single_sale_order_count')
    component_stock_move = fields.Many2one('stock.move')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)]})
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        compute="_compute_location_id", store=True, precompute=True, readonly=False,
        check_company=True, required=True,
        states={'done': [('readonly', True)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        compute="_compute_location_id", store=True, precompute=True, readonly=False,
        check_company=True, required=True,
        states={'done': [('readonly', True)]})
    name = fields.Char(
        'Reference', default='/',
        copy=False, index='trigram', readonly=True)
    is_sale_button = fields.Boolean(default=False)
    is_validate = fields.Boolean(default=False)
    is_validate_multiple = fields.Boolean(default=False)
    is_single_sale_button = fields.Boolean(default=False)
    is_vehicle_details = fields.Boolean(default=False, related="purchase_id.is_vehicle_no")
    is_check_availabilty = fields.Boolean(default=False)
    is_set_quantities = fields.Boolean(default=False)

    new_vehicle_otl_details = fields.Text(string="Vehicle/OTL Details")
    is_vehicle = fields.Boolean(related='picking_type_id.vehicle_otl_details')

    delivery_challan = fields.Text(string="Delivery Challan")
    gstin_of_consignee = fields.Text(string="GST Of Consignee")
    is_delivery = fields.Boolean(related='picking_type_id.delivery_challan_details')

    gst_invoice_no = fields.Text(string="GST Invoice No.")
    gst_invoice_date = fields.Date(string="GST Invoice Date")
    sgst_tax_paid_amount = fields.Float(string="SGST Tax paid amount")
    cgst_tax_paid_amount = fields.Float(string="CGST Tax paid amount")
    igst_tax_paid_amount = fields.Float(string="IGST Tax paid amount")
    gst_comp_cess_paid_amount = fields.Float(string="GST Comp. Cess paid amount")
    is_sale = fields.Boolean(related='picking_type_id.sale_invoice_details')

    shipping_bill_no = fields.Text(string='Shipping Bill No.')
    shipping_bill_date = fields.Date(string='Shipping Bill Date')
    assessable_value = fields.Float(string='Assessable Value INR')
    export_duty_value = fields.Date(string='Export Duty Value INR')
    is_export = fields.Boolean(related='picking_type_id.export_details')

    def action_confirm(self):
        self._check_company()
        self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
        for rec in self.move_ids:
            rec.location_dest_id = rec.picking_id.location_dest_id
        # call `_action_confirm` on every draft move
        self.move_ids.filtered(lambda move: move.state == 'draft')._action_confirm()
        # run scheduler for moves forecasted to not have enough in stock
        self.move_ids.filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))._trigger_scheduler()
        return True

    # function to count the sale order created from create multiple sale order button transfer
    def _compute_sale_order_count(self):
        for rec in self:
            sale_count = self.env['sale.order'].search_count([('receipt_id', '=', rec.id)])
            rec.sale_count = sale_count

    # function to count the sale order created from create single sale order button transfer
    def _compute_single_sale_order_count(self):
        for rec in self:
            sale_single_count = self.env['sale.order'].search_count([('receipt_id', '=', rec.id)])
            rec.sale_single_count = sale_single_count

    # function to make button create multiple sale order visible
    @api.depends('picking_type_id')
    def compute_so_creation(self):
        for rec in self:
            if rec.picking_type_id.is_so:
                rec.is_so = True
            else:
                rec.is_so = False

    # @api.depends('picking_type_id')
    # def _compute_additional_information_vehicle(self):
    #     for rec in self:
    #         if rec.picking_type_id.vehicle_otl_details:
    #             rec.is_vehicle = True

    # @api.depends('picking_type_id')
    # def _compute_additional_information_delivery(self):
    #     for rec in self:
    #         if rec.picking_type_id.delivery_challan_details:
    #             rec.is_delivery = True
    #
    # @api.depends('picking_type_id')
    # def _compute_additional_information_sale(self):
    #     for rec in self:
    #         if rec.picking_type_id.sale_invoice_details:
    #             rec.is_sale = True
    #
    # @api.depends('picking_type_id')
    # def _compute_additional_information_export(self):
    #     for rec in self:
    #         if rec.picking_type_id.export_details:
    #             rec.is_export = True

    # function to make button single multiple sale order visible
    @api.depends('picking_type_id')
    def compute_single_so_creation(self):
        for rec in self:
            if rec.picking_type_id.is_single_so:
                rec.is_single_so = True
            else:
                rec.is_single_so = False

    # Inherited set quantities function and added validation if FG serial number in FG tab and detailed operation is
    # different
    def action_set_quantities_to_reservation(self):
        res = super(InventoryProductPicking, self).action_set_quantities_to_reservation()
        self.is_set_quantities = True
        for rec in self.manufacturing_fg_ids:
            record = self.move_ids_without_package.filtered(
                lambda x: x.product_id.id == rec.manufacturing_product_id.id)
            if record:
                if rec.lot_producing_id.name != record.lot_ids.name:
                    raise ValidationError("FG Serial Number of operation is not matching with FG tab")
        return res

    # Function to create multiple sale order on the basis of BOE
    def create_multiple_sale_order(self):
        # if not self.is_check_availabilty:
        #     raise ValidationError("Please check availability of the product first!")
        move_lot_ids = self.move_ids_without_package.mapped('lot_ids')  # In this we will get lot ids of move product
        # lot_boe_ids = [lot.source_document.source_document.id for lot in move_lot_ids]  # list comprehension is used to get list of all BOE id
        boe_ids = self.env['non.moowr'].search([('id', 'in', [lot.source_document.source_document.id
                                                              for lot in move_lot_ids])])
        for records in self.move_ids_without_package:
            if records.reserved_availability != records.product_uom_qty:
                raise ValidationError("Product is not reserved means not in stock")
        if not self.is_set_quantities:
            raise ValidationError("Please set quantities first!")
        for rec in boe_ids:
            if rec.order_line:
                so_details = {
                    'partner_id': self.partner_id.id,
                    'receipt_id': self.id,
                    'inventory_interface': self.id
                }
                line_item = []
                boe_order_line_ids = rec.order_line.mapped('product_id.id')
                move_ids = self.move_ids_without_package.filtered(lambda x: x.product_id.id in boe_order_line_ids)
                # comp_id = None
                for move in move_ids:
                    print([lot.name for lot in move.lot_ids])
                    lot_id = self.env['stock.lot'].search(
                        ['|', ('name', '=', move.lot_id), ('name', 'in', [lot.name for lot in move.lot_ids]),
                         ('product_id', '=', move.product_id.id)], limit=1)
                    comp_id = self.env['mrp.production'].search(
                        [('product_id', '=', move.product_id.id)])
                    if not comp_id:
                        so_line_item = (0, 0, {
                            'product_id': move.product_id.id,
                            'invoice_no': move.invoice_no,
                            'be_line_no': move.be_line_no,
                            'material_code': move.material_code,
                            'product_uom_qty': move.quantity_done,
                            'invsno': move.invsno,
                            'itemsn': move.itemsn,
                            'unit': move.unit,
                            'cth': move.cth,
                            # for lot number data
                            'lot_id': move.lot_id or move.lot_ids.name,
                            'health_cess': lot_id.health_cess * move.quantity_done,
                            'acd': lot_id.acd * move.quantity_done,
                            'sad': lot_id.sad * move.quantity_done,
                            'g_cess': lot_id.g_cess * move.quantity_done,
                            'add': lot_id.add * move.quantity_done,
                            'cvd': lot_id.cvd * move.quantity_done,
                            'sg': lot_id.sg * move.quantity_done,
                            'saed': lot_id.saed * move.quantity_done,
                            'gsia': lot_id.gsia * move.quantity_done,
                            'spexd': lot_id.spexd * move.quantity_done,
                            'chcess': lot_id.chcess * move.quantity_done,
                            'cess': lot_id.cess * move.quantity_done,
                            'caidc': lot_id.caidc * move.quantity_done,
                            'eaidc': lot_id.eaidc * move.quantity_done,
                            'cusedc': lot_id.cusedc * move.quantity_done,
                            'cushec': lot_id.cushec * move.quantity_done,
                            'ncd': lot_id.ncd * move.quantity_done,
                            'aggr': lot_id.aggr * move.quantity_done,
                            'invoice_currency': lot_id.invoice_currency,
                            'exchange_rate': lot_id.exchange_rate * move.quantity_done,
                            'cif_value': lot_id.cif_value * move.quantity_done,
                            'assessable_value': lot_id.assessable_value * move.quantity_done,
                            'basic_duty_rate': lot_id.basic_duty_rate * move.quantity_done,
                            'total_basic_duty': lot_id.total_basic_duty * move.quantity_done,
                            'sws_rate': lot_id.sws_rate * move.quantity_done,
                            'sws_duty_amt': lot_id.sws_duty_amt * move.quantity_done,
                            'igst_rate': lot_id.igst_rate * move.quantity_done,
                            'igst_amount': lot_id.igst_amount * move.quantity_done,
                            'total_duty': lot_id.total_duty * move.quantity_done,
                            'country_of_origin': lot_id.country_of_origin
                        })
                        line_item.append(so_line_item)
                # if not comp_id:
                sale_id = self.env['sale.order'].create(so_details)
                sale_id.write({'order_line': line_item})
                self.is_sale_button = True
                self.sale_order_id.is_sale = True
                self.is_validate_multiple = True

    # Function to create single sale order
    def create_single_sale_order(self):
        # if self.is_check_availabilty == False:
        #     raise ValidationError("Please check availability of the product first!")
        for records in self.move_ids_without_package:
            if records.reserved_availability != records.product_uom_qty:
                raise ValidationError("Product is not reserved means not in stock")
        if self.is_set_quantities == False:
            raise ValidationError("Please set quantities first!")
        sale_order = self.env['sale.order']
        line_item = []
        so_details = {}
        for move in self.move_ids_without_package:
            lot_id = self.env['stock.lot'].search(
                ['|', ('name', '=', move.lot_id), ('name', '=', move.lot_ids.name),
                 ('product_id', '=', move.product_id.id)])
            comp_id = self.env['mrp.production'].search(
                [('product_id', '=', move.product_id.id)])
            if not comp_id:
                so_details = {
                    'partner_id': self.partner_id.id,
                    'receipt_id': self.id,
                    'inventory_interface': self.id
                }
                so_line_item = (0, 0, {
                    'product_id': move.product_id.id,
                    'invoice_no': move.invoice_no,
                    'be_line_no': move.be_line_no,
                    'material_code': move.material_code,
                    'product_uom_qty': move.quantity_done,
                    'invsno': move.invsno,
                    'itemsn': move.itemsn,
                    'unit': move.unit,
                    'cth': move.cth,
                    'lot_id': move.lot_id or move.lot_ids.name,
                    'health_cess': lot_id.health_cess * move.quantity_done,
                    'acd': lot_id.acd * move.quantity_done,
                    'sad': lot_id.sad * move.quantity_done,
                    'g_cess': lot_id.g_cess * move.quantity_done,
                    'add': lot_id.add * move.quantity_done,
                    'cvd': lot_id.cvd * move.quantity_done,
                    'sg': lot_id.sg * move.quantity_done,
                    'saed': lot_id.saed * move.quantity_done,
                    'gsia': lot_id.gsia * move.quantity_done,
                    'spexd': lot_id.spexd * move.quantity_done,
                    'chcess': lot_id.chcess * move.quantity_done,
                    'cess': lot_id.cess * move.quantity_done,
                    'caidc': lot_id.caidc * move.quantity_done,
                    'eaidc': lot_id.eaidc * move.quantity_done,
                    'cusedc': lot_id.cusedc * move.quantity_done,
                    'cushec': lot_id.cushec * move.quantity_done,
                    'ncd': lot_id.ncd * move.quantity_done,
                    'aggr': lot_id.aggr * move.quantity_done,
                    'invoice_currency': lot_id.invoice_currency,
                    'exchange_rate': lot_id.exchange_rate * move.quantity_done,
                    'cif_value': lot_id.cif_value * move.quantity_done,
                    'assessable_value': lot_id.assessable_value * move.quantity_done,
                    'basic_duty_rate': lot_id.basic_duty_rate * move.quantity_done,
                    'total_basic_duty': lot_id.total_basic_duty * move.quantity_done,
                    'sws_rate': lot_id.sws_rate * move.quantity_done,
                    'sws_duty_amt': lot_id.sws_duty_amt * move.quantity_done,
                    'igst_rate': lot_id.igst_rate * move.quantity_done,
                    'igst_amount': lot_id.igst_amount * move.quantity_done,
                    'total_duty': lot_id.total_duty * move.quantity_done,
                    'country_of_origin': lot_id.country_of_origin
                })
                line_item.append(so_line_item)
        order_id = sale_order.create(so_details)
        self.sale_order_id = order_id
        order_id.write({'order_line': line_item})
        self.is_single_sale_button = True
        self.is_validate = True

    # function to pass component of FG into operation tab along with FG
    @api.onchange('manufacturing_fg_ids')
    def push_to_operations(self):
        transfer_line = []
        for fg_line in self.manufacturing_fg_ids:
            if fg_line.lot_producing_id:
                search_lot_id = self.env['mrp.production'].search(
                    [('lot_producing_id', '=', fg_line.lot_producing_id.id)])
                fg_line.manufacturing_product_id = search_lot_id.product_id.id
                for components in search_lot_id.move_raw_ids:
                    # search_stock_lot = self.env["stock.lot"].search([('product_id', '=', components.product_id.id)])
                    # print(search_stock_lot)
                    transfer_line.append({
                        'product_id': components.product_id.id,
                        'product_uom': components.product_id.uom_po_id.id,
                        'product_uom_qty': components.product_uom_qty,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'name': components.product_id.name,
                        'lot_ids': [(4, components.lot_ids.id)],
                        # 'lot_ids': (6, 0, [components.lot_ids.ids]),
                        'picking_id': self.id,
                    })
                transfer_line.append({
                    'product_id': fg_line.manufacturing_product_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'product_uom': fg_line.manufacturing_product_id.uom_po_id.id,
                    'product_uom_qty': search_lot_id.product_qty,
                    'name': fg_line.manufacturing_product_id.name,
                    # 'lot_id': fg_line.lot_producing_id.name,
                    'lot_ids': [(4, fg_line.lot_producing_id.id)],
                    # 'lot_ids': (6, 0, [fg_line.lot_producing_id.id]),
                    'picking_id': self.id,
                })
        if transfer_line:
            for rec in transfer_line:
                self.env['stock.move'].create(rec)

    # function to pass component of FG into component tab
    @api.onchange('manufacturing_fg_ids')
    def push_to_components(self):
        transfer_line = []
        for fg_line in self.manufacturing_fg_ids:
            if fg_line.lot_producing_id:
                search_lot_id = self.env['mrp.production'].search(
                    [('lot_producing_id', '=', fg_line.lot_producing_id.id)])
                for components in search_lot_id.move_raw_ids:
                    # search_stock_lot_no = self.env["stock.lot"].search([('product_id', '=', components.product_id.id)])
                    transfer_line.append({
                        'manufacturing_component_id': components.product_id.id,
                        'product_uom_qty': components.product_uom_qty,
                        'quantity_done': components.quantity_done,
                        'product_uom': components.product_id.uom_po_id.id,
                        # 'lot_ids': (search_stock_lot_no.ids),
                        'lot_id': components.lot_ids.name
                    })
        if transfer_line:
            rec_id = self.env['component.stock.move'].create(transfer_line)
            self.write({
                'manufacturing_component_ids': rec_id
            })

    # Function to show validation if create single sale order and multiple sale order
    # button is visible, and we are trying to validate move, if sale order is created,
    # and it is not confirmed, and we are trying to validate move it will through error.
    def button_validate(self):
        for records in self:
            if records.is_so and records.is_validate_multiple == False:
                raise ValidationError('Please create sale order')
            if records.is_single_so and records.is_validate == False:
                raise ValidationError('Please create sale order')
            if records.sale_count != 0:
                values = self.env['sale.order'].search([('receipt_id', '=', records.id)])
                if values:
                    for vals in values:
                        if vals.state != 'sale':
                            raise ValidationError('Sale Order is not Confirmed')
                        else:
                            return super(InventoryProductPicking, self).button_validate()
        return super(InventoryProductPicking, self).button_validate()

    # Function for smart button to show sale order created from multiple sale order button.
    def create_sale_order_from_transfer(self):
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('receipt_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
        }

    # Function for smart button to show sale order created from single sale order button.
    def create_single_sale_order_from_transfer(self):
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('receipt_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
        }


class InventoryProductMove(models.Model):
    _inherit = 'stock.move'

    invoice_currency = fields.Many2one('res.currency', string='Invoice Currency',
                                       related='purchase_line_id.invoice_currency', store=True)
    exchange_rate = fields.Float(string='Exchange Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    cif_value = fields.Float(string='CIF Value(INR)', compute='compute_health_cess', digits=(12, 4), store=True)
    assessable_value = fields.Float(string='Assessable Value(INR)', compute='compute_health_cess', digits=(12, 4),
                                    store=True)
    basic_duty_rate = fields.Float(string='Basic Duty Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    total_basic_duty = fields.Float(string='Total Basic Duty(INR)', compute='compute_health_cess', digits=(12, 4),
                                    store=True)
    sws_rate = fields.Float(string='SWS Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    sws_duty_amt = fields.Float(string='SWS Duty Amt', compute='compute_health_cess', digits=(12, 4), store=True)
    igst_rate = fields.Float(string='IGST Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    igst_amount = fields.Float(string='IGST Amount', compute='compute_health_cess', digits=(12, 4), store=True)
    total_duty = fields.Float(string='Total Duty(INR)', compute='compute_health_cess', digits=(12, 4), store=True)
    country_of_origin = fields.Char(string='Country of Origin', related='purchase_line_id.country_of_origin',
                                    store=True)

    invoice_no = fields.Char(string='Invoice No', related='purchase_line_id.invoice_no', store=True)
    lot_id = fields.Char(string='Lot/Serial Number', related='purchase_line_id.lot_id', store=True)
    be_line_no = fields.Char(string='BE Line No', related='purchase_line_id.be_line_no', store=True)
    material_code = fields.Char(string='Material Code', related='purchase_line_id.material_code', store=True)
    unit = fields.Char(string='Unit', related='purchase_line_id.unit', store=True)
    cth = fields.Integer(string='CTH', related='purchase_line_id.cth', store=True)

    health_cess = fields.Float(string='Health Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    nccd = fields.Float(string='NCCD', compute='compute_health_cess', digits=(12, 4), store=True)
    acd = fields.Float(string='ACD', compute='compute_health_cess', digits=(12, 4), store=True)
    sad = fields.Float(string='SAD', compute='compute_health_cess', digits=(12, 4), store=True)
    g_cess = fields.Float(string='G.Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    add = fields.Float(string='ADD', compute='compute_health_cess', digits=(12, 4), store=True)
    cvd = fields.Float(string='CVD', compute='compute_health_cess', digits=(12, 4), store=True)
    sg = fields.Float(string='SG', compute='compute_health_cess', digits=(12, 4), store=True)
    saed = fields.Float(string='SAED', compute='compute_health_cess', digits=(12, 4), store=True)
    gsia = fields.Float(string='GSIA', compute='compute_health_cess', digits=(12, 4), store=True)
    spexd = fields.Float(string='SPEXD', compute='compute_health_cess', digits=(12, 4), store=True)
    chcess = fields.Float(string='CHCESS', compute='compute_health_cess', digits=(12, 4), store=True)
    cess = fields.Float(string='Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    caidc = fields.Float(string='CAIDC', compute='compute_health_cess', digits=(12, 4), store=True)
    eaidc = fields.Float(string='EAIDC', compute='compute_health_cess', digits=(12, 4), store=True)
    cusedc = fields.Float(string='CUSEDC', compute='compute_health_cess', digits=(12, 4), store=True)
    cushec = fields.Float(string='CUSHEC', compute='compute_health_cess', digits=(12, 4), store=True)
    ncd = fields.Float(string='NCD', compute='compute_health_cess', digits=(12, 4), store=True)
    aggr = fields.Float(string='AGGR', compute='compute_health_cess', digits=(12, 4), store=True)
    invsno = fields.Integer(string="INVSNO", related='purchase_line_id.invsno', readonly=True)
    itemsn = fields.Integer(string="ITEMSN", related='purchase_line_id.itemsn', readonly=True)

    stock_move_line_connection = fields.Many2one('stock.move.line')
    is_lots = fields.Boolean(default=True)
    is_lot = fields.Boolean(default=True)
    lot_ids = fields.Many2many('stock.lot', compute='_compute_lot_ids', inverse='_set_lot_ids', string='Serial Numbers',
                               readonly=False)

    # lot_ids = fields.Many2many('stock.lot', string='Serial Numbers',
    #                            readonly=False)

    @api.depends('move_line_ids', 'move_line_ids.lot_id', 'move_line_ids.qty_done')
    def _compute_lot_ids(self):
        if not self.manufacturing_product_id:
            domain_nosuggest = [('move_id', 'in', self.ids), ('lot_id', '!=', False), '|', ('qty_done', '!=', 0.0),
                                ('reserved_qty', '=', 0.0)]
            domain_suggest = [('move_id', 'in', self.ids), ('lot_id', '!=', False), ('qty_done', '!=', 0.0)]
            lots_by_move_id_list = []
            for domain in [domain_nosuggest, domain_suggest]:
                lots_by_move_id = self.env['stock.move.line']._read_group(
                    domain,
                    ['move_id', 'lot_ids:array_agg(lot_id)'], ['move_id'],
                )
                lots_by_move_id_list.append({by_move['move_id'][0]: by_move['lot_ids'] for by_move in lots_by_move_id})
            for move in self:
                move.lot_ids = lots_by_move_id_list[0 if move.picking_type_id.show_reserved else 1].get(move._origin.id,
                                                                                                        [])
        # else:
        #     for move in self:
        #         move.lot_ids  = move.lot_ids

    def _set_lot_ids(self):
        if not self.manufacturing_product_id:
            for move in self:
                if move.product_id.tracking != 'serial':
                    continue
                move_lines_commands = []
                if move.picking_type_id.show_reserved is False:
                    mls = move.move_line_nosuggest_ids
                else:
                    mls = move.move_line_ids
                mls_with_lots = mls.filtered(lambda ml: ml.lot_id)
                mls_without_lots = (mls - mls_with_lots)
                for ml in mls_with_lots:
                    if ml.qty_done and ml.lot_id not in move.lot_ids:
                        move_lines_commands.append((2, ml.id))
                ls = move.move_line_ids.lot_id
                for lot in move.lot_ids:
                    if lot not in ls:
                        if mls_without_lots[:1]:  # Updates an existing line without serial number.
                            move_line = mls_without_lots[:1]
                            move_lines_commands.append(Command.update(move_line.id, {
                                'lot_name': lot.name,
                                'lot_id': lot.id,
                                'product_uom_id': move.product_id.uom_id.id,
                                'qty_done': 1,
                            }))
                            mls_without_lots -= move_line
                        else:  # No line without serial number, creates a new one.
                            move_line_vals = self._prepare_move_line_vals(quantity=0)
                            move_line_vals['lot_id'] = lot.id
                            move_line_vals['lot_name'] = lot.name
                            move_line_vals['product_uom_id'] = move.product_id.uom_id.id
                            move_line_vals['qty_done'] = 1
                            move_lines_commands.append((0, 0, move_line_vals))
                    else:
                        move_line = move.move_line_ids.filtered(lambda line: line.lot_id.id == lot.id)
                        move_line.qty_done = 1
                move.write({'move_line_ids': move_lines_commands})

    @api.depends('purchase_line_id')
    def compute_health_cess(self):
        for rec in self:
            if rec.purchase_line_id.product_qty > 0:
                rec.health_cess = round(rec.purchase_line_id.health_cess / rec.purchase_line_id.product_qty, 4)
                rec.nccd = round(rec.purchase_line_id.nccd / rec.purchase_line_id.product_qty, 4)
                rec.acd = round(rec.purchase_line_id.acd / rec.purchase_line_id.product_qty, 4)
                rec.sad = round(rec.purchase_line_id.sad / rec.purchase_line_id.product_qty, 4)
                rec.g_cess = round(rec.purchase_line_id.g_cess / rec.purchase_line_id.product_qty, 4)
                rec.add = round(rec.purchase_line_id.add / rec.purchase_line_id.product_qty, 4)
                rec.cvd = round(rec.purchase_line_id.cvd / rec.purchase_line_id.product_qty, 4)
                rec.sg = round(rec.purchase_line_id.sg / rec.purchase_line_id.product_qty, 4)
                rec.saed = round(rec.purchase_line_id.saed / rec.purchase_line_id.product_qty, 4)
                rec.gsia = round(rec.purchase_line_id.gsia / rec.purchase_line_id.product_qty, 4)
                rec.spexd = round(rec.purchase_line_id.spexd / rec.purchase_line_id.product_qty, 4)
                rec.chcess = round(rec.purchase_line_id.chcess / rec.purchase_line_id.product_qty, 4)
                rec.cess = round(rec.purchase_line_id.cess / rec.purchase_line_id.product_qty, 4)
                rec.caidc = round(rec.purchase_line_id.caidc / rec.purchase_line_id.product_qty, 4)
                rec.eaidc = round(rec.purchase_line_id.eaidc / rec.purchase_line_id.product_qty, 4)
                rec.cusedc = round(rec.purchase_line_id.cusedc / rec.purchase_line_id.product_qty, 4)
                rec.cushec = round(rec.purchase_line_id.cushec / rec.purchase_line_id.product_qty, 4)
                rec.ncd = round(rec.purchase_line_id.ncd / rec.purchase_line_id.product_qty, 4)
                rec.aggr = round(rec.purchase_line_id.aggr / rec.purchase_line_id.product_qty, 4)
                # rec.exchange_rate = round(rec.purchase_line_id.exchange_rate / rec.purchase_line_id.product_qty, 4)
                rec.exchange_rate = round(rec.purchase_line_id.exchange_rate, 4)
                # rec.basic_duty_rate = round(rec.purchase_line_id.basic_duty_rate / rec.purchase_line_id.product_qty, 4)
                rec.basic_duty_rate = round(rec.purchase_line_id.basic_duty_rate, 4)
                rec.cif_value = round(rec.purchase_line_id.cif_value / rec.purchase_line_id.product_qty, 4)
                rec.total_basic_duty = round(rec.purchase_line_id.total_basic_duty / rec.purchase_line_id.product_qty,
                                             4)
                rec.assessable_value = round(rec.purchase_line_id.assessable_value / rec.purchase_line_id.product_qty,
                                             4)
                # rec.sws_rate = round(rec.purchase_line_id.sws_rate / rec.purchase_line_id.product_qty, 4)
                rec.sws_rate = round(rec.purchase_line_id.sws_rate, 4)
                rec.sws_duty_amt = round(rec.purchase_line_id.sws_duty_amt / rec.purchase_line_id.product_qty, 4)
                rec.total_duty = round(rec.purchase_line_id.total_duty / rec.purchase_line_id.product_qty, 4)
                # rec.igst_rate = round(rec.purchase_line_id.igst_rate / rec.purchase_line_id.product_qty, 4)
                rec.igst_rate = round(rec.purchase_line_id.igst_rate, 4)
                rec.igst_amount = round(rec.purchase_line_id.igst_amount / rec.purchase_line_id.product_qty, 4)

    @api.model
    def default_get(self, fields_list):
        location_id = self.env['stock.location'].search([('is_production_location', '=', True)])
        defaults = super(InventoryProductMove, self).default_get(fields_list)
        if defaults.get('location_dest_id'):
            defaults['location_dest_id'] = location_id.id
        else:
            pass
        if self.env.context.get('default_raw_material_production_id') or self.env.context.get('default_production_id'):
            production_id = self.env['mrp.production'].browse(
                self.env.context.get('default_raw_material_production_id') or self.env.context.get(
                    'default_production_id'))
            if production_id.state not in ('draft', 'cancel'):
                if production_id.state != 'done':
                    defaults['state'] = 'draft'
                else:
                    defaults['state'] = 'done'
                    defaults['additional'] = True
                defaults['product_uom_qty'] = 0.0
            elif production_id.state == 'draft':
                defaults['group_id'] = production_id.procurement_group_id.id
                defaults['reference'] = production_id.name
        return defaults

    # Function to show additional fields of operation tab
    def view_order_line(self):
        return {
            'name': "Order Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'view_id': self.env.ref('slc_custom.stock_move_line_view_form').id,
            'res_id': self.id,
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ Enforce consistent values (i.e. match _get_move_raw_values/_get_move_finished_values) for:
        - Manually added components/byproducts specifically values we can't set via view with "default_"
        - Moves from a copied MO
        - Backorders
        """
        res = super().create(vals_list)
        if res.raw_material_production_id:
            res.location_dest_id = res.raw_material_production_id.location_dest_id
        else:
            for i in vals_list:
                if i.get('location_dest_id'):
                    res.location_dest_id = i['location_dest_id']
                    res.location_id = i['location_id']
        return res

    # fields for new tab Manufacturing FG
    manufacturing_fg_id = fields.Many2one('stock.picking')
    lot_producing_id = fields.Many2one('stock.lot', string='Lot/Serial Number')
    manufacturing_product_id = fields.Many2one('product.product', string='Manufacturing Product',
                                               related='lot_producing_id.product_id')
    # product_uom_qty = fields.Float(string="Demand")
    location_move_id = fields.Many2one('stock.location', related='manufacturing_fg_id.location_id', store=True)
    location_dest_move_id = fields.Many2one('stock.location', related='manufacturing_fg_id.location_dest_id',
                                            store=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True, required=False,
        states={'done': [('readonly', True)]})
    product_uom_qty = fields.Float(
        'Demand',
        digits='Product Unit of Measure',
        default=1.0, required=False, states={'done': [('readonly', True)]},
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved. For other "
             "moves, this is the quantity of product that is planned to "
             "be moved. Lowering this quantity does not generate a "
             "backorder. Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.")
    product_uom = fields.Many2one(
        'uom.uom', "UoM", required=False, domain="[('category_id', '=', product_uom_category_id)]",
        compute="_compute_product_uom", store=True, readonly=False, precompute=True,
    )
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=False,
        check_company=True,
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        auto_join=True, index=True, required=False,
        check_company=True,
        help="Location where the system will stock the finished products.")
    name = fields.Char('Description', required=False)

    def serach_lot_id(self):
        records = self.env['stock.move'].search([('')])


class InheritStockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, vals):
        res = super(InheritStockQuant, self).create(vals)
        if vals.get('quantity'):
            # select virtual location in stock location
            location_list = []
            search_virtual_location = self.env['stock.location'].search([('usage', '=', 'internal')])
            for rec in search_virtual_location:
                location_list.append(rec.id)
            if vals['quantity'] < 0 and vals['location_id'] in location_list:
                raise ValidationError("You cannot have negative inventory")
            print(res)
        else:
            pass
        return res


class ComponentStockMove(models.Model):
    _name = 'component.stock.move'

    manufacturing_component_id = fields.Many2one('product.product', string='Manufacturing Component')
    component_id = fields.Many2one('stock.picking')
    purchase_line_id = fields.Many2one('purchase.order.line')

    invoice_currency = fields.Many2one('res.currency', string='Invoice Currency',
                                       related='purchase_line_id.invoice_currency', store=True)
    exchange_rate = fields.Float(string='Exchange Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    cif_value = fields.Float(string='CIF Value(INR)', compute='compute_health_cess', digits=(12, 4), store=True)
    assessable_value = fields.Float(string='Assessable Value(INR)', compute='compute_health_cess', digits=(12, 4),
                                    store=True)
    basic_duty_rate = fields.Float(string='Basic Duty Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    total_basic_duty = fields.Float(string='Total Basic Duty(INR)', compute='compute_health_cess', digits=(12, 4),
                                    store=True)
    sws_rate = fields.Float(string='SWS Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    sws_duty_amt = fields.Float(string='SWS Duty Amt', compute='compute_health_cess', digits=(12, 4), store=True)
    igst_rate = fields.Float(string='IGST Rate', compute='compute_health_cess', digits=(12, 4), store=True)
    igst_amount = fields.Float(string='IGST Amount', compute='compute_health_cess', digits=(12, 4), store=True)
    total_duty = fields.Float(string='Total Duty(INR)', compute='compute_health_cess', digits=(12, 4), store=True)
    country_of_origin = fields.Char(string='Country of Origin', related='purchase_line_id.country_of_origin',
                                    store=True)

    invoice_no = fields.Char(string='Invoice No', related='purchase_line_id.invoice_no', store=True)
    lot_id = fields.Char(string='Lot/Serial Number', related='purchase_line_id.lot_id', store=True)
    be_line_no = fields.Char(string='BE Line No', related='purchase_line_id.be_line_no', store=True)
    material_code = fields.Char(string='Material Code', related='purchase_line_id.material_code', store=True)
    unit = fields.Char(string='Unit', related='purchase_line_id.unit', store=True)
    cth = fields.Integer(string='CTH', related='purchase_line_id.cth', store=True)

    health_cess = fields.Float(string='Health Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    nccd = fields.Float(string='NCCD', compute='compute_health_cess', digits=(12, 4), store=True)
    acd = fields.Float(string='ACD', compute='compute_health_cess', digits=(12, 4), store=True)
    sad = fields.Float(string='SAD', compute='compute_health_cess', digits=(12, 4), store=True)
    g_cess = fields.Float(string='G.Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    add = fields.Float(string='ADD', compute='compute_health_cess', digits=(12, 4), store=True)
    cvd = fields.Float(string='CVD', compute='compute_health_cess', digits=(12, 4), store=True)
    sg = fields.Float(string='SG', compute='compute_health_cess', digits=(12, 4), store=True)
    saed = fields.Float(string='SAED', compute='compute_health_cess', digits=(12, 4), store=True)
    gsia = fields.Float(string='GSIA', compute='compute_health_cess', digits=(12, 4), store=True)
    spexd = fields.Float(string='SPEXD', compute='compute_health_cess', digits=(12, 4), store=True)
    chcess = fields.Float(string='CHCESS', compute='compute_health_cess', digits=(12, 4), store=True)
    cess = fields.Float(string='Cess', compute='compute_health_cess', digits=(12, 4), store=True)
    caidc = fields.Float(string='CAIDC', compute='compute_health_cess', digits=(12, 4), store=True)
    eaidc = fields.Float(string='EAIDC', compute='compute_health_cess', digits=(12, 4), store=True)
    cusedc = fields.Float(string='CUSEDC', compute='compute_health_cess', digits=(12, 4), store=True)
    cushec = fields.Float(string='CUSHEC', compute='compute_health_cess', digits=(12, 4), store=True)
    ncd = fields.Float(string='NCD', compute='compute_health_cess', digits=(12, 4), store=True)
    aggr = fields.Float(string='AGGR', compute='compute_health_cess', digits=(12, 4), store=True)

    product_uom_qty = fields.Float(string='Demand')
    reserved_availability = fields.Float(string='Reserved')
    quantity_done = fields.Float(string='Done')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    lot_ids = fields.Many2many('stock.lot', string='Serial Number')
    stock_move_operation = fields.Many2one('stock.move')

    @api.depends('purchase_line_id')
    def compute_health_cess(self):
        for rec in self:
            if rec.purchase_line_id.product_qty > 0:
                rec.health_cess = round(rec.purchase_line_id.health_cess / rec.purchase_line_id.product_qty, 4)
                rec.nccd = round(rec.purchase_line_id.nccd / rec.purchase_line_id.product_qty, 4)
                rec.acd = round(rec.purchase_line_id.acd / rec.purchase_line_id.product_qty, 4)
                rec.sad = round(rec.purchase_line_id.sad / rec.purchase_line_id.product_qty, 4)
                rec.g_cess = round(rec.purchase_line_id.g_cess / rec.purchase_line_id.product_qty, 4)
                rec.add = round(rec.purchase_line_id.add / rec.purchase_line_id.product_qty, 4)
                rec.cvd = round(rec.purchase_line_id.cvd / rec.purchase_line_id.product_qty, 4)
                rec.sg = round(rec.purchase_line_id.sg / rec.purchase_line_id.product_qty, 4)
                rec.saed = round(rec.purchase_line_id.saed / rec.purchase_line_id.product_qty, 4)
                rec.gsia = round(rec.purchase_line_id.gsia / rec.purchase_line_id.product_qty, 4)
                rec.spexd = round(rec.purchase_line_id.spexd / rec.purchase_line_id.product_qty, 4)
                rec.chcess = round(rec.purchase_line_id.chcess / rec.purchase_line_id.product_qty, 4)
                rec.cess = round(rec.purchase_line_id.cess / rec.purchase_line_id.product_qty, 4)
                rec.caidc = round(rec.purchase_line_id.caidc / rec.purchase_line_id.product_qty, 4)
                rec.eaidc = round(rec.purchase_line_id.eaidc / rec.purchase_line_id.product_qty, 4)
                rec.cusedc = round(rec.purchase_line_id.cusedc / rec.purchase_line_id.product_qty, 4)
                rec.cushec = round(rec.purchase_line_id.cushec / rec.purchase_line_id.product_qty, 4)
                rec.ncd = round(rec.purchase_line_id.ncd / rec.purchase_line_id.product_qty, 4)
                rec.aggr = round(rec.purchase_line_id.aggr / rec.purchase_line_id.product_qty, 4)
                # rec.exchange_rate = round(rec.purchase_line_id.exchange_rate / rec.purchase_line_id.product_qty, 4)
                rec.exchange_rate = round(rec.purchase_line_id.exchange_rate, 4)
                # rec.basic_duty_rate = round(rec.purchase_line_id.basic_duty_rate / rec.purchase_line_id.product_qty, 4)
                rec.basic_duty_rate = round(rec.purchase_line_id.basic_duty_rate, 4)
                rec.cif_value = round(rec.purchase_line_id.cif_value / rec.purchase_line_id.product_qty, 4)
                rec.total_basic_duty = round(rec.purchase_line_id.total_basic_duty / rec.purchase_line_id.product_qty,
                                             4)
                rec.assessable_value = round(rec.purchase_line_id.assessable_value / rec.purchase_line_id.product_qty,
                                             4)
                # rec.sws_rate = round(rec.purchase_line_id.sws_rate / rec.purchase_line_id.product_qty, 4)
                rec.sws_rate = round(rec.purchase_line_id.sws_rate, 4)
                rec.sws_duty_amt = round(rec.purchase_line_id.sws_duty_amt / rec.purchase_line_id.product_qty, 4)
                rec.total_duty = round(rec.purchase_line_id.total_duty / rec.purchase_line_id.product_qty, 4)
                # rec.igst_rate = round(rec.purchase_line_id.igst_rate / rec.purchase_line_id.product_qty, 4)
                rec.igst_rate = round(rec.purchase_line_id.igst_rate, 4)
                rec.igst_amount = round(rec.purchase_line_id.igst_amount / rec.purchase_line_id.product_qty, 4)
