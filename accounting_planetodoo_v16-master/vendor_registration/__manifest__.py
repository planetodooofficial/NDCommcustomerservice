{
    'name': 'Vendor Registration',
    'sequence': 1,
    'version': '1.1',
    'author': 'Planet Odoo',
    'description': """Vendor Registration""",
    'category': '',
    'website': '',
    'depends': [
        'base', 'account', 'l10n_in', 'l10n_in_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/partner.xml',
        'views/template.xml',
        'views/bank.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
