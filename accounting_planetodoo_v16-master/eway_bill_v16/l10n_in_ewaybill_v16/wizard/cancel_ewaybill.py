# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import UserError


class L10nInEwayBillCancel(models.TransientModel):
    _name = "l10n.in.ewaybill.cancel"
    _description = "Cancel EWay Bill"

    reason_code = fields.Selection(
        [
            ("1", "Duplicate"),
            ("2", "Order Cancelled"),
            ("3", "Data Entry mistake"),
            ("4", "Others"),
        ],
        "Cancel Reason",
    )
    cancel_remark = fields.Char("Cancel Remark")

    def action_cancel_ewaybill(self):
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

        values = {
            "request_type": "cancel",
            "cancel_reason_code": self.reason_code,
        }
        if self.reason_code == "4":
            values.update({"cancel_remark": self.cancel_remark})

        ewaybill = docuemnt._generate_ewaybill_transaction(values)
        ewaybill.cancel()
