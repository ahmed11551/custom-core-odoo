# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TimeTracking(models.Model):
    _name = 'honey.time.tracking'
    _description = 'Production Time Tracking'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch',
        required=True
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True
    )
    
    # Time tracking
    start_time = fields.Datetime(
        string='Start Time',
        required=True
    )
    end_time = fields.Datetime(
        string='End Time'
    )
    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True
    )
    
    # Activity details
    activity_type = fields.Selection([
        ('preparation', 'Preparation'),
        ('production', 'Production'),
        ('quality_control', 'Quality Control'),
        ('packaging', 'Packaging'),
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ], string='Activity Type', required=True, default='production')
    
    activity_description = fields.Text(
        string='Activity Description'
    )
    
    # Production metrics
    quantity_produced = fields.Integer(
        string='Quantity Produced',
        default=0
    )
    quantity_rejected = fields.Integer(
        string='Quantity Rejected',
        default=0
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Approval
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By'
    )
    approval_date = fields.Datetime(
        string='Approval Date'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600  # Convert to hours
            else:
                record.duration = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.time.tracking') or _('New')
        return super().create(vals)

    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        for record in self:
            if record.start_time and record.end_time and record.start_time >= record.end_time:
                raise ValidationError(_('Start time must be before end time.'))

    def action_start(self):
        """Start time tracking"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft records can be started.'))
            record.state = 'in_progress'
            record.start_time = fields.Datetime.now()

    def action_stop(self):
        """Stop time tracking"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Only in-progress records can be stopped.'))
            record.state = 'completed'
            record.end_time = fields.Datetime.now()

    def action_approve(self):
        """Approve time tracking"""
        for record in self:
            if record.state != 'completed':
                raise ValidationError(_('Only completed records can be approved.'))
            record.approved_by = self.env.user.id
            record.approval_date = fields.Datetime.now()

    def action_cancel(self):
        """Cancel time tracking"""
        for record in self:
            if record.state in ['completed']:
                raise ValidationError(_('Cannot cancel completed records.'))
            record.state = 'cancelled'


class ShiftPlanning(models.Model):
    _name = 'honey.shift.planning'
    _description = 'Production Shift Planning'

    name = fields.Char(
        string='Shift Name',
        required=True
    )
    
    # Shift details
    shift_date = fields.Date(
        string='Shift Date',
        required=True
    )
    shift_type = fields.Selection([
        ('morning', 'Morning Shift'),
        ('afternoon', 'Afternoon Shift'),
        ('night', 'Night Shift'),
        ('overtime', 'Overtime'),
    ], string='Shift Type', required=True)
    
    start_time = fields.Float(
        string='Start Time',
        required=True
    )
    end_time = fields.Float(
        string='End Time',
        required=True
    )
    
    # Team assignment
    team_leader_id = fields.Many2one(
        'hr.employee',
        string='Team Leader'
    )
    team_member_ids = fields.Many2many(
        'hr.employee',
        'honey_shift_employee_rel',
        'shift_id',
        'employee_id',
        string='Team Members'
    )
    
    # Production targets
    target_batches = fields.Integer(
        string='Target Batches'
    )
    target_quantity = fields.Integer(
        string='Target Quantity (Sticks)'
    )
    
    # Status
    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='planned', tracking=True)
    
    # Actual results
    actual_batches = fields.Integer(
        string='Actual Batches',
        compute='_compute_actual_results',
        store=True
    )
    actual_quantity = fields.Integer(
        string='Actual Quantity',
        compute='_compute_actual_results',
        store=True
    )
    
    # Performance metrics
    efficiency = fields.Float(
        string='Efficiency (%)',
        compute='_compute_efficiency',
        store=True
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('shift_date', 'team_member_ids')
    def _compute_actual_results(self):
        for record in self:
            # Calculate actual results from time tracking records
            time_records = self.env['honey.time.tracking'].search([
                ('employee_id', 'in', record.team_member_ids.ids),
                ('start_time', '>=', fields.Datetime.combine(record.shift_date, fields.time(0, 0, 0))),
                ('start_time', '<=', fields.Datetime.combine(record.shift_date, fields.time(23, 59, 59))),
                ('state', '=', 'completed')
            ])
            
            record.actual_batches = len(time_records.mapped('batch_id'))
            record.actual_quantity = sum(time_records.mapped('quantity_produced'))

    @api.depends('target_quantity', 'actual_quantity')
    def _compute_efficiency(self):
        for record in self:
            if record.target_quantity > 0:
                record.efficiency = (record.actual_quantity / record.target_quantity) * 100
            else:
                record.efficiency = 0.0

    def action_start_shift(self):
        """Start the shift"""
        for record in self:
            if record.state != 'planned':
                raise ValidationError(_('Only planned shifts can be started.'))
            record.state = 'in_progress'

    def action_complete_shift(self):
        """Complete the shift"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Only in-progress shifts can be completed.'))
            record.state = 'completed'

    def action_cancel_shift(self):
        """Cancel the shift"""
        for record in self:
            if record.state in ['completed']:
                raise ValidationError(_('Cannot cancel completed shifts.'))
            record.state = 'cancelled'
