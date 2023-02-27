# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Indian - E Invoice",
    "version": "1.0",
    "description": """
E-invoice for India
================================

This module is connect with ODOO IAP
Government API version is 1.01
    """,
    "category": "Accounting/Accounting",
    "depends": ["l10n_in_extend_v16"],
    "data": [
        "security/ir.model.access.csv",
        # "data/account_tax_template_data.xml",
        "data/account_invoice_json.xml",
        "views/account_move_views.xml",
        "views/report_invoice.xml",
        "wizard/generate_token_wizard_views.xml",
        "wizard/einvoice_cancel_wizard_views.xml",
        "wizard/einvoice_cancel_wizard_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "license": "OEEL-1",
}
