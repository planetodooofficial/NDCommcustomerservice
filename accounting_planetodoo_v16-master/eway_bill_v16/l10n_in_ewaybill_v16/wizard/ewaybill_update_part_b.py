# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nInEwayBillUpdatePartB(models.TransientModel):
    _name = "l10n.in.ewaybill.update.partb"
    _description = "EWay Bill Update Part-B"

    mode = fields.Selection(
        [
            ("0", "Managed by Transporter"),
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
    from_place = fields.Char(
        "From place", help="If empty then value from where goods are transporting"
    )
    from_state_id = fields.Many2one(
        "res.country.state",
        "From State",
        help="If empty then value from where goods are transporting",
        domain=[("country_id.code", "=", "IN")],
    )
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
    transporter_id = fields.Many2one("res.partner", "Transporter")

    def action_ewaybill_update_part_b(self):
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

        docuemnt.write(
            {
                "l10n_in_ewaybill_mode": self.mode,
                "l10n_in_ewaybill_vehicle_no": self.vehicle_no,
                "l10n_in_ewaybill_transporter_doc_no": self.transporter_doc_no,
                "l10n_in_ewaybill_transporter_doc_date": self.transporter_doc_date,
                "l10n_in_ewaybill_transporter_id": self.transporter_id.id,
            }
        )
        docuemnt._validate_l10n_in_ewaybill()
        reason_remark = dict(self._fields["reason_code"].selection).get(
            self.reason_code
        )
        if self.reason_code == "3":
            reason_remark = "Others (%s)" % (self.reason_remark)
        values = {
            "request_type": "update_partb",
            "reason_code": self.reason_code,
            "reason_remark": reason_remark,
            "from_place": self.from_place,
            "from_state_id": self.from_state_id.id,
        }
        ewaybill = docuemnt._generate_ewaybill_transaction(values)
        if self.mode == "0":
            ewaybill.update_part_b_transporter_id()
        else:
            ewaybill.update_part_b()
        return True
