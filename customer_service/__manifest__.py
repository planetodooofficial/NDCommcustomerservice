{
    'name': 'Customer Service',
    'version': '1.0',
    'summary': 'Customer Service',
    'sequence': -100,
    'description': """Customer Service""",
    'category': '',
    'website': 'https://www.odoo.com/app/',
    'depends': ["base", "sale", "l10n_in_sale", "delivery","account","crm","odoo_vinculum_connector"],
    'data': [
        'security/ir.model.access.csv',
        'wizard/bulk_cancellation_view.xml',
        'wizard/bulk_rto_request.xml',
        'wizard/bulk_refund.xml',
        'wizard/return_wizard.xml',
        'wizard/reason_wizard.xml',
        'views/customer_service.xml',
        'views/cancellation_request.xml',
        'views/rto_request.xml',
        'views/return.xml',
        'views/refund.xml',
        'views/email_template.xml',
        'views/customer_service_groups.xml',
        # 'views/account_inherit.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
