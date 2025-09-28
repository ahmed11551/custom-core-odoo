# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Commission(models.Model):
    _name = 'honey.commission'
    _description = 'Sales Commission'
    _order = 'date desc'

    name = fields.Char(
        string='Commission Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    agent_id = fields.Many2one(
        'honey.agent',
        string='Agent',
        required=True
    )
    region_id = fields.Many2one(
        'honey.region',
        string='Region',
        related='agent_id.region_id',
        store=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='sale_order_id.partner_id',
        store=True
    )
    
    # Commission calculation
    base_amount = fields.Float(
        string='Base Amount',
        digits=(16, 2),
        required=True
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(5, 2),
        required=True
    )
    amount = fields.Float(
        string='Commission Amount',
        digits=(16, 2),
        compute='_compute_amount',
        store=True
    )
    
    # Status and dates
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    date = fields.Date(
        string='Commission Date',
        required=True,
        default=fields.Date.today
    )
    payment_date = fields.Date(
        string='Payment Date'
    )
    
    # QR confirmation tracking
    qr_confirmed = fields.Boolean(
        string='QR Confirmed',
        default=False,
        tracking=True
    )
    qr_confirmation_date = fields.Datetime(
        string='QR Confirmation Date'
    )
    
    # Return handling
    return_amount = fields.Float(
        string='Return Amount',
        digits=(16, 2),
        default=0.0
    )
    adjusted_amount = fields.Float(
        string='Adjusted Amount',
        digits=(16, 2),
        compute='_compute_adjusted_amount',
        store=True
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('base_amount', 'commission_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.base_amount * (record.commission_rate / 100)

    @api.depends('amount', 'return_amount')
    def _compute_adjusted_amount(self):
        for record in self:
            record.adjusted_amount = record.amount - record.return_amount

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.commission') or _('New')
        return super().create(vals)

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100%'))

    def action_confirm(self):
        for record in self:
            if not record.qr_confirmed:
                raise ValidationError(_('Commission can only be confirmed after QR confirmation of delivery.'))
            record.state = 'confirmed'

    def action_pay(self):
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_('Commission must be confirmed before payment.'))
            record.state = 'paid'
            record.payment_date = fields.Date.today()

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_confirm_qr(self):
        for record in self:
            record.qr_confirmed = True
            record.qr_confirmation_date = fields.Datetime.now()
            if record.state == 'draft':
                record.action_confirm()

    def action_process_return(self, return_amount):
        for record in self:
            if return_amount > record.amount:
                raise ValidationError(_('Return amount cannot exceed commission amount.'))
            record.return_amount = return_amount
            if record.state == 'paid':
                # Create adjustment entry
                self.env['honey.commission'].create({
                    'agent_id': record.agent_id.id,
                    'sale_order_id': record.sale_order_id.id,
                    'base_amount': -return_amount,
                    'commission_rate': record.commission_rate,
                    'state': 'confirmed',
                    'notes': f'Return adjustment for {record.name}',
                })


class CommissionRule(models.Model):
    _name = 'honey.commission.rule'
    _description = 'Commission Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    region_id = fields.Many2one(
        'honey.region',
        string='Region',
        help='Leave empty to apply to all regions'
    )
    agent_id = fields.Many2one(
        'honey.agent',
        string='Agent',
        help='Leave empty to apply to all agents in region'
    )
    customer_type = fields.Selection([
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('distributor', 'Distributor'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
    ], string='Customer Type')
    
    # Commission calculation
    base_commission_rate = fields.Float(
        string='Base Commission Rate (%)',
        digits=(5, 2),
        required=True
    )
    min_amount = fields.Float(
        string='Minimum Order Amount',
        digits=(16, 2),
        default=0.0
    )
    max_amount = fields.Float(
        string='Maximum Order Amount',
        digits=(16, 2)
    )
    
    # Bonus conditions
    bonus_rate = fields.Float(
        string='Bonus Rate (%)',
        digits=(5, 2),
        default=0.0
    )
    bonus_threshold = fields.Float(
        string='Bonus Threshold',
        digits=(16, 2),
        default=0.0
    )
    
    # Validity
    date_from = fields.Date(
        string='Valid From',
        required=True,
        default=fields.Date.today
    )
    date_to = fields.Date(
        string='Valid To'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    @api.constrains('base_commission_rate', 'bonus_rate')
    def _check_commission_rates(self):
        for record in self:
            if record.base_commission_rate < 0 or record.base_commission_rate > 100:
                raise ValidationError(_('Base commission rate must be between 0 and 100%'))
            if record.bonus_rate < 0 or record.bonus_rate > 100:
                raise ValidationError(_('Bonus rate must be between 0 and 100%'))

    @api.constrains('min_amount', 'max_amount')
    def _check_amount_range(self):
        for record in self:
            if record.max_amount and record.min_amount > record.max_amount:
                raise ValidationError(_('Minimum amount cannot be greater than maximum amount'))

    def get_commission_rate(self, agent_id, customer_id, order_amount, order_date=None):
        """Calculate commission rate based on rules"""
        if not order_date:
            order_date = fields.Date.today()
        
        domain = [
            ('active', '=', True),
            ('date_from', '<=', order_date),
            '|', ('date_to', '=', False), ('date_to', '>=', order_date),
            '|', ('region_id', '=', False), ('region_id', '=', agent_id.region_id.id),
            '|', ('agent_id', '=', False), ('agent_id', '=', agent_id.id),
        ]
        
        if customer_id.honey_customer_type:
            domain.append(('customer_type', 'in', [False, customer_id.honey_customer_type]))
        
        rules = self.search(domain, order='sequence, id')
        
        for rule in rules:
            if rule.min_amount <= order_amount and (not rule.max_amount or order_amount <= rule.max_amount):
                total_rate = rule.base_commission_rate
                if rule.bonus_threshold and order_amount >= rule.bonus_threshold:
                    total_rate += rule.bonus_rate
                return total_rate
        
        # Default to agent's commission rate
        return agent_id.commission_rate
