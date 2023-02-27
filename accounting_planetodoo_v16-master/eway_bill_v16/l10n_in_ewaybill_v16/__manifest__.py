# -*- coding: utf-8 -*-
{
    'name': "eWayBill for India",

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
    'depends': ['l10n_in', 'l10n_in_extend_v16'],

    # always loaded
    'data': [
        "security/ir.model.access.csv",
        "data/ewaybill_type_data.xml",
        "data/ewaybill_generate_json.xml",
        "data/ewaybill_cancel_json.xml",
        "data/ewaybill_update_part_b_json.xml",
        "data/ewaybill_extend_json.xml",
        "views/ewaybill_transaction_views.xml",
        "views/account_move_views.xml",
        "wizard/generate_token_wizard_views.xml",
        "wizard/cancel_ewaywill_wizard_views.xml",
        "wizard/ewaybill_update_part_b_wizard_views.xml",
        "wizard/extend_ewaybill_wizard_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    'license': 'OEEL-1',
}
