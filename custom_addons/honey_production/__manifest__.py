# -*- coding: utf-8 -*-
{
    'name': 'Honey Production Management',
    'version': '1.2.0',
    'category': 'Manufacturing',
    'summary': 'Production planning and control for honey sticks manufacturing',
    'description': """
        Honey Production Management
        ==========================
        
        This module manages honey sticks production:
        - Production batch planning and control
        - Material requirements and availability
        - Time tracking and labor management
        - Quality control and batch tracking
        - Production scheduling and timeline
        - Integration with sales and logistics
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'mrp',
        'stock',
        'hr',
        'mail',
        'honey_participants',
        'honey_sales',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/production_batch_views.xml',
        'views/batch_search_wizard_views.xml',
        'views/quality_control_views.xml',
        'views/material_views.xml',
        'views/time_tracking_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
