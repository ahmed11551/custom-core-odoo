# -*- coding: utf-8 -*-
{
    'name': 'Honey Sales Management',
    'version': '1.2.0',
    'category': 'Sales',
    'summary': 'Sales orders, commissions and regional management for honey sticks',
    'description': """
        Honey Sales Management
        =====================
        
        This module extends Odoo sales functionality for honey sticks business:
        - Enhanced sales orders with regional and agent assignment
        - Commission calculation and tracking
        - QR confirmation workflow
        - Regional sales analytics
        - Agent performance tracking
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'sale',
        'stock',
        'account',
        'mail',
        'honey_participants',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/sale_order_views.xml',
        'views/commission_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
