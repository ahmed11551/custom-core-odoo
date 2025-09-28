# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Region(models.Model):
    _name = 'honey.region'
    _description = 'Sales Region'
    _order = 'name'

    name = fields.Char(
        string='Region Name',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Region Code',
        required=True,
        size=10
    )
    manager_id = fields.Many2one(
        'res.users',
        string='Regional Manager',
        domain=[('groups_id', 'in', 'honey_participants.group_honey_manager')]
    )
    agent_ids = fields.One2many(
        'honey.agent',
        'region_id',
        string='Agents'
    )
    customer_ids = fields.One2many(
        'res.partner',
        'honey_region_id',
        string='Customers'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    description = fields.Text(
        string='Description'
    )
    sales_target = fields.Float(
        string='Monthly Sales Target',
        digits=(16, 2)
    )
    commission_rate = fields.Float(
        string='Default Commission Rate (%)',
        digits=(5, 2),
        default=5.0
    )

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Region code must be unique!'),
    ]

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100%'))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result
