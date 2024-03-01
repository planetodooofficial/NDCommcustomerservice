from odoo import fields, api, models, Command, _
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError


class InheritManufacturing(models.Model):
    _inherit = 'mrp.production'

    production_location_id = fields.Many2one('stock.location', "Production Location", store=True,
                                             compute="_compute_production_location")
    lot_sn = fields.Char(string="Lot/Serial Number", copy=False)
    location_dest_id = fields.Many2one(
        'stock.location', 'Finished Products Location',
        compute='_compute_locations', store=True, check_company=True,
        readonly=False, required=True, precompute=True,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Location where the system will stock the finished products.")
    move_raw_ids = fields.One2many(
        'stock.move', 'raw_material_production_id', 'Components',
        compute='_compute_move_raw_ids', store=True, readonly=False,
        copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    )

    # def button_mark_done(self):
    #     res = super(InheritManufacturing, self).button_mark_done()
    #     for rec in self.finished_move_line_ids:
    #         if rec.reserved_uom_qty == 0:
    #             raise ValidationError(f"Product {rec.product_id.name} is not in stock at {rec.location_id}")
    #     return res


    def _compute_locations(self):
        location_id = self.env['stock.location'].search([('is_production_location', '=', True)])
        for production in self:
            if not production.picking_type_id.default_location_src_id or not production.picking_type_id.default_location_dest_id:
                company_id = production.company_id.id if (
                        production.company_id and production.company_id in self.env.companies) else self.env.company.id
                fallback_loc = self.env['stock.warehouse'].search([('company_id', '=', company_id)],
                                                                  limit=1).lot_stock_id
            production.location_src_id = production.picking_type_id.default_location_src_id.id or fallback_loc.id
            production.location_dest_id = location_id

    @api.depends('company_id', 'bom_id', 'product_id', 'product_qty', 'product_uom_id', 'location_src_id',
                 'date_planned_start')
    def _compute_move_raw_ids(self):
        for production in self:
            if production.state != 'draft':
                continue
            list_move_raw = [Command.link(move.id) for move in
                             production.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
            if not production.bom_id and not production._origin.product_id:
                production.move_raw_ids = list_move_raw
            if production.bom_id != production._origin.bom_id:
                production.move_raw_ids = [Command.clear()]
            if production.bom_id and production.product_id and production.product_qty > 0:
                # keep manual entries
                moves_raw_values = production._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in
                                 production.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                for move_raw_values in moves_raw_values:
                    if move_raw_values['bom_line_id'] in move_raw_dict:
                        # update existing entries
                        list_move_raw += [
                            Command.update(move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                    else:
                        # add new entries
                        list_move_raw += [Command.create(move_raw_values)]
                production.move_raw_ids = list_move_raw
            else:
                production.move_raw_ids = [Command.delete(move.id) for move in
                                           production.move_raw_ids.filtered(lambda m: m.bom_line_id)]

    def _get_moves_raw_values(self):
        moves = []
        for production in self:
            if not production.bom_id:
                continue
            factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
                        bom_line.product_id.type not in ['product', 'consu']:
                    continue
                operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
                    'parent_line'].operation_id.id
                moves.append(production._get_move_raw_values(
                    bom_line.product_id,
                    line_data['qty'],
                    bom_line.product_uom_id,
                    operation,
                    bom_line
                ))
        return moves

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """ Warning, any changes done to this method will need to be repeated for consistency in:
            - Manually added components, i.e. "default_" values in view
            - Moves from a copied MO, i.e. move.create
            - Existing moves during backorder creation """
        location_id = self.env['stock.location'].search([('is_production_location', '=', True)])

        source_location = self.location_src_id
        data = {
            'sequence': bom_line.sequence if bom_line else 10,
            'name': _('New'),
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': bom_line.id if bom_line else False,
            'picking_type_id': self.picking_type_id.id,
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'location_id': source_location.id,
            'location_dest_id': location_id.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': operation_id,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self._get_origin(),
            'state': 'draft',
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
        }
        return data

    def button_mark_done(self):
        self._button_mark_done_sanity_checks()
        if not self.env.context.get('button_mark_done_production_ids'):
            self = self.with_context(button_mark_done_production_ids=self.ids)
            self.move_finished_ids.location_dest_id = self.location_dest_id
            print(self.move_finished_ids.location_dest_id, 'selffff')
            if self.move_raw_ids:
                for rec in self.move_raw_ids:
                    if rec.forecast_availability == 0:
                        raise ValidationError(f"Product {rec.product_id.name} is not in stock at {rec.location_id.name} location")
            # print(self,'selffff')
        res = self._pre_button_mark_done()
        if res is not True:
            return res

        if self.env.context.get('mo_ids_to_backorder'):
            productions_to_backorder = self.browse(self.env.context['mo_ids_to_backorder'])
            productions_not_to_backorder = self - productions_to_backorder
        else:
            productions_not_to_backorder = self
            productions_to_backorder = self.env['mrp.production']

        self.workorder_ids.button_finish()

        backorders = productions_to_backorder and productions_to_backorder._split_productions()
        backorders = backorders - productions_to_backorder

        productions_not_to_backorder._post_inventory(cancel_backorder=True)
        productions_to_backorder._post_inventory(cancel_backorder=True)

        # if completed products make other confirmed/partially_available moves available, assign them
        done_move_finished_ids = (
                    productions_to_backorder.move_finished_ids | productions_not_to_backorder.move_finished_ids).filtered(
            lambda m: m.state == 'done')
        done_move_finished_ids._trigger_assign()

        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (productions_not_to_backorder.move_raw_ids | productions_not_to_backorder.move_finished_ids).filtered(
            lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        for production in self:
            production.write({
                'date_finished': fields.Datetime.now(),
                'product_qty': production.qty_produced,
                'priority': '0',
                'is_locked': True,
                'state': 'done',
            })

        if not backorders:
            if self.env.context.get('from_workorder'):
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.production',
                    'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
                    'res_id': self.id,
                    'target': 'main',
                }
            if self.user_has_groups(
                    'mrp.group_mrp_reception_report') and self.picking_type_id.auto_show_reception_report:
                lines = self.move_finished_ids.filtered(lambda
                                                            m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                if lines:
                    if any(mo.show_allocation for mo in self):
                        action = self.action_view_reception_report()
                        return action
            return True
        context = self.env.context.copy()
        context = {k: v for k, v in context.items() if not k.startswith('default_')}
        for k, v in context.items():
            if k.startswith('skip_'):
                context[k] = False
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'context': dict(context, mo_ids_to_backorder=None, button_mark_done_production_ids=None)
        }
        if len(backorders) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': backorders[0].id,
            })
        else:
            action.update({
                'name': _("Backorder MO"),
                'domain': [('id', 'in', backorders.ids)],
                'view_mode': 'tree,form',
            })
        return action