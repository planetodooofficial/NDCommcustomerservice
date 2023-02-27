# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Vinculum',
    'version': '1.0',
    'summary': 'ND Commerce',
    'sequence': 10,
    'description': """Odoo Vinculum Connector""",
    'category': 'PO_Connector',
    'website': 'https://www.odoo.com/app/',
    'depends': ["base", "base_ecommerce", "mail", "stock", "sale"],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_order.xml',
        'wizard/cod_remittance_reconciliation_view.xml',
        'wizard/payment_gateway_reconciliation_view.xml',
        'wizard/payment_reconciliation_marketplace_view.xml',
        'wizard/shipped_and_returned_orders_view.xml',
        'wizard/stock_for_vinculum_view.xml',
        'wizard/import_order_vinculum_files_view.xml',
        'views/inherit_sale_order.xml',
        'views/inherit_shop_instance.xml',
        'views/locations_master_view.xml',
        'views/inherit_sales_channel.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
