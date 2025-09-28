# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json


class WhatsAppMessage(models.Model):
    _name = 'honey.whatsapp.message'
    _description = 'WhatsApp Messages'
    _order = 'message_date desc'

    # Основные поля
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        help='Клиент для которого предназначено сообщение'
    )
    message_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], string='Message Type', required=True, default='outgoing')
    
    # Содержимое сообщения
    message_text = fields.Text(
        string='Message Text',
        required=True
    )
    message_date = fields.Datetime(
        string='Message Date',
        default=fields.Datetime.now,
        required=True
    )
    
    # WhatsApp данные
    whatsapp_id = fields.Char(
        string='WhatsApp Message ID',
        help='Уникальный ID сообщения в WhatsApp'
    )
    phone_number = fields.Char(
        string='Phone Number',
        related='partner_id.phone',
        store=True
    )
    
    # Статус сообщения
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', tracking=True)
    
    # Связанные документы
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order'
    )
    shipment_id = fields.Many2one(
        'honey.shipment',
        string='Shipment'
    )
    
    # Медиа файлы
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Attachments',
        domain=[('res_model', '=', 'honey.whatsapp.message')]
    )
    
    # Автоматические уведомления
    is_auto_notification = fields.Boolean(
        string='Auto Notification',
        default=False,
        help='Автоматическое уведомление'
    )
    notification_type = fields.Selection([
        ('order_confirmation', 'Order Confirmation'),
        ('shipment_ready', 'Shipment Ready'),
        ('shipment_sent', 'Shipment Sent'),
        ('payment_reminder', 'Payment Reminder'),
        ('custom', 'Custom'),
    ], string='Notification Type')

    @api.model
    def create(self, vals):
        """Создание сообщения с автоматической отправкой"""
        message = super().create(vals)
        if message.message_type == 'outgoing' and message.status == 'draft':
            message.action_send()
        return message

    def action_send(self):
        """Отправка сообщения через WhatsApp API"""
        for message in self:
            if message.status != 'draft':
                continue
                
            try:
                # Здесь должна быть интеграция с WhatsApp Business API
                # Для демонстрации просто меняем статус
                message.status = 'sent'
                message.whatsapp_id = f"WA_{message.id}_{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Логирование отправки
                message._log_activity('message_sent', f'Message sent to {message.partner_id.name}')
                
            except Exception as e:
                message.status = 'failed'
                raise ValidationError(_('Failed to send message: %s') % str(e))

    def action_mark_as_read(self):
        """Отметить сообщение как прочитанное"""
        for message in self:
            if message.status in ['sent', 'delivered']:
                message.status = 'read'

    def action_mark_as_delivered(self):
        """Отметить сообщение как доставленное"""
        for message in self:
            if message.status == 'sent':
                message.status = 'delivered'

    def _log_activity(self, activity_type, note):
        """Логирование активности"""
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f'WhatsApp: {note}',
            'note': note,
            'res_id': self.id,
            'res_model': self._name,
            'user_id': self.env.user.id,
        })

    @api.model
    def send_order_confirmation(self, sale_order):
        """Отправка подтверждения заказа"""
        template = self.env['honey.whatsapp.template'].search([
            ('template_type', '=', 'order_confirmation')
        ], limit=1)
        
        if not template:
            return False
            
        message_text = template.render_template(sale_order)
        
        return self.create({
            'partner_id': sale_order.partner_id.id,
            'message_type': 'outgoing',
            'message_text': message_text,
            'sale_order_id': sale_order.id,
            'is_auto_notification': True,
            'notification_type': 'order_confirmation',
            'status': 'draft',
        })

    @api.model
    def send_shipment_notification(self, shipment):
        """Отправка уведомления об отгрузке"""
        template = self.env['honey.whatsapp.template'].search([
            ('template_type', '=', 'shipment_ready')
        ], limit=1)
        
        if not template:
            return False
            
        message_text = template.render_template(shipment)
        
        return self.create({
            'partner_id': shipment.customer_id.id,
            'message_type': 'outgoing',
            'message_text': message_text,
            'shipment_id': shipment.id,
            'is_auto_notification': True,
            'notification_type': 'shipment_ready',
            'status': 'draft',
        })

    def action_reply(self):
        """Ответ на сообщение"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reply to WhatsApp Message'),
            'res_model': 'honey.whatsapp.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_message_type': 'outgoing',
                'default_sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
                'default_shipment_id': self.shipment_id.id if self.shipment_id else False,
            }
        }
