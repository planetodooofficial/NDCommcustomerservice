{
    'name': 'State Configuration',
    'sequence': 1,
    'category': 'All',
    'description': 'State Configuration',
    'website': 'https://www.planet-odoo.com/',
    'author': 'Planet Odoo',
    'depends': ['base'],
    'data': [
        "security/ir.model.access.csv",
        "wizard/state_config_view.xml",
        ],
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}

