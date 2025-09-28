# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductionBatch(models.Model):
    _name = 'honey.production.batch'
    _description = 'Honey Sticks Production Batch'
    _order = 'planned_start_date desc, name'

    name = fields.Char(
        string='Batch Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Basic information
    honey_type = fields.Selection([
        ('acacia', 'Acacia Honey'),
        ('linden', 'Linden Honey'),
        ('sunflower', 'Sunflower Honey'),
        ('buckwheat', 'Buckwheat Honey'),
        ('wildflower', 'Wildflower Honey'),
        ('manuka', 'Manuka Honey'),
    ], string='Honey Type', required=True)
    
    batch_size = fields.Integer(
        string='Batch Size (Sticks)',
        required=True,
        default=1000
    )
    
    # Planning and scheduling
    planned_start_date = fields.Datetime(
        string='Planned Start Date',
        required=True
    )
    planned_end_date = fields.Datetime(
        string='Planned End Date',
        required=True
    )
    actual_start_date = fields.Datetime(
        string='Actual Start Date'
    )
    actual_end_date = fields.Datetime(
        string='Actual End Date'
    )
    
    # Status tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('ready', 'Ready to Start'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Materials and requirements
    material_requirements_ids = fields.One2many(
        'honey.material.requirement',
        'batch_id',
        string='Material Requirements'
    )
    material_availability = fields.Selection([
        ('available', 'Available'),
        ('partial', 'Partially Available'),
        ('unavailable', 'Unavailable'),
    ], string='Material Availability', compute='_compute_material_availability', store=True)
    
    # Production tracking
    produced_quantity = fields.Integer(
        string='Produced Quantity',
        default=0
    )
    rejected_quantity = fields.Integer(
        string='Rejected Quantity',
        default=0
    )
    quality_grade = fields.Selection([
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    ], string='Quality Grade', default='standard')
    
    # Time tracking
    time_tracking_ids = fields.One2many(
        'honey.time.tracking',
        'batch_id',
        string='Time Tracking'
    )
    total_production_time = fields.Float(
        string='Total Production Time (Hours)',
        compute='_compute_total_production_time',
        store=True
    )
    
    # Quality control
    quality_control_ids = fields.One2many(
        'honey.quality.control',
        'batch_id',
        string='Quality Control'
    )
    quality_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional'),
    ], string='Quality Status', default='pending')
    
    # Packaging and labeling
    sticker_range_start = fields.Integer(
        string='Sticker Range Start',
        required=True
    )
    sticker_range_end = fields.Integer(
        string='Sticker Range End',
        required=True
    )
    label_template_id = fields.Many2one(
        'honey.label.template',
        string='Label Template'
    )
    display_type = fields.Selection([
        ('standard', 'Standard Display'),
        ('premium', 'Premium Display'),
        ('custom', 'Custom Display'),
    ], string='Display Type', default='standard')
    
    # Notes and instructions
    notes = fields.Text(
        string='Production Notes'
    )
    special_instructions = fields.Text(
        string='Special Instructions'
    )
    
    # Related orders and sales
    sale_order_ids = fields.Many2many(
        'sale.order',
        'honey_batch_sale_rel',
        'batch_id',
        'order_id',
        string='Related Sales Orders'
    )
    
    # Responsible person
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user
    )

    @api.depends('material_requirements_ids.available_quantity', 'material_requirements_ids.required_quantity')
    def _compute_material_availability(self):
        for record in self:
            if not record.material_requirements_ids:
                record.material_availability = 'unavailable'
                continue
            
            total_required = sum(record.material_requirements_ids.mapped('required_quantity'))
            total_available = sum(record.material_requirements_ids.mapped('available_quantity'))
            
            if total_available >= total_required:
                record.material_availability = 'available'
            elif total_available > 0:
                record.material_availability = 'partial'
            else:
                record.material_availability = 'unavailable'

    @api.depends('time_tracking_ids.duration')
    def _compute_total_production_time(self):
        for record in self:
            record.total_production_time = sum(record.time_tracking_ids.mapped('duration'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.production.batch') or _('New')
        return super().create(vals)

    @api.constrains('sticker_range_start', 'sticker_range_end')
    def _check_sticker_range(self):
        for record in self:
            if record.sticker_range_start >= record.sticker_range_end:
                raise ValidationError(_('Sticker range start must be less than end.'))

    @api.constrains('planned_start_date', 'planned_end_date')
    def _check_planned_dates(self):
        for record in self:
            if record.planned_start_date >= record.planned_end_date:
                raise ValidationError(_('Planned start date must be before end date.'))

    def action_plan(self):
        """Plan the batch - check material availability"""
        for record in self:
            if record.material_availability == 'unavailable':
                raise ValidationError(_('Cannot plan batch - materials not available.'))
            record.state = 'planned'

    def action_start(self):
        """Start production"""
        for record in self:
            if record.state != 'planned':
                raise ValidationError(_('Batch must be planned before starting.'))
            record.state = 'in_progress'
            record.actual_start_date = fields.Datetime.now()

    def action_complete(self):
        """Complete production"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Batch must be in progress to complete.'))
            record.state = 'completed'
            record.actual_end_date = fields.Datetime.now()

    def action_cancel(self):
        """Cancel batch"""
        for record in self:
            if record.state in ['completed']:
                raise ValidationError(_('Cannot cancel completed batch.'))
            record.state = 'cancelled'

    def action_check_materials(self):
        """Check and update material availability"""
        for record in self:
            for requirement in record.material_requirements_ids:
                requirement._compute_available_quantity()

    def action_create_material_requirements(self):
        """Create material requirements based on batch size and honey type"""
        for record in self:
            # Clear existing requirements
            record.material_requirements_ids.unlink()
            
            # Create requirements based on batch size
            requirements = []
            
            # Honey requirement (ml per stick)
            honey_per_stick = 10  # ml
            total_honey = record.batch_size * honey_per_stick
            requirements.append({
                'material_type': 'honey',
                'material_subtype': record.honey_type,
                'required_quantity': total_honey,
                'unit': 'ml',
            })
            
            # Film requirement (cm per stick)
            film_per_stick = 15  # cm
            total_film = record.batch_size * film_per_stick
            requirements.append({
                'material_type': 'film',
                'required_quantity': total_film,
                'unit': 'cm',
            })
            
            # Stickers requirement
            requirements.append({
                'material_type': 'sticker',
                'required_quantity': record.batch_size,
                'unit': 'pcs',
            })
            
            # Displays requirement (displays per batch)
            displays_per_batch = (record.batch_size // 20) + 1  # 20 sticks per display
            requirements.append({
                'material_type': 'display',
                'material_subtype': record.display_type,
                'required_quantity': displays_per_batch,
                'unit': 'pcs',
            })
            
            # Create requirement records
            for req_data in requirements:
                self.env['honey.material.requirement'].create({
                    'batch_id': record.id,
                    **req_data
                })


class MaterialRequirement(models.Model):
    _name = 'honey.material.requirement'
    _description = 'Material Requirement for Production Batch'

    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch',
        required=True,
        ondelete='cascade'
    )
    
    material_type = fields.Selection([
        ('honey', 'Honey'),
        ('film', 'Film'),
        ('sticker', 'Sticker'),
        ('display', 'Display'),
        ('packaging', 'Packaging'),
    ], string='Material Type', required=True)
    
    material_subtype = fields.Char(
        string='Material Subtype'
    )
    
    required_quantity = fields.Float(
        string='Required Quantity',
        required=True
    )
    available_quantity = fields.Float(
        string='Available Quantity',
        compute='_compute_available_quantity',
        store=True
    )
    unit = fields.Char(
        string='Unit',
        required=True
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        domain=[('supplier_rank', '>', 0)]
    )
    
    status = fields.Selection([
        ('available', 'Available'),
        ('shortage', 'Shortage'),
        ('unavailable', 'Unavailable'),
    ], string='Status', compute='_compute_status', store=True)

    @api.depends('material_type', 'material_subtype', 'required_quantity')
    def _compute_available_quantity(self):
        for record in self:
            # This would typically check stock levels
            # For now, we'll simulate availability
            if record.material_type == 'honey':
                # Check honey stock by type
                stock = self.env['stock.quant'].search([
                    ('product_id.name', 'ilike', record.material_subtype or 'honey'),
                    ('quantity', '>', 0)
                ])
                record.available_quantity = sum(stock.mapped('quantity'))
            else:
                # For other materials, check general stock
                stock = self.env['stock.quant'].search([
                    ('product_id.name', 'ilike', record.material_type),
                    ('quantity', '>', 0)
                ])
                record.available_quantity = sum(stock.mapped('quantity'))

    @api.depends('required_quantity', 'available_quantity')
    def _compute_status(self):
        for record in self:
            if record.available_quantity >= record.required_quantity:
                record.status = 'available'
            elif record.available_quantity > 0:
                record.status = 'shortage'
            else:
                record.status = 'unavailable'
