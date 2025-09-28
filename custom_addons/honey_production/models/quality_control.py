# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityControl(models.Model):
    _name = 'honey.quality.control'
    _description = 'Quality Control for Honey Production'

    name = fields.Char(
        string='QC Reference',
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
    
    # QC details
    qc_type = fields.Selection([
        ('incoming', 'Incoming Material QC'),
        ('in_process', 'In-Process QC'),
        ('final', 'Final Product QC'),
        ('random', 'Random Sampling QC'),
        ('complaint', 'Customer Complaint QC'),
    ], string='QC Type', required=True)
    
    qc_date = fields.Datetime(
        string='QC Date',
        required=True,
        default=fields.Datetime.now
    )
    
    # Inspector information
    inspector_id = fields.Many2one(
        'hr.employee',
        string='Inspector',
        required=True
    )
    qc_supervisor_id = fields.Many2one(
        'hr.employee',
        string='QC Supervisor'
    )
    
    # Sample information
    sample_size = fields.Integer(
        string='Sample Size',
        required=True,
        default=10
    )
    sample_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('stratified', 'Stratified Sampling'),
        ('convenience', 'Convenience Sampling'),
    ], string='Sampling Method', default='random')
    
    # Test results
    test_results_ids = fields.One2many(
        'honey.quality.test.result',
        'qc_id',
        string='Test Results'
    )
    
    # Overall assessment
    overall_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional Pass'),
        ('pending', 'Pending'),
    ], string='Overall Result', default='pending')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    
    # Approval
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By'
    )
    approval_date = fields.Datetime(
        string='Approval Date'
    )
    
    # Notes and recommendations
    notes = fields.Text(
        string='Notes'
    )
    recommendations = fields.Text(
        string='Recommendations'
    )
    corrective_actions = fields.Text(
        string='Corrective Actions'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.quality.control') or _('New')
        return super().create(vals)

    def action_start_qc(self):
        """Start quality control process"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft records can be started.'))
            record.state = 'in_progress'

    def action_complete_qc(self):
        """Complete quality control process"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Only in-progress records can be completed.'))
            
            # Calculate overall result based on test results
            if record.test_results_ids:
                failed_tests = record.test_results_ids.filtered(lambda r: r.result == 'fail')
                if failed_tests:
                    record.overall_result = 'fail'
                else:
                    conditional_tests = record.test_results_ids.filtered(lambda r: r.result == 'conditional')
                    if conditional_tests:
                        record.overall_result = 'conditional'
                    else:
                        record.overall_result = 'pass'
            
            record.state = 'completed'

    def action_approve(self):
        """Approve quality control results"""
        for record in self:
            if record.state != 'completed':
                raise ValidationError(_('Only completed records can be approved.'))
            record.state = 'approved'
            record.approved_by = self.env.user.id
            record.approval_date = fields.Datetime.now()
            
            # Update batch quality status
            if record.batch_id:
                if record.overall_result == 'pass':
                    record.batch_id.quality_status = 'passed'
                elif record.overall_result == 'fail':
                    record.batch_id.quality_status = 'failed'
                else:
                    record.batch_id.quality_status = 'conditional'

    def action_reject(self):
        """Reject quality control results"""
        for record in self:
            if record.state not in ['completed', 'approved']:
                raise ValidationError(_('Only completed or approved records can be rejected.'))
            record.state = 'rejected'
            record.overall_result = 'fail'
            
            # Update batch quality status
            if record.batch_id:
                record.batch_id.quality_status = 'failed'


class QualityTestResult(models.Model):
    _name = 'honey.quality.test.result'
    _description = 'Quality Test Result'

    qc_id = fields.Many2one(
        'honey.quality.control',
        string='Quality Control',
        required=True,
        ondelete='cascade'
    )
    
    # Test information
    test_name = fields.Char(
        string='Test Name',
        required=True
    )
    test_method = fields.Char(
        string='Test Method'
    )
    test_standard = fields.Char(
        string='Test Standard'
    )
    
    # Test parameters
    parameter_name = fields.Char(
        string='Parameter Name',
        required=True
    )
    unit = fields.Char(
        string='Unit'
    )
    
    # Test values
    target_value = fields.Float(
        string='Target Value'
    )
    min_value = fields.Float(
        string='Minimum Value'
    )
    max_value = fields.Float(
        string='Maximum Value'
    )
    actual_value = fields.Float(
        string='Actual Value',
        required=True
    )
    
    # Result
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional'),
    ], string='Result', compute='_compute_result', store=True)
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('target_value', 'min_value', 'max_value', 'actual_value')
    def _compute_result(self):
        for record in self:
            if record.target_value and record.actual_value:
                # Check if actual value is within acceptable range
                if record.min_value and record.max_value:
                    if record.min_value <= record.actual_value <= record.max_value:
                        record.result = 'pass'
                    else:
                        record.result = 'fail'
                elif record.target_value:
                    # Allow 5% tolerance
                    tolerance = record.target_value * 0.05
                    if abs(record.actual_value - record.target_value) <= tolerance:
                        record.result = 'pass'
                    else:
                        record.result = 'fail'
                else:
                    record.result = 'conditional'
            else:
                record.result = 'conditional'


class QualityStandard(models.Model):
    _name = 'honey.quality.standard'
    _description = 'Quality Standards for Honey Products'

    name = fields.Char(
        string='Standard Name',
        required=True
    )
    
    # Product information
    honey_type = fields.Selection([
        ('acacia', 'Acacia Honey'),
        ('linden', 'Linden Honey'),
        ('sunflower', 'Sunflower Honey'),
        ('buckwheat', 'Buckwheat Honey'),
        ('wildflower', 'Wildflower Honey'),
        ('manuka', 'Manuka Honey'),
    ], string='Honey Type')
    
    quality_grade = fields.Selection([
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    ], string='Quality Grade')
    
    # Test parameters
    test_parameters_ids = fields.One2many(
        'honey.quality.test.parameter',
        'standard_id',
        string='Test Parameters'
    )
    
    # Validity
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        default=fields.Date.today
    )
    expiry_date = fields.Date(
        string='Expiry Date'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Notes
    description = fields.Text(
        string='Description'
    )


class QualityTestParameter(models.Model):
    _name = 'honey.quality.test.parameter'
    _description = 'Quality Test Parameter'

    standard_id = fields.Many2one(
        'honey.quality.standard',
        string='Quality Standard',
        required=True,
        ondelete='cascade'
    )
    
    parameter_name = fields.Char(
        string='Parameter Name',
        required=True
    )
    unit = fields.Char(
        string='Unit',
        required=True
    )
    
    # Target values
    target_value = fields.Float(
        string='Target Value'
    )
    min_value = fields.Float(
        string='Minimum Value'
    )
    max_value = fields.Float(
        string='Maximum Value'
    )
    
    # Test method
    test_method = fields.Char(
        string='Test Method'
    )
    test_frequency = fields.Selection([
        ('every_batch', 'Every Batch'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('random', 'Random'),
    ], string='Test Frequency', default='every_batch')
    
    # Criticality
    is_critical = fields.Boolean(
        string='Critical Parameter',
        default=False
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
