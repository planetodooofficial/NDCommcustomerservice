# -*- coding: utf-8 -*-
{
    'name': "eWayBill for India (Sale-Stock)",

    'summary': """
        Create an eWayBill to transer the goods in India""",

    'description': """
        This module link Sale invoice and stock picking to get bill and ship address
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["sale", "l10n_in_ewaybill_v16", "l10n_in_ewaybill_stock_v16"],

    "installable": True,
    "auto_install": True,
    'license': 'OEEL-1',
}
