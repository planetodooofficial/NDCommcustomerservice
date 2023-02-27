# -*- coding: utf-8 -*-
{
    'name': "eWayBill for India (stock)",

    'summary': """
        Create an eWayBill to transer the goods in India""",

    'description': """
        This module Create an eWayBill from Invoice and bill
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["stock", "l10n_in_ewaybill_v16"],

    # always loaded
    'data': [
        "views/stock_picking_view.xml",
        "views/ewaybill_transaction_views.xml",
        "report/report_deliveryslip.xml",
        "report/report_stockpicking_operations.xml",
    ],
    "installable": True,
    "auto_install": True,
    'license': 'OEEL-1',
}
