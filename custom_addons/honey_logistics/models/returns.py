# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReturnRequest(models.Model):
    _name = 'honey.return.request'
    _description = 'Return Request'

    name = fields.Char(
        string='Return Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Related records
    shipment_id = fields.Many2one(
        'honey.shipment',
        string='Shipment',
        required=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        related='shipment_id.sale_order_id',
        store=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='shipment_id.customer_id',
        store=True
    )
    
    # Return details
    return_date = fields.Date(
        string='Return Date',
        required=True,
        default=fields.Date.today
    )
    return_reason = fields.Selection([
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged in Transit'),
        ('quality_issue', 'Quality Issue'),
        ('customer_request', 'Customer Request'),
        ('expired', 'Expired Product'),
        ('other', 'Other'),
    ], string='Return Reason', required=True)
    
    other_reason = fields.Text(
        string='Other Reason',
        attrs={'invisible': [('return_reason', '!=', 'other')]}
    )
    
    # Return quantities
    return_line_ids = fields.One2many(
        'honey.return.line',
        'return_id',
        string='Return Lines'
    )
    total_quantity = fields.Integer(
        string='Total Quantity',
        compute='_compute_total_quantity',
        store=True
    )
    total_value = fields.Float(
        string='Total Value',
        digits=(16, 2),
        compute='_compute_total_value',
        store=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
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
    rejection_reason = fields.Text(
        string='Rejection Reason'
    )
    
    # Processing
    processed_by = fields.Many2one(
        'res.users',
        string='Processed By'
    )
    processing_date = fields.Datetime(
        string='Processing Date'
    )
    
    # Refund information
    refund_amount = fields.Float(
        string='Refund Amount',
        digits=(16, 2)
    )
    refund_method = fields.Selection([
        ('credit_note', 'Credit Note'),
        ('refund', 'Refund'),
        ('replacement', 'Replacement'),
        ('store_credit', 'Store Credit'),
    ], string='Refund Method')
    
    # Commission adjustment
    commission_adjustment = fields.Float(
        string='Commission Adjustment',
        digits=(16, 2),
        compute='_compute_commission_adjustment',
        store=True
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
    customer_notes = fields.Text(
        string='Customer Notes'
    )

    @api.depends('return_line_ids.quantity')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = sum(record.return_line_ids.mapped('quantity'))

    @api.depends('return_line_ids.value')
    def _compute_total_value(self):
        for record in self:
            record.total_value = sum(record.return_line_ids.mapped('value'))

    @api.depends('total_value')
    def _compute_commission_adjustment(self):
        for record in self:
            if record.sale_order_id and record.sale_order_id.honey_agent_id:
                # Calculate commission adjustment based on return value
                commission_rate = record.sale_order_id.honey_agent_id.commission_rate / 100
                record.commission_adjustment = record.total_value * commission_rate
            else:
                record.commission_adjustment = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.return.request') or _('New')
        return super().create(vals)

    def action_submit(self):
        """Submit return request"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft requests can be submitted.'))
            record.state = 'submitted'

    def action_approve(self):
        """Approve return request"""
        for record in self:
            if record.state != 'submitted':
                raise ValidationError(_('Only submitted requests can be approved.'))
            record.state = 'approved'
            record.approved_by = self.env.user.id
            record.approval_date = fields.Datetime.now()

    def action_reject(self):
        """Reject return request"""
        for record in self:
            if record.state != 'submitted':
                raise ValidationError(_('Only submitted requests can be rejected.'))
            record.state = 'rejected'

    def action_process(self):
        """Process return request"""
        for record in self:
            if record.state != 'approved':
                raise ValidationError(_('Only approved requests can be processed.'))
            record.state = 'processed'
            record.processed_by = self.env.user.id
            record.processing_date = fields.Datetime.now()
            
            # Adjust commissions
            if record.commission_adjustment != 0:
                self._adjust_commissions()

    def action_complete(self):
        """Complete return request"""
        for record in self:
            if record.state != 'processed':
                raise ValidationError(_('Only processed requests can be completed.'))
            record.state = 'completed'

    def action_cancel(self):
        """Cancel return request"""
        for record in self:
            if record.state in ['completed']:
                raise ValidationError(_('Cannot cancel completed requests.'))
            record.state = 'cancelled'

    def _adjust_commissions(self):
        """Adjust commissions based on return"""
        for record in self:
            if record.sale_order_id and record.sale_order_id.commission_ids:
                for commission in record.sale_order_id.commission_ids:
                    if commission.state == 'paid':
                        # Create adjustment entry
                        self.env['honey.commission'].create({
                            'agent_id': commission.agent_id.id,
                            'sale_order_id': commission.sale_order_id.id,
                            'base_amount': -record.commission_adjustment,
                            'commission_rate': commission.commission_rate,
                            'state': 'confirmed',
                            'notes': f'Return adjustment for {record.name}',
                        })


class ReturnLine(models.Model):
    _name = 'honey.return.line'
    _description = 'Return Line'

    return_id = fields.Many2one(
        'honey.return.request',
        string='Return Request',
        required=True,
        ondelete='cascade'
    )
    
    # Product information
    product_name = fields.Char(
        string='Product Name',
        required=True
    )
    honey_type = fields.Selection([
        ('acacia', 'Acacia Honey'),
        ('linden', 'Linden Honey'),
        ('sunflower', 'Sunflower Honey'),
        ('buckwheat', 'Buckwheat Honey'),
        ('wildflower', 'Wildflower Honey'),
        ('manuka', 'Manuka Honey'),
    ], string='Honey Type', required=True)
    
    batch_number = fields.Char(
        string='Batch Number'
    )
    
    # Quantities
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1
    )
    unit_price = fields.Float(
        string='Unit Price',
        digits=(16, 2),
        required=True
    )
    value = fields.Float(
        string='Value',
        digits=(16, 2),
        compute='_compute_value',
        store=True
    )
    
    # Quality information
    quality_grade = fields.Selection([
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    ], string='Quality Grade')
    
    # Return condition
    return_condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
        ('expired', 'Expired'),
    ], string='Return Condition', required=True, default='good')
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('quantity', 'unit_price')
    def _compute_value(self):
        for record in self:
            record.value = record.quantity * record.unit_price


class ReturnPolicy(models.Model):
    _name = 'honey.return.policy'
    _description = 'Return Policy'

    name = fields.Char(
        string='Policy Name',
        required=True
    )
    
    # Policy details
    return_period_days = fields.Integer(
        string='Return Period (Days)',
        required=True,
        default=30
    )
    
    # Customer type restrictions
    customer_types = fields.Selection([
        ('all', 'All Customer Types'),
        ('retail', 'Retail Only'),
        ('wholesale', 'Wholesale Only'),
        ('distributor', 'Distributor Only'),
    ], string='Customer Types', default='all')
    
    # Product restrictions
    honey_types = fields.Selection([
        ('all', 'All Honey Types'),
        ('premium', 'Premium Only'),
        ('standard', 'Standard Only'),
        ('economy', 'Economy Only'),
    ], string='Honey Types', default='all')
    
    # Return reasons allowed
    allowed_reasons = fields.Selection([
        ('all', 'All Reasons'),
        ('defective_only', 'Defective Only'),
        ('quality_issues', 'Quality Issues Only'),
    ], string='Allowed Reasons', default='all')
    
    # Refund policy
    refund_percentage = fields.Float(
        string='Refund Percentage (%)',
        digits=(5, 2),
        default=100.0
    )
    
    # Processing requirements
    require_approval = fields.Boolean(
        string='Require Approval',
        default=True
    )
    require_photos = fields.Boolean(
        string='Require Photos',
        default=False
    )
    require_batch_verification = fields.Boolean(
        string='Require Batch Verification',
        default=True
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

    def check_return_eligibility(self, return_request):
        """Check if return request is eligible under this policy"""
        self.ensure_one()
        
        # Check customer type
        if self.customer_types != 'all':
            if return_request.customer_id.honey_customer_type != self.customer_types:
                return False, f"Return not allowed for customer type: {return_request.customer_id.honey_customer_type}"
        
        # Check return period
        if return_request.return_date:
            days_since_shipment = (return_request.return_date - return_request.shipment_id.shipment_date.date()).days
            if days_since_shipment > self.return_period_days:
                return False, f"Return period exceeded. Allowed: {self.return_period_days} days, Actual: {days_since_shipment} days"
        
        # Check return reason
        if self.allowed_reasons != 'all':
            if self.allowed_reasons == 'defective_only' and return_request.return_reason != 'defective':
                return False, "Only defective products can be returned under this policy"
            elif self.allowed_reasons == 'quality_issues' and return_request.return_reason not in ['defective', 'quality_issue']:
                return False, "Only quality issues can be returned under this policy"
        
        return True, "Return is eligible under this policy"
