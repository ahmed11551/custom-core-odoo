# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentCommission(models.Model):
    _name = 'honey.payment.commission'
    _description = 'Payment-based Commission System'
    _order = 'create_date desc'

    # Основные поля
    name = fields.Char(
        string='Commission Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Связанные записи
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='sale_order_id.partner_id',
        store=True
    )
    
    # Участники
    manager_id = fields.Many2one(
        'res.users',
        string='Sales Manager',
        required=True
    )
    agent_id = fields.Many2one(
        'honey.agent',
        string='Sales Agent',
        required=True
    )
    
    # Финансовые данные
    order_amount = fields.Float(
        string='Order Amount',
        related='sale_order_id.amount_total',
        store=True
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        required=True,
        digits=(5, 2)
    )
    commission_amount = fields.Float(
        string='Commission Amount',
        compute='_compute_commission_amount',
        store=True
    )
    
    # КРИТИЧЕСКИ ВАЖНО: Комиссия начисляется только после оплаты
    payment_confirmed = fields.Boolean(
        string='Payment Confirmed',
        default=False,
        help='Комиссия начисляется только после подтверждения оплаты директором'
    )
    payment_date = fields.Date(
        string='Payment Date',
        help='Дата поступления оплаты на счет'
    )
    payment_amount = fields.Float(
        string='Payment Amount',
        help='Сумма поступившей оплаты'
    )
    payment_reference = fields.Char(
        string='Payment Reference',
        help='Номер платежного документа'
    )
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Card Payment'),
        ('other', 'Other'),
    ], string='Payment Method')
    
    # Статус
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Даты
    commission_date = fields.Date(
        string='Commission Date',
        default=fields.Date.today
    )
    payment_confirmation_date = fields.Date(
        string='Payment Confirmation Date'
    )
    
    # Примечания
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('order_amount', 'commission_rate')
    def _compute_commission_amount(self):
        for record in self:
            record.commission_amount = record.order_amount * (record.commission_rate / 100)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.payment.commission') or _('New')
        return super().create(vals)

    def action_confirm_payment(self):
        """Подтверждение оплаты директором - КЛЮЧЕВАЯ ФУНКЦИЯ"""
        for record in self:
            if not record.payment_confirmed:
                record.payment_confirmed = True
                record.payment_confirmation_date = fields.Date.today()
                record.state = 'confirmed'
                
                # Уведомление менеджера и агента о начислении комиссии
                record._notify_commission_earned()

    def action_confirm(self):
        """Подтвердить комиссию (только после оплаты)"""
        for record in self:
            if not record.payment_confirmed:
                raise ValidationError(_('Commission can only be confirmed after payment is confirmed by director.'))
            if record.state != 'draft':
                raise ValidationError(_('Only draft commissions can be confirmed.'))
            record.state = 'confirmed'

    def action_pay(self):
        """Отметить комиссию как выплаченную"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_('Only confirmed commissions can be paid.'))
            record.state = 'paid'

    def action_cancel(self):
        """Отменить комиссию"""
        for record in self:
            if record.state == 'paid':
                raise ValidationError(_('Cannot cancel paid commissions.'))
            record.state = 'cancelled'

    def _notify_commission_earned(self):
        """Уведомление о начислении комиссии"""
        for record in self:
            # Создание уведомления для менеджера
            self.env['mail.message'].create({
                'subject': f'Комиссия начислена - {record.name}',
                'body': f'Вам начислена комиссия в размере {record.commission_amount:,.2f} руб. за заказ {record.sale_order_id.name}',
                'partner_ids': [(4, record.manager_id.partner_id.id)],
                'model': 'honey.payment.commission',
                'res_id': record.id,
            })
            
            # Создание уведомления для агента
            if record.agent_id.user_id:
                self.env['mail.message'].create({
                    'subject': f'Комиссия начислена - {record.name}',
                    'body': f'Вам начислена комиссия в размере {record.commission_amount:,.2f} руб. за заказ {record.sale_order_id.name}',
                    'partner_ids': [(4, record.agent_id.user_id.partner_id.id)],
                    'model': 'honey.payment.commission',
                    'res_id': record.id,
                })

    @api.model
    def get_monthly_commissions(self, user_id, month, year):
        """Получение комиссий за месяц для пользователя"""
        start_date = fields.Date.today().replace(day=1, month=month, year=year)
        end_date = (start_date + fields.timedelta(days=32)).replace(day=1) - fields.timedelta(days=1)
        
        return self.search([
            '|',
            ('manager_id', '=', user_id),
            ('agent_id.user_id', '=', user_id),
            ('payment_confirmed', '=', True),
            ('commission_date', '>=', start_date),
            ('commission_date', '<=', end_date),
        ])

    @api.model
    def get_pending_payments(self):
        """Получение заказов ожидающих подтверждения оплаты"""
        return self.search([
            ('state', '=', 'draft'),
            ('payment_confirmed', '=', False)
        ])

    @api.model
    def create_from_sale_order(self, sale_order):
        """Создание комиссии из заказа продаж"""
        # Получение настроек комиссий
        manager_rate = self.env['ir.config_parameter'].sudo().get_param('honey_sales.manager_commission_rate', 5.0)
        agent_rate = self.env['ir.config_parameter'].sudo().get_param('honey_sales.agent_commission_rate', 3.0)
        
        # Создание комиссии для менеджера
        if sale_order.user_id:
            self.create({
                'sale_order_id': sale_order.id,
                'manager_id': sale_order.user_id.id,
                'agent_id': sale_order.honey_agent_id.id if hasattr(sale_order, 'honey_agent_id') else False,
                'commission_rate': float(manager_rate),
                'state': 'pending_payment',
            })
        
        # Создание комиссии для агента
        if hasattr(sale_order, 'honey_agent_id') and sale_order.honey_agent_id:
            self.create({
                'sale_order_id': sale_order.id,
                'manager_id': sale_order.user_id.id,
                'agent_id': sale_order.honey_agent_id.id,
                'commission_rate': float(agent_rate),
                'state': 'pending_payment',
            })
