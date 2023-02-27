# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Indian Accounting by Planet Odoo',
    'version': '1.1',
    'summary': 'Invoices & Payments',
    'description': """
1. Advances / Proforma Invoices.
2. Partial Booking  - Partial Receipts / Payment for Customer Invoices / Vendors Bills.
3. Payment - Miscellaneous Payments to cover Non-Vendor Related Payments like Salary Payment , TDS / GST / Tax Payments which can be reconciled with Bank reconciliation.
4. Receipt - Miscellaneous Receipts to cover Non-Customer Related Payments like Bank Charges , TDS Receivable , GST Receivable , Other Income which can be reconciled with Bank reconciliation.
5. HSN Code - Supports HSN Masters.
6. Multi Branch Support - Fiscal Position to Support Multi GSTIN and interbranch Transfers in P&L , BS
7. TDS Master - Setup TDS in Vendors.
8. Maker / Checker Support for Accounting Transactions
9. Multi Currency Exchange Rate at Invoice / Bills / Payment / Receipts Level.
    """,
    'sequence': 10,
    'category': 'Accounting/Accounting',
    'website': 'https://planet-odoo.com/',
    'depends': ['base','account','account_accountant', 'sale','l10n_in','purchase','l10n_in_purchase','l10n_in_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/templates.xml',
        'views/account.xml',
        'views/product.xml',
        # 'views/report_bottom2.xml',
        'views/purchase_report.xml',
        'views/partner_views.xml',
        "views/payment.xml",
        "views/account_move.xml",
        'views/payment_term_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_views.xml',
        'wizard/payment_wiz.xml',
        'wizard/send_to_checker.xml'
    ],
    "application": True,
    "installable": True,
}
