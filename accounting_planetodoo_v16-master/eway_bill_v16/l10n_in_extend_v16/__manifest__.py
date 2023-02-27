# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Indian - Accounting extend",
    "version": "2.0",
    "description": """
Indian Accounting extend.
====================================

This module create tax lines per invoice lines

""",
    "category": "Accounting/Localizations",
    "depends": [
        "l10n_in",
    ],
    "data": [
        "data/account_data.xml",
        "data/account_tax_template_data.xml",
        "data/res_country_state_data.xml",
        "views/account_invoice_views.xml",
        "views/report_invoice.xml",
    ],
    "installable": True,
    'license': 'OEEL-1',
}
