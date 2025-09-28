# -*- coding: utf-8 -*-
{
    'name': 'Honey Reports and Printing',
    'version': '1.2.0',
    'category': 'Reporting',
    'summary': 'Reports and printing for Honey Sticks Management System',
    'description': """
        Honey Reports and Printing Module
        =================================
        
        Модуль отчётов и печати для системы управления мёдовыми стиками.
        Включает:
        - Lieferschein (накладные) с QR кодами
        - Этикетки коробок A6
        - Отчёты по производству
        - Отчёты по комиссиям
        - Отчёты по логистике
        - QR код генерация
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'sale',
        'stock',
        'honey_participants',
        'honey_sales',
        'honey_production',
        'honey_logistics',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/lieferschein_report.xml',
        'reports/box_label_report.xml',
        'reports/production_report.xml',
        'reports/commission_report.xml',
        'reports/shipment_report.xml',
        'views/report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
