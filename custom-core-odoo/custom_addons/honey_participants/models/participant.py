# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Honey Sticks specific fields
    honey_region_id = fields.Many2one(
        'honey.region',
        string='Sales Region',
        tracking=True
    )
    honey_agent_id = fields.Many2one(
        'honey.agent',
        string='Sales Agent',
        domain="[('region_id', '=', honey_region_id)]",
        tracking=True
    )
    honey_customer_type = fields.Selection([
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('distributor', 'Distributor'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
    ], string='Customer Type', default='retail')
    
    # Contact preferences
    preferred_contact_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('visit', 'Personal Visit'),
    ], string='Preferred Contact Method', default='email')
    
    # Communication tracking
    last_contact_date = fields.Date(
        string='Last Contact Date',
        tracking=True
    )
    next_contact_date = fields.Date(
        string='Next Contact Date',
        tracking=True
    )
    contact_notes = fields.Text(
        string='Contact Notes'
    )
    
    # Sales tracking
    honey_sales_target = fields.Float(
        string='Monthly Sales Target',
        digits=(16, 2)
    )
    honey_credit_limit = fields.Float(
        string='Credit Limit',
        digits=(16, 2)
    )
    
    # Status tracking
    honey_status = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    ], string='Customer Status', default='prospect', tracking=True)
    
    # History tracking
    region_history_ids = fields.One2many(
        'honey.region.history',
        'partner_id',
        string='Region History'
    )
    agent_history_ids = fields.One2many(
        'honey.agent.history',
        'partner_id',
        string='Agent History'
    )

    @api.constrains('honey_region_id', 'honey_agent_id')
    def _check_agent_region_consistency(self):
        for record in self:
            if record.honey_agent_id and record.honey_region_id:
                if record.honey_agent_id.region_id != record.honey_region_id:
                    raise ValidationError(
                        _('Selected agent must belong to the selected region.')
                    )

    @api.onchange('honey_region_id')
    def _onchange_region(self):
        if self.honey_region_id:
            self.honey_agent_id = False
        else:
            self.honey_agent_id = False

    def write(self, vals):
        # Track region and agent changes
        for record in self:
            if 'honey_region_id' in vals and vals['honey_region_id'] != record.honey_region_id.id:
                self.env['honey.region.history'].create({
                    'partner_id': record.id,
                    'old_region_id': record.honey_region_id.id,
                    'new_region_id': vals['honey_region_id'],
                    'change_date': fields.Date.today(),
                    'change_reason': vals.get('change_reason', 'Region changed'),
                })
            
            if 'honey_agent_id' in vals and vals['honey_agent_id'] != record.honey_agent_id.id:
                self.env['honey.agent.history'].create({
                    'partner_id': record.id,
                    'old_agent_id': record.honey_agent_id.id,
                    'new_agent_id': vals['honey_agent_id'],
                    'change_date': fields.Date.today(),
                    'change_reason': vals.get('change_reason', 'Agent changed'),
                })
        
        return super().write(vals)


class RegionHistory(models.Model):
    _name = 'honey.region.history'
    _description = 'Region Change History'
    _order = 'change_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade'
    )
    old_region_id = fields.Many2one(
        'honey.region',
        string='Previous Region'
    )
    new_region_id = fields.Many2one(
        'honey.region',
        string='New Region',
        required=True
    )
    change_date = fields.Date(
        string='Change Date',
        required=True
    )
    change_reason = fields.Text(
        string='Reason for Change'
    )


class AgentHistory(models.Model):
    _name = 'honey.agent.history'
    _description = 'Agent Change History'
    _order = 'change_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade'
    )
    old_agent_id = fields.Many2one(
        'honey.agent',
        string='Previous Agent'
    )
    new_agent_id = fields.Many2one(
        'honey.agent',
        string='New Agent',
        required=True
    )
    change_date = fields.Date(
        string='Change Date',
        required=True
    )
    change_reason = fields.Text(
        string='Reason for Change'
    )
