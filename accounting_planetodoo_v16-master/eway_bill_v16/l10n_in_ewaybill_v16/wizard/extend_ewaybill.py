# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nInEwayBillExtend(models.TransientModel):
    _name = "l10n.in.ewaybill.extend"
    _description = "Extend EWay Bill"

    """
    During the extension of the e-way bill,
    the user is prompted to answer whether the Consignment is in Transit or in Movement.
    On selection of In Transit, the address details of the transit place need to be provided.
    On selection of In Movement the system will prompt the user to enter the Place and Vehicle details from where the extension is required.
    In both these scenarios, the destination PIN will be considered from the PART-A of the E-way Bill for calculation of distance for movement and validity date.
    """

    street = fields.Char("Stree")
    street2 = fields.Char("Stree2")
    street3 = fields.Char("Stree3")
    from_place = fields.Char("Cureent Place", required=True)
    from_state_id = fields.Many2one(
        "res.country.state",
        "Cureent State",
        domain=[("country_id.code", "=", "IN")],
        required=True,
    )
    from_pincode = fields.Char("Cureent Pincode", required=True)
    remaining_distance = fields.Char("Remaining Distance", required=True)
    reason_code = fields.Selection(
        [
            ("1", "Natural Calamity"),
            ("2", "Law and Order Situation"),
            ("4", "Transhipment"),
            ("5", "Accident"),
            ("99", "Other"),
        ],
        "Extend Reason",
        required=True,
    )
    remarks = fields.Char("Extend Remarks")
    consignment_status = fields.Selection(
        [("M", "In Movement"), ("T", "In Transit")], "Consignment Status", required=True
    )
    transit_type = fields.Selection(
        [("R", "Road"), ("W", "Warehouse"), ("O", "Others")], "Transit Type"
    )
    mode = fields.Selection(
        [
            ("1", "Road"),
            ("2", "Rail"),
            ("3", "Air"),
            ("4", "Ship"),
        ],
        "Transportation Mode",
    )
    vehicle_no = fields.Char("Vehicle No")
    transporter_doc_no = fields.Char(
        "Document No",
        help="""Transporter document number.
If it is more than 15 chars, last 15 chars may be entered""",
    )
    transporter_doc_date = fields.Date(
        "Document Date", help="Date on the transporter document"
    )

    def action_extend_ewaybill(self):
        context = self.env.context
        if context.get("active_model") not in ("stock.picking", "account.move"):
            raise UserError(
                _(
                    "The cancel eway bill wizard should only be called on account.move or stock.picking records."
                )
            )
        docuemnt = self.env[context.get("active_model")].browse(
            context.get("active_id")
        )

        extn_remarks = dict(self._fields["reason_code"].selection).get(self.reason_code)
        if self.reason_code == "99":
            extn_remarks = self.extn_remarks
        docuemnt.write(
            {
                "l10n_in_ewaybill_mode": self.mode,
                "l10n_in_ewaybill_vehicle_no": self.vehicle_no,
                "l10n_in_ewaybill_transporter_doc_no": self.transporter_doc_no,
                "l10n_in_ewaybill_transporter_doc_date": self.transporter_doc_date,
            }
        )
        values = {
            "request_type": "extend_date",
            "from_place": self.from_place,
            "from_state_id": self.from_state_id.id,
            "from_pincode": self.from_pincode,
            "remaining_distance": self.remaining_distance,
            "extn_reason_code": self.reason_code,
            "extn_remarks": extn_remarks,
            "transit_type": self.transit_type,
            "consignment_status": self.consignment_status,
            "street": self.street,
            "street2": self.street2,
            "street3": self.street3,
        }

        ewaybill = docuemnt._generate_ewaybill_transaction(values)
        ewaybill.extend()
        return True
