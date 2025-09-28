# -*- coding: utf-8 -*-
{
    'name': 'Honey Logistics Management',
    'version': '1.2.0',
    'category': 'Inventory',
    'summary': 'Logistics, packaging, and QR confirmation system for honey sticks',
    'description': """
        Honey Logistics Management
        =========================
        
        This module manages logistics operations for honey sticks:
        - Order fulfillment and packaging
        - QR code generation and confirmation
        - Shipping and tracking
        - Returns and exchanges
        - Logistics KPI tracking
        - Integration with sales and production
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'stock',
        'sale',
        'mail',
        'honey_participants',
        'honey_sales',
        'honey_production',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/shipment_views.xml',
        'views/packaging_views.xml',
        'views/qr_confirmation_views.xml',
        'views/returns_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
