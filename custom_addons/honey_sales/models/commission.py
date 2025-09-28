# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Commission(models.Model):
    _inherit = 'honey.commission'

    # Additional fields for sales module
    sale_order_line_ids = fields.One2many(
        'sale.order.line',
        'honey_commission_id',
        string='Sale Order Lines'
    )
    
    # Performance tracking
    performance_bonus = fields.Float(
        string='Performance Bonus',
        digits=(16, 2),
        default=0.0
    )
    performance_bonus_rate = fields.Float(
        string='Performance Bonus Rate (%)',
        digits=(5, 2),
        default=0.0
    )
    
    # Regional performance
    regional_rank = fields.Integer(
        string='Regional Rank',
        compute='_compute_regional_rank',
        store=True
    )
    monthly_rank = fields.Integer(
        string='Monthly Rank',
        compute='_compute_monthly_rank',
        store=True
    )

    @api.depends('agent_id', 'date')
    def _compute_regional_rank(self):
        for record in self:
            if record.agent_id and record.region_id:
                # Calculate rank within region for the month
                month_start = record.date.replace(day=1)
                month_end = (month_start + fields.timedelta(days=32)).replace(day=1) - fields.timedelta(days=1)
                
                commissions = self.search([
                    ('agent_id.region_id', '=', record.region_id.id),
                    ('date', '>=', month_start),
                    ('date', '<=', month_end),
                    ('state', 'in', ['confirmed', 'paid'])
                ])
                
                sorted_commissions = commissions.sorted('amount', reverse=True)
                record.regional_rank = sorted_commissions.ids.index(record.id) + 1 if record.id in sorted_commissions.ids else 0
            else:
                record.regional_rank = 0

    @api.depends('agent_id', 'date')
    def _compute_monthly_rank(self):
        for record in self:
            if record.agent_id:
                # Calculate rank for the agent in the month
                month_start = record.date.replace(day=1)
                month_end = (month_start + fields.timedelta(days=32)).replace(day=1) - fields.timedelta(days=1)
                
                commissions = self.search([
                    ('agent_id', '=', record.agent_id.id),
                    ('date', '>=', month_start),
                    ('date', '<=', month_end),
                    ('state', 'in', ['confirmed', 'paid'])
                ])
                
                sorted_commissions = commissions.sorted('amount', reverse=True)
                record.monthly_rank = sorted_commissions.ids.index(record.id) + 1 if record.id in sorted_commissions.ids else 0
            else:
                record.monthly_rank = 0

    def action_calculate_performance_bonus(self):
        """Calculate performance bonus based on regional and monthly ranks"""
        for record in self:
            if record.regional_rank <= 3:  # Top 3 in region
                record.performance_bonus_rate = 2.0  # 2% bonus
            elif record.regional_rank <= 5:  # Top 5 in region
                record.performance_bonus_rate = 1.0  # 1% bonus
            else:
                record.performance_bonus_rate = 0.0
            
            if record.performance_bonus_rate > 0:
                record.performance_bonus = record.base_amount * (record.performance_bonus_rate / 100)
                # Update total amount
                record.amount = record.base_amount * (record.commission_rate / 100) + record.performance_bonus


class CommissionReport(models.Model):
    _name = 'honey.commission.report'
    _description = 'Commission Report'
    _auto = False

    agent_id = fields.Many2one('honey.agent', string='Agent', readonly=True)
    region_id = fields.Many2one('honey.region', string='Region', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    month = fields.Char(string='Month', readonly=True)
    year = fields.Integer(string='Year', readonly=True)
    total_commission = fields.Float(string='Total Commission', readonly=True)
    total_orders = fields.Integer(string='Total Orders', readonly=True)
    total_amount = fields.Float(string='Total Amount', readonly=True)
    average_commission = fields.Float(string='Average Commission', readonly=True)
    performance_bonus = fields.Float(string='Performance Bonus', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    c.agent_id,
                    c.region_id,
                    c.date,
                    to_char(c.date, 'YYYY-MM') AS month,
                    extract(year from c.date) AS year,
                    sum(c.amount) AS total_commission,
                    count(c.id) AS total_orders,
                    sum(c.base_amount) AS total_amount,
                    avg(c.amount) AS average_commission,
                    sum(c.performance_bonus) AS performance_bonus
                FROM honey_commission c
                WHERE c.state IN ('confirmed', 'paid')
                GROUP BY c.agent_id, c.region_id, c.date
            )
        """ % self._table)
