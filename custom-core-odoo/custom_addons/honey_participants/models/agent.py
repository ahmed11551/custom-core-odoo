# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Agent(models.Model):
    _name = 'honey.agent'
    _description = 'Sales Agent'
    _order = 'name'

    name = fields.Char(
        string='Agent Name',
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User Account',
        required=True,
        domain=[('groups_id', 'in', 'honey_participants.group_honey_agent')]
    )
    region_id = fields.Many2one(
        'honey.region',
        string='Sales Region',
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee Record'
    )
    
    # Contact information
    phone = fields.Char(
        string='Phone',
        related='user_id.partner_id.phone',
        store=True
    )
    email = fields.Char(
        string='Email',
        related='user_id.partner_id.email',
        store=True
    )
    mobile = fields.Char(
        string='Mobile',
        related='user_id.partner_id.mobile',
        store=True
    )
    
    # Sales targets and performance
    monthly_target = fields.Float(
        string='Monthly Sales Target',
        digits=(16, 2),
        default=0.0
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(5, 2),
        default=5.0
    )
    
    # Performance tracking
    current_month_sales = fields.Float(
        string='Current Month Sales',
        digits=(16, 2),
        compute='_compute_current_month_sales',
        store=True
    )
    target_achievement = fields.Float(
        string='Target Achievement (%)',
        digits=(5, 2),
        compute='_compute_target_achievement',
        store=True
    )
    
    # Customer management
    customer_ids = fields.One2many(
        'res.partner',
        'honey_agent_id',
        string='Customers',
        domain=[('is_company', '=', True)]
    )
    customer_count = fields.Integer(
        string='Customer Count',
        compute='_compute_customer_count',
        store=True
    )
    
    # Status and activity
    active = fields.Boolean(
        string='Active',
        default=True
    )
    last_activity_date = fields.Date(
        string='Last Activity Date',
        compute='_compute_last_activity_date',
        store=True
    )
    
    # Commission tracking
    commission_ids = fields.One2many(
        'honey.commission',
        'agent_id',
        string='Commissions'
    )
    total_commission = fields.Float(
        string='Total Commission',
        digits=(16, 2),
        compute='_compute_total_commission',
        store=True
    )

    _sql_constraints = [
        ('user_uniq', 'unique (user_id)', 'Each user can only be one agent!'),
    ]

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100%'))

    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.customer_ids)

    @api.depends('customer_ids.last_contact_date')
    def _compute_last_activity_date(self):
        for record in self:
            if record.customer_ids:
                last_dates = record.customer_ids.filtered('last_contact_date').mapped('last_contact_date')
                record.last_activity_date = max(last_dates) if last_dates else False
            else:
                record.last_activity_date = False

    @api.depends('commission_ids.amount')
    def _compute_total_commission(self):
        for record in self:
            record.total_commission = sum(record.commission_ids.mapped('amount'))

    @api.depends('customer_ids', 'customer_ids.sale_order_ids')
    def _compute_current_month_sales(self):
        for record in self:
            current_month = fields.Date.today().replace(day=1)
            orders = self.env['sale.order'].search([
                ('partner_id', 'in', record.customer_ids.ids),
                ('date_order', '>=', current_month),
                ('state', 'in', ['sale', 'done'])
            ])
            record.current_month_sales = sum(orders.mapped('amount_total'))

    @api.depends('current_month_sales', 'monthly_target')
    def _compute_target_achievement(self):
        for record in self:
            if record.monthly_target > 0:
                record.target_achievement = (record.current_month_sales / record.monthly_target) * 100
            else:
                record.target_achievement = 0.0

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.region_id.name})"
            result.append((record.id, name))
        return result

    def action_view_customers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customers'),
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('honey_agent_id', '=', self.id)],
            'context': {'default_honey_agent_id': self.id},
        }

    def action_view_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commissions'),
            'res_model': 'honey.commission',
            'view_mode': 'tree,form',
            'domain': [('agent_id', '=', self.id)],
            'context': {'default_agent_id': self.id},
        }
