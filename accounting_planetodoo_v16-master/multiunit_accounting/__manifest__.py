# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Multi-Unit Accounting',
    'version': '1.1',
    'summary': 'Taxes & Ledgers',
    'description': """
    Create Taxes,Fiscal Positions and Ledgers for each GSTIN Unit
    """,
    'sequence': 10,
    'category': 'Accounting/Accounting',
    'website': 'https://planet-odoo.com/',
    'depends': ['base','account','account_accountant','l10n_in','po_accounting_v16'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/gstin_data_views.xml',
        'views/account_views.xml'
    ],
    "application": True,
    "installable": True,
}
