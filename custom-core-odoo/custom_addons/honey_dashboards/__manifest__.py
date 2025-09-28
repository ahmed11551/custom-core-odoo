# -*- coding: utf-8 -*-
{
    'name': 'Honey Dashboards',
    'version': '1.2.0',
    'category': 'Dashboards',
    'summary': 'Role-based dashboards for Honey Sticks management system',
    'description': """
        Honey Dashboards
        ================
        
        This module provides role-based dashboards for the Honey Sticks management system:
        - Director Executive Dashboard
        - Sales Manager Dashboard
        - Sales Agent Dashboard
        - Production Dashboard
        - Logistics Dashboard
        
        Each dashboard is customized for specific user roles and responsibilities.
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'web',
        'mail',
        'honey_participants',
        'honey_sales',
        'honey_production',
        'honey_logistics',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/director_dashboard.xml',
        'views/manager_dashboard.xml',
        'views/agent_dashboard.xml',
        'views/production_dashboard.xml',
        'views/logistics_dashboard.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
