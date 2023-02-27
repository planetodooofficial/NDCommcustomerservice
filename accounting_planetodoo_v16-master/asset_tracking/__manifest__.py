
{
    'name': 'Asset Tracking',
    'version': '14.0',
    'summary': 'Asset Tracking',
    'description': 'Partner Ledger Report',
    'author': 'Planet Odoo',
    'maintainer': 'Planetodoo',
    'company': 'PlanetOdoo',
    'website': 'https://planet-odoo.com/',
    'depends': ['base', 'account','account_asset','maintenance','hr'],
    'category': 'Accounting',
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/asset_masters.xml',
        'views/account_asset_views.xml'
             ],
    'installable': True,
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
