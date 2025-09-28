# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WhatsAppTemplate(models.Model):
    _name = 'honey.whatsapp.template'
    _description = 'WhatsApp Message Templates'

    name = fields.Char(
        string='Template Name',
        required=True
    )
    template_type = fields.Selection([
        ('order_confirmation', 'Order Confirmation'),
        ('shipment_ready', 'Shipment Ready'),
        ('shipment_sent', 'Shipment Sent'),
        ('payment_reminder', 'Payment Reminder'),
        ('custom', 'Custom'),
    ], string='Template Type', required=True)
    
    template_text = fields.Text(
        string='Template Text',
        required=True,
        help='Используйте переменные: {partner_name}, {order_number}, {shipment_number}, {date}'
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Примеры шаблонов
    order_confirmation_template = fields.Text(
        string='Order Confirmation Template',
        default='''
🍯 *Подтверждение заказа*

Здравствуйте, {partner_name}!

Ваш заказ #{order_number} принят в обработку.

Дата заказа: {date}
Сумма: {amount} руб.

Спасибо за выбор наших мёдовых стиков! 🍯

С уважением,
Команда Honey Sticks
        ''',
        help='Шаблон подтверждения заказа'
    )
    
    shipment_ready_template = fields.Text(
        string='Shipment Ready Template',
        default='''
📦 *Отгрузка готова*

Здравствуйте, {partner_name}!

Ваша отгрузка #{shipment_number} готова к отправке.

Дата отгрузки: {date}
Количество коробок: {boxes_count}

Трек-номер: {tracking_number}

Спасибо за сотрудничество! 🍯

С уважением,
Команда Honey Sticks
        ''',
        help='Шаблон уведомления о готовности отгрузки'
    )

    def render_template(self, record):
        """Рендеринг шаблона с данными записи"""
        self.ensure_one()
        
        # Базовые переменные
        variables = {
            'partner_name': record.partner_id.name if hasattr(record, 'partner_id') else record.customer_id.name,
            'date': fields.Date.today().strftime('%d.%m.%Y'),
        }
        
        # Специфичные переменные для разных типов записей
        if hasattr(record, 'name'):
            variables['order_number'] = record.name
            variables['shipment_number'] = record.name
            
        if hasattr(record, 'amount_total'):
            variables['amount'] = f"{record.amount_total:,.2f}"
            
        if hasattr(record, 'boxes_count'):
            variables['boxes_count'] = record.boxes_count
            
        if hasattr(record, 'tracking_number'):
            variables['tracking_number'] = record.tracking_number or 'Будет предоставлен'
        
        # Замена переменных в шаблоне
        rendered_text = self.template_text
        for key, value in variables.items():
            rendered_text = rendered_text.replace(f'{{{key}}}', str(value))
            
        return rendered_text

    @api.model
    def get_template_by_type(self, template_type):
        """Получение активного шаблона по типу"""
        return self.search([
            ('template_type', '=', template_type),
            ('is_active', '=', True)
        ], limit=1)
