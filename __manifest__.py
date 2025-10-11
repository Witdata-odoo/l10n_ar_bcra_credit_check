{
    'name': 'BCRA Credit Check',
    'version': '17.0',
    'category': 'Accounting',
    'summary': 'Consulta el estado crediticio, historial y cheques rechazados del cliente en el BCRA',
    'author': 'Horacio Montaño, Francisco Sulé',
    'depends': ['base', 'account'],
    'data': [
        'views/res_partner_view.xml',
        'views/account_payment_bcra.xml',
        'data/bcra_cron.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
