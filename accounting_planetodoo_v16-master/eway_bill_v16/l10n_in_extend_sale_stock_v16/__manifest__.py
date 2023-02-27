# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Indian - E-Invoice Sale, stock",
    "version": "1.0",
    "description": """
E-invoice using Sale stock
================================

If invoice is create from sale,
then set dispatch address from warehouse address if available.
if we found more then one warehouse for single invoice then we don't set dispatch address.
So in this case select dispatch address manually.
    """,
    "category": "Accounting/Accounting",
    "depends": ["l10n_in_extend_v16", 'sale_stock'],
    "data": [
        'wizard/sale_make_invoice_advance_views.xml',
    ],
    "installable": True,
    "license": "OEEL-1",
}
