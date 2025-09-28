# -*- coding: utf-8 -*-
{
    'name': 'Honey Participants Management',
    'version': '1.2.0',
    'category': 'Sales',
    'summary': 'Management of participants, regions, and agents',
    'description': """
        Honey Participants Management
        ============================
        
        This module manages:
        - Participants (employees, customers, suppliers)
        - Regions and territories
        - Agents and managers assignment
        - Commission settings
        - Regional analytics
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'sale',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/region_views.xml',
        'views/participant_views.xml',
        'views/agent_views.xml',
        'views/commission_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
