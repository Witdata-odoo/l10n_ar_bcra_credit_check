{
    'name': 'BCRA Credit Check',
    'version': '19.0.1.1.0',
    'category': 'Accounting',
    'images':['static/description/main_screenshot.png'],
    'summary': 'Consulta el estado crediticio, historial y cheques rechazados del cliente en el BCRA',
    'author': 'Horacio Montaño, Francisco Sulé, Ariel Ameghino',
    'depends': ['account','contacts'],
    'data': [
        'views/res_partner_view.xml',
        'views/account_payment_bcra.xml',
        'data/bcra_cron.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
