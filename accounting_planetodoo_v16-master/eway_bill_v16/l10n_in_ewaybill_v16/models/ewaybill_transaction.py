# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import html2text
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

TEMPLATES = {
    "generate": "l10n_in_ewaybill.l10n_in_ewaybill_generate_json",
    "cancel": "l10n_in_ewaybill.l10n_in_ewaybill_cancel_json",
    "update_partb": "l10n_in_ewaybill.l10n_in_ewaybill_update_part_b_json",
    "extend_date": "l10n_in_ewaybill.l10n_in_ewaybill_extend_json",
}


class EwayBill(models.Model):
    _name = "l10n.in.ewaybill.transaction"
    _description = "India EWay Bill transaction"
    _rec_name = "ewaybill_number"
    _order = "create_date DESC"

    move_id = fields.Many2one("account.move", string="Invoice")

    # state = fields.Selection([
    #     ('process', 'In Progress'),
    #     ('done', 'Done'),
    #     ], default='process', string='Status')

    request_json = fields.Text(
        "Request (JSON)", compute="_compute_request_json", store=True
    )

    response_json = fields.Text("Response (JSON)")

    request_type = fields.Selection(
        [
            ("generate", "Generate eWayBill or Part A"),
            ("cancel", "Cancel eWayBill"),
            ("update_partb", "Update eWayBill Part-B"),
            ("extend_date", "Extend eWayBill Validaty"),
        ],
        string="eWayBill Type",
        required=True,
    )

    # Get details from response
    ewaybill_number = fields.Char(
        compute="_compute_ewaybill_details", string="eWaybill Number"
    )

    ewaybill_valid_upto = fields.Datetime(
        compute="_compute_ewaybill_details", string="Valid Upto"
    )

    # Cancel eWay Bill
    cancel_reason_code = fields.Selection(
        [
            ("1", "Duplicate"),
            ("2", "Order Cancelled"),
            ("3", "Data Entry mistake"),
            ("4", "Others"),
        ],
        "Cancel Reason",
    )
    cancel_remark = fields.Char("Cancel Remark")

    # eWay Bill Update Part-B
    reason_code = fields.Selection(
        [
            ("1", "Due to Break Down"),
            ("2", "Due to Transhipment"),
            ("3", "Others"),
            ("4", "First Time"),
        ],
        "Reason",
    )
    reason_remark = fields.Char("Reason Remark")

    # Extend eWay Bill + eWay Bill Update Part-B
    from_place = fields.Char("From Place")
    from_state_id = fields.Many2one(
        "res.country.state", "From State", domain=[("country_id.code", "=", "IN")]
    )

    # Extend eWay Bill
    from_pincode = fields.Char("From Pincode")
    remaining_distance = fields.Char("Remaining Distance")
    extn_reason_code = fields.Selection(
        [
            ("1", "Natural Calamity"),
            ("2", "Law and Order Situation"),
            ("4", "Transhipment"),
            ("5", "Accident"),
            ("99", "Other"),
        ],
        "Extend Reason",
    )
    extn_remarks = fields.Char("Extend Remarks")
    consignment_status = fields.Selection(
        [("M", "In Movement"), ("T", "In Transit")], "Consignment Status"
    )
    transit_type = fields.Selection(
        [("R", "Road"), ("W", "Warehouse"), ("O", "Others")], "Transit Type"
    )
    street = fields.Char("Stree")
    street2 = fields.Char("Stree2")
    street3 = fields.Char("Stree3")

    def _get_last_generate_request(self):
        last_generate_request = self.search(
            [
                ("move_id", "=", self.move_id.id),
                ("request_type", "=", "generate"),
            ],
            limit=1,
        )
        return last_generate_request

    @api.depends("response_json")
    def _compute_ewaybill_details(self):
        for transaction in self:
            response = (
                transaction.response_json
                and json.loads(transaction.response_json)
                or {}
            )
            if not response:
                last_generate_request = self._get_last_generate_request()
                response = json.loads(last_generate_request.response_json)
            transaction.ewaybill_number = False
            transaction.ewaybill_valid_upto = False
            if response.get("ewayBillNo", False):
                transaction.ewaybill_number = response.get("ewayBillNo")
            if (
                response.get("validUpto", False)
                and transaction.request_type != "cancel"
            ):
                transaction.ewaybill_valid_upto = datetime.strptime(
                    response.get("validUpto"), "%d/%m/%Y %H:%M:%S %p"
                )

    def _prepare_compute_request_json_template_values(self):
        self.ensure_one()
        return {
            "transaction": self,
            "document": self.move_id,
            "document_line": self.move_id.invoice_line_ids,
            "is_invoice": self.move_id and True or False,
        }

    @api.depends("move_id")
    def _compute_request_json(self):
        """Render account_eway_bill_json.xml template and returns the json data required to generate the eWayBill"""

        for transaction in self:
            template = TEMPLATES.get(transaction.request_type)
            values = transaction._prepare_compute_request_json_template_values()
            request_json = self.env["ir.ui.view"]._render_template(template, values)
            # raise UserError(request_json)
            # request_json = request_json.decode("utf-8")
            request_json = request_json
            json_dumps = json.dumps(safe_eval(request_json))
            json_dumps = html2text.html2text(json_dumps)
            json_dumps = json_dumps.replace("\n", "")
            transaction.request_json = json_dumps

    def _get_company_partner(self):
        self.ensure_one()
        company_partner_id = self.move_id.journal_id.company_id.partner_id
        if self.move_id.journal_id.l10n_in_gstin_partner_id:
            company_partner_id = self.move_id.journal_id.l10n_in_gstin_partner_id
        return company_partner_id

    def submit(self):
        """Submit the json data to stored in request_json field and get the generated data
        {
            'ewayBillNo': Number,
            'validUpto': Valid Until Date,
        }
        For more information: https://mastergst.com/e-way-bill/e-way-bill-api.html"""

        self.ensure_one()
        WaybillService = self.env["l10n.in.ewaybill.service"]

        service = WaybillService.get_service(self._get_company_partner())

        response = service.submit(transaction_id=self)

        if not response:
            raise UserError(_("Could not submited Eway bill."))

        response = response.get("data", {})
        self.response_json = json.dumps(response)

        return response

    def cancel(self):
        self.ensure_one()
        WaybillService = self.env["l10n.in.ewaybill.service"]
        service = WaybillService.get_service(self._get_company_partner())

        response = service.cancel(transaction_id=self)

        if not response:
            raise UserError(_("Could not cancel Eway bill."))

        response = response.get("data", {})
        self.response_json = json.dumps(response)

        return response

    def update_part_b(self):
        self.ensure_one()
        WaybillService = self.env["l10n.in.ewaybill.service"]
        service = WaybillService.get_service(self._get_company_partner())

        response = service.update_part_b(transaction_id=self)

        if not response:
            raise UserError(_("Could not Update Part-B of Eway bill."))

        response = response.get("data", {})
        self.response_json = json.dumps(response)
        return response

    def update_part_b_transporter_id(self):
        self.ensure_one()
        WaybillService = self.env["l10n.in.ewaybill.service"]
        service = WaybillService.get_service(self._get_company_partner())

        response = service.update_part_b_transporter_id(transaction_id=self)

        if not response:
            raise UserError(_("Could not Update Part-B/Transporter Id of Eway bill."))

        response = response.get("data", {})
        # response.update({'ewayBillNo': self.ewaybill_number})
        self.response_json = json.dumps(response)
        return response

    def extend(self):
        self.ensure_one()
        WaybillService = self.env["l10n.in.ewaybill.service"]
        service = WaybillService.get_service(self._get_company_partner())

        response = service.extend(transaction_id=self)

        if not response:
            raise UserError(_("Could not extend Eway bill."))

        response = response.get("data", {})
        self.response_json = json.dumps(response)
        return response

    def _get_source_document(self):
        self.ensure_one()
        source_document = ""
        if self.move_id and self.move_id.is_purchase_document(include_receipts=True):
            source_document = self.move_id.ref
        elif self.move_id:
            source_document = self.move_id.name
        return source_document
