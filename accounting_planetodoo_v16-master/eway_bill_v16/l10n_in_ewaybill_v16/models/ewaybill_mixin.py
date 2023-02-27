# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from ast import literal_eval
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class EwayBillType(models.Model):
    _name = "l10n.in.ewaybill.type"
    _description = "eWaybill Document Type"

    name = fields.Char("Document Type")
    code = fields.Char("Code")
    allowed_in_supply_type = fields.Selection(
        [
            ("both", "Incoming and Outgoing"),
            ("O", "Outgoing"),
            ("I", "Incoming"),
        ],
        string="Allowed in supply type",
    )
    allowed_in_document = fields.Selection(
        [("invoice", "Invoice"), ("stock", "Stock")], string="Allowed in Document"
    )
    active = fields.Boolean("Active", default=True)

    child_type_ids = fields.Many2many(
        "l10n.in.ewaybill.type",
        "rel_ewaybill_type_subtype",
        "type_id",
        "subtype_id",
        "Subtype",
    )
    parent_type_ids = fields.Many2many(
        "l10n.in.ewaybill.type",
        "rel_ewaybill_type_subtype",
        "subtype_id",
        "type_id",
        "Parent Types",
    )


class L10nInEwayBillMixin(models.AbstractModel):
    _name = "l10n.in.ewaybill.mixin"
    _description = "Base of eWaybill"

    l10n_in_ewaybill_type_id = fields.Many2one("l10n.in.ewaybill.type", "Document Type")
    l10n_in_ewaybill_subtype_id = fields.Many2one(
        "l10n.in.ewaybill.type", "Sub Supply Type"
    )
    l10n_in_ewaybill_subtype_code = fields.Char(
        "Sub Supply Type Code", related="l10n_in_ewaybill_subtype_id.code"
    )
    l10n_in_ewaybill_sub_supply_desc = fields.Char("Sub Supply Description")

    # In Stock onlu "Regular" and "Bill From-Dispatch From" is supported
    l10n_in_ewaybill_transaction_type = fields.Selection(
        [
            ("1", "Regular"),
            ("2", "Bill To-Ship To"),
            ("3", "Bill From-Dispatch From"),
            ("4", "Combination of 2 and 3"),
        ],
        string="Ewaybill Transaction Type",
    )

    l10n_in_ewaybill_mode = fields.Selection(
        [
            ("0", "Managed by Transporter"),
            ("1", "By Road"),
            ("2", "Rail"),
            ("3", "Air"),
            ("4", "Ship"),
        ],
        string="Transportation Mode",
    )

    l10n_in_ewaybill_vehicle_type = fields.Selection(
        [
            ("R", "Regular"),
            ("O", "ODC"),
        ],
        string="Vehicle Type",
    )

    # l10n_in_ewaybill_transporter_id = fields.Char('Transporter Id')
    # l10n_in_ewaybill_transporter_name = fields.Char('Transporter Name')
    l10n_in_ewaybill_transporter_id = fields.Many2one("res.partner", "Transporter")

    l10n_in_ewaybill_distance = fields.Char("Distance")
    l10n_in_ewaybill_vehicle_no = fields.Char("Vehicle Number")

    l10n_in_ewaybill_transporter_doc_no = fields.Char(
        "Document Number",
        help="""Transport document number.
If it is more than 15 chars, last 15 chars may be entered""",
    )
    l10n_in_ewaybill_transporter_doc_date = fields.Date(
        "Document Date", help="Date on the transporter document"
    )

    l10n_in_ewaybill_document_number = fields.Char(
        "Doc No", compute="_compute_l10n_in_ewaybill_document_number"
    )
    l10n_in_ewaybill_document_date = fields.Date(
        "Doc Date", compute="_compute_l10n_in_ewaybill_document_date"
    )

    l10n_in_ewaybill_bill_to = fields.Many2one(
        "res.partner", compute="_compute_l10n_in_ewaybill_bill_to", string="Consigner"
    )
    l10n_in_ewaybill_ship_to = fields.Many2one(
        "res.partner", compute="_compute_l10n_in_ewaybill_ship_to", string="Ship to"
    )

    l10n_in_ewaybill_bill_from = fields.Many2one(
        "res.partner", compute="_compute_l10n_in_ewaybill_bill_from", string="Consignee"
    )
    l10n_in_ewaybill_ship_from = fields.Many2one(
        "res.partner", compute="_compute_l10n_in_ewaybill_ship_from", string="Ship from"
    )

    l10n_in_ewaybill_number = fields.Char(
        compute="_compute_l10n_in_ewaybill_details", string="eWaybill Number"
    )
    l10n_in_ewaybill_valid_upto = fields.Datetime(
        compute="_compute_l10n_in_ewaybill_details", string="Valid Upto"
    )
    l10n_in_ewaybill_state = fields.Selection(
        [
            ("not_submited", "Not Submited"),
            ("submited", "Submited"),
            ("cancelled", "Cancelled"),
        ],
        string="eWaybill Status",
        compute="_compute_l10n_in_ewaybill_details",
    )

    l10n_in_ewaybill_supply_type = fields.Selection(
        [
            ("O", "Outward"),
            ("I", "Inward"),
        ],
        string="Supply type",
        compute="_compute_l10n_in_ewaybill_supply_type",
    )

    l10n_in_ewaybill_invoice_values_json = fields.Binary(
        "Financial Data (JSON)", compute="_compute_l10n_in_ewaybill_invoice_values_json"
    )

    # TO BE OVERWRITTEN
    @api.model
    def _get_ewaybill_transaction_field(self):
        return ""

    # TO BE OVERWRITTEN
    def _get_ewaybill_transaction_domain(self):
        return []

    def _compute_l10n_in_ewaybill_details(self):
        for record in self:
            transaction = self.env["l10n.in.ewaybill.transaction"].search(
                self._get_ewaybill_transaction_domain()
                + [("request_type", "!=", "update_partb")],
                limit=1,
            )
            record.l10n_in_ewaybill_number = transaction.ewaybill_number
            # if eway bill is cancelled then not set valid_upto because is meaningless
            if transaction and transaction.request_type == "cancel":
                record.l10n_in_ewaybill_valid_upto = False
                record.l10n_in_ewaybill_state = "cancelled"
            elif transaction and transaction.request_type != "cancel":
                record.l10n_in_ewaybill_valid_upto = transaction.ewaybill_valid_upto
                record.l10n_in_ewaybill_state = "submited"
            else:
                record.l10n_in_ewaybill_state = "not_submited"
                record.l10n_in_ewaybill_valid_upto = False

    # TO BE OVERWRITTEN
    def _compute_l10n_in_ewaybill_document_number(self):
        self.l10n_in_ewaybill_document_number = False
        self.l10n_in_ewaybill_document_date = False

    # TO BE OVERWRITTEN
    def _compute_l10n_in_ewaybill_supply_type(self):
        self.l10n_in_ewaybill_supply_type = False

    # TO BE OVERWRITTEN
    def _compute_l10n_in_ewaybill_invoice_values_json(self):
        self.l10n_in_ewaybill_invoice_values_json = {}

    def _compute_l10n_in_ewaybill_bill_to(self):
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "I":
                record.l10n_in_ewaybill_bill_to = record.company_id.partner_id
                # record.l10n_in_ewaybill_bill_to = record.journal_id.l10n_in_gstin_partner_id
            else:
                record.l10n_in_ewaybill_bill_to = False

    def _compute_l10n_in_ewaybill_ship_to(self):
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "I":
                record.l10n_in_ewaybill_ship_to = record.company_id.partner_id
                # record.l10n_in_ewaybill_ship_to = record.journal_id.l10n_in_gstin_partner_id
                _logger.info("Ship to partner %s", record.l10n_in_ewaybill_ship_to.name)
            else:
                record.l10n_in_ewaybill_ship_to = False

    def _compute_l10n_in_ewaybill_bill_from(self):
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                record.l10n_in_ewaybill_bill_from = record.company_id.partner_id
                # record.l10n_in_ewaybill_bill_from = record.journal_id.l10n_in_gstin_partner_id
                _logger.info("Bill From partner %s", record.l10n_in_ewaybill_ship_to.name)
            else:
                record.l10n_in_ewaybill_bill_from = False

    def _compute_l10n_in_ewaybill_ship_from(self):
        for record in self:
            if record.l10n_in_ewaybill_supply_type == "O":
                record.l10n_in_ewaybill_ship_from = record.company_id.partner_id
                # record.l10n_in_ewaybill_ship_from = record.journal_id.l10n_in_gstin_partner_id
                _logger.info("Ship From to partner %s", record.l10n_in_ewaybill_ship_to.name)
            else:
                record.l10n_in_ewaybill_ship_from = False

    @api.model
    def _validate_ewaybill_partner(self, partner, prefix):
        message = str()
        if partner and not re.match("^[0-9]{6,}$", partner.zip or ""):
            message += "\n- %s(%s) required Pincode" % (prefix, partner.name)
        if partner and not partner.state_id.name:
            message += "\n- %s(%s) required State" % (prefix, partner.name)
        return message

    def _check_ewaybill_require_field(self, field_name, postfix=""):
        self.ensure_one()
        message = str()
        field = self.env["ir.model.fields"]._get(self._name, field_name)
        if field and not self[field_name]:
            message += "\n- %s is Required %s" % (field.field_description, postfix)
        return message

    def _prepare_validate_ewaybill_message(self):
        self.ensure_one()
        message = str()
        message += self._validate_ewaybill_partner(
            self.l10n_in_ewaybill_bill_from, "Bill From"
        )
        message += self._validate_ewaybill_partner(
            self.l10n_in_ewaybill_ship_from, "Ship From"
        )
        message += self._validate_ewaybill_partner(
            self.l10n_in_ewaybill_bill_to, "Bill To"
        )
        message += self._validate_ewaybill_partner(
            self.l10n_in_ewaybill_ship_to, "Ship To"
        )
        message += self._check_ewaybill_require_field(
            "l10n_in_ewaybill_transaction_type"
        )
        message += self._check_ewaybill_require_field("l10n_in_ewaybill_type_id")
        message += self._check_ewaybill_require_field("l10n_in_ewaybill_subtype_id")
        message += self._check_ewaybill_require_field("l10n_in_ewaybill_distance")
        message += self._check_ewaybill_require_field("l10n_in_ewaybill_mode")
        if self.l10n_in_ewaybill_subtype_id == self.env.ref(
            "l10n_in_ewaybill.type_others"
        ):
            message += self._check_ewaybill_require_field(
                "l10n_in_ewaybill_sub_supply_desc", "when supply type is Other"
            )
        if self.l10n_in_ewaybill_mode == "1":
            # message += self._check_ewaybill_require_field('l10n_in_ewaybill_vehicle_type', "when Transportation by road")
            message += self._check_ewaybill_require_field(
                "l10n_in_ewaybill_vehicle_no", "when Transportation by road"
            )
            if (
                self.l10n_in_ewaybill_vehicle_no
                and len(self.l10n_in_ewaybill_vehicle_no) < 7
            ):
                message += "\n- Vehicle Number expected minimum length: 7"
        elif self.l10n_in_ewaybill_mode in ("2", "3", "4"):
            message += self._check_ewaybill_require_field(
                "l10n_in_ewaybill_transporter_doc_no",
                "when Transportation by Rail,Air or Ship",
            )
            message += self._check_ewaybill_require_field(
                "l10n_in_ewaybill_transporter_doc_date",
                "when Transportation by Rail,Air or Ship",
            )
        if not re.match("^.{1,16}$", self.l10n_in_ewaybill_document_number or ""):
            message += "\n- Source Document Number(%s) expected maximum length: 16" % (
                self.l10n_in_ewaybill_document_number
            )
        if (
            self.l10n_in_ewaybill_subtype_id.code in ("11", "5", "12", "10")
            and self.l10n_in_ewaybill_bill_from.vat != self.l10n_in_ewaybill_bill_to.vat
        ):
            message += '\n- Sub Supply Type "%s" Need self GSTIN' % (
                self.l10n_in_ewaybill_subtype_id.name
            )
        if (
            self.l10n_in_ewaybill_transaction_type in ("2", "4")
            and not self.l10n_in_ewaybill_ship_to.vat
        ):
            transaction_type = dict(
                self._fields["l10n_in_ewaybill_transaction_type"].selection
            ).get(self.l10n_in_ewaybill_transaction_type)
            message += (
                '\n- If transaction type is "%s" then GSTIN is required in "%s" '
                % (transaction_type, self.l10n_in_ewaybill_ship_to.display_name)
            )
        if (
            self.l10n_in_ewaybill_transaction_type in ("3", "4")
            and not self.l10n_in_ewaybill_ship_from.vat
        ):
            transaction_type = dict(
                self._fields["l10n_in_ewaybill_transaction_type"].selection
            ).get(self.l10n_in_ewaybill_transaction_type)
            message += (
                '\n- If transaction type is "%s" then GSTIN is required in "%s" '
                % (transaction_type, self.l10n_in_ewaybill_ship_from.display_name)
            )
        return message

    def _validate_l10n_in_ewaybill(self):
        self.ensure_one()
        message = self._prepare_validate_ewaybill_message()
        if message:
            raise UserError(_(message))
        return True

    # TO BE OVERWRITTEN
    def _generate_ewaybill_transaction(self, vals):
        return False

    def button_l10n_in_submit_ewaybill(self):
        self.ensure_one()
        self._validate_l10n_in_ewaybill()

        ewaybill = self._generate_ewaybill_transaction({"request_type": "generate"})
        ewaybill.submit()

    def button_l10n_in_cancel_ewaybill(self):
        self.ensure_one()
        return {
            "name": _("Cancel Eway Bill"),
            "res_model": "l10n.in.ewaybill.cancel",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_cancel_ewaybill").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def button_l10n_in_ewaybill_update_part_b(self):
        self.ensure_one()
        return {
            "name": _("Update Part-B or Transporter id"),
            "res_model": "l10n.in.ewaybill.update.partb",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_update_part_b").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def button_l10n_in_extend_ewaybill(self):
        self.ensure_one()
        return {
            "name": _("Extend Eway Bill"),
            "res_model": "l10n.in.ewaybill.extend",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_extend_ewaybill").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def action_view_ewaybills(self):
        self.ensure_one()
        domain = self._get_ewaybill_transaction_domain()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_in_ewaybill.action_ewaybill_list"
        )
        context = literal_eval(action["context"])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def action_print_ewaybill(self):
        return {
            "type": "ir.actions.act_url",
            "url": "https://ewaybillgst.gov.in/Others/EBPrintnew.aspx",
            "target": "new",
        }
