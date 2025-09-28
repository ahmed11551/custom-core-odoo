# -*- coding: utf-8 -*-
{
    'name': 'Honey WhatsApp Integration',
    'version': '1.2.0',
    'category': 'Communication',
    'summary': 'WhatsApp integration for Honey Sticks Management System',
    'description': """
        WhatsApp Integration Module
        ==========================
        
        Интеграция с WhatsApp для системы управления мёдовыми стиками.
        Включает:
        - Отправка сообщений клиентам
        - Получение сообщений от клиентов
        - История переписки
        - Автоматические уведомления
        - Интеграция с заказами и отгрузками
    """,
    'author': 'Honey Sticks Company',
    'website': 'https://www.honeysticks.com',
    'depends': [
        'base',
        'mail',
        'honey_participants',
        'honey_sales',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_message_views.xml',
        'views/whatsapp_template_views.xml',
        'data/whatsapp_template_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
