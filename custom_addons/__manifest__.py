# -*- coding: utf-8 -*-
{
    'name': 'Honey Sticks Management System',
    'version': '1.2.0',
    'category': 'Manufacturing',
    'summary': 'Complete enterprise management system for honey sticks production',
    'description': """
        Honey Sticks Management System
        =============================
        
        Complete enterprise management system focused on honey sticks production.
        Includes:
        - Participants and regions management
        - Sales and commissions system
        - Production planning and control
        - Logistics with QR confirmations
        - Marketing and communications
        - Financial management
        - Role-based dashboards
        - Timeline management
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'sale',
        'purchase',
        'stock',
        'mrp',
        'account',
        'mail',
        'website',
        'portal',
        'honey_participants',
        'honey_sales',
        'honey_production',
        'honey_logistics',
        'honey_dashboards',
        'honey_whatsapp',
        'honey_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
