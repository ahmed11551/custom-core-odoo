# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaterialType(models.Model):
    _name = 'honey.material.type'
    _description = 'Material Type for Honey Production'

    name = fields.Char(
        string='Material Type',
        required=True
    )
    code = fields.Char(
        string='Code',
        required=True
    )
    category = fields.Selection([
        ('raw_material', 'Raw Material'),
        ('packaging', 'Packaging'),
        ('labeling', 'Labeling'),
        ('equipment', 'Equipment'),
    ], string='Category', required=True)
    
    unit_of_measure = fields.Char(
        string='Unit of Measure',
        required=True
    )
    
    # Quality specifications
    quality_standards = fields.Text(
        string='Quality Standards'
    )
    storage_requirements = fields.Text(
        string='Storage Requirements'
    )
    
    # Supplier information
    preferred_suppliers = fields.Many2many(
        'res.partner',
        'honey_material_supplier_rel',
        'material_type_id',
        'supplier_id',
        string='Preferred Suppliers',
        domain=[('supplier_rank', '>', 0)]
    )
    
    # Cost tracking
    standard_cost = fields.Float(
        string='Standard Cost',
        digits=(16, 2)
    )
    last_purchase_cost = fields.Float(
        string='Last Purchase Cost',
        digits=(16, 2)
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )


class MaterialStock(models.Model):
    _name = 'honey.material.stock'
    _description = 'Material Stock Tracking'

    material_type_id = fields.Many2one(
        'honey.material.type',
        string='Material Type',
        required=True
    )
    material_subtype = fields.Char(
        string='Material Subtype'
    )
    
    # Stock information
    current_stock = fields.Float(
        string='Current Stock',
        required=True,
        default=0.0
    )
    minimum_stock = fields.Float(
        string='Minimum Stock Level',
        required=True,
        default=0.0
    )
    maximum_stock = fields.Float(
        string='Maximum Stock Level',
        required=True,
        default=0.0
    )
    
    # Location information
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        required=True
    )
    
    # Status tracking
    stock_status = fields.Selection([
        ('sufficient', 'Sufficient'),
        ('low', 'Low Stock'),
        ('critical', 'Critical Stock'),
        ('out_of_stock', 'Out of Stock'),
    ], string='Stock Status', compute='_compute_stock_status', store=True)
    
    # Last movement
    last_in_date = fields.Datetime(
        string='Last In Date'
    )
    last_out_date = fields.Datetime(
        string='Last Out Date'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('current_stock', 'minimum_stock')
    def _compute_stock_status(self):
        for record in self:
            if record.current_stock <= 0:
                record.stock_status = 'out_of_stock'
            elif record.current_stock <= record.minimum_stock * 0.5:
                record.stock_status = 'critical'
            elif record.current_stock <= record.minimum_stock:
                record.stock_status = 'low'
            else:
                record.stock_status = 'sufficient'


class MaterialMovement(models.Model):
    _name = 'honey.material.movement'
    _description = 'Material Movement Tracking'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    material_type_id = fields.Many2one(
        'honey.material.type',
        string='Material Type',
        required=True
    )
    material_subtype = fields.Char(
        string='Material Subtype'
    )
    
    # Movement details
    movement_type = fields.Selection([
        ('in', 'In'),
        ('out', 'Out'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ], string='Movement Type', required=True)
    
    quantity = fields.Float(
        string='Quantity',
        required=True
    )
    unit = fields.Char(
        string='Unit',
        related='material_type_id.unit_of_measure',
        store=True
    )
    
    # Location information
    from_location_id = fields.Many2one(
        'stock.location',
        string='From Location'
    )
    to_location_id = fields.Many2one(
        'stock.location',
        string='To Location'
    )
    
    # Reference information
    reference = fields.Char(
        string='Reference'
    )
    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch'
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order'
    )
    
    # User and date
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.material.movement') or _('New')
        return super().create(vals)

    def action_process_movement(self):
        """Process the material movement and update stock"""
        for record in self:
            # Update material stock
            stock = self.env['honey.material.stock'].search([
                ('material_type_id', '=', record.material_type_id.id),
                ('material_subtype', '=', record.material_subtype),
                ('location_id', '=', record.to_location_id.id if record.movement_type == 'in' else record.from_location_id.id)
            ])
            
            if not stock:
                # Create new stock record
                stock = self.env['honey.material.stock'].create({
                    'material_type_id': record.material_type_id.id,
                    'material_subtype': record.material_subtype,
                    'warehouse_id': record.to_location_id.warehouse_id.id if record.movement_type == 'in' else record.from_location_id.warehouse_id.id,
                    'location_id': record.to_location_id.id if record.movement_type == 'in' else record.from_location_id.id,
                })
            
            # Update stock quantity
            if record.movement_type == 'in':
                stock.current_stock += record.quantity
                stock.last_in_date = record.date
            elif record.movement_type == 'out':
                stock.current_stock -= record.quantity
                stock.last_out_date = record.date
                if stock.current_stock < 0:
                    stock.current_stock = 0  # Prevent negative stock
