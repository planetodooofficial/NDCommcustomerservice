{
    'name': 'SLC Custom',
    'version': '15.0.0.0',
    'sequence': 10,
    'category': '',
    'summary': '',
    'description': """""",
    'author': 'PlanetOdoo',
    'depends': ['base', 'purchase', 'stock', 'mail', 'portal', 'mrp', 'sale', 'web'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/notification_master.xml",
        "views/hsn_master.xml",
        "views/notification_master.xml",
        "views/notification_serial_master.xml",
        "views/bond_master.xml",
        "views/commisionerate_master.xml",
        "views/customs_station.xml",
        "views/stock_lot_view.xml",
        "views/eximtransaction_sub_category.xml",
        "views/product_template.xml",
        "views/inventory.xml",
        "views/purchase.xml",
        "views/product_category.xml",
        "views/manufacturing.xml",
        "views/import_po.xml",
        "views/stock_picking.xml",
        "views/inherit_sale.xml",
        "views/inherit_stock_picking_type.xml",
        "views/non_moowr.xml",
        "views/notification_master_tag.xml",
        "views/cost_dimension.xml",
        "views/dashboard_master_menu.xml",
        # "views/assets.xml",
        # "views/inherit_res_user.xml",

    ],
    "assets": {
        "web.assets_backend": [
            # 'slc_custom/static/src/scss/custom.scss'

        ],
        "web.assets_qweb": [
        ],
    },
    'website': 'https://planet-odoo.com/',
    'installable': True,
    'auto_install': False,
}
