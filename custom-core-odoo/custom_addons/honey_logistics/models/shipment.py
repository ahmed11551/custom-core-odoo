# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import qrcode
import base64
from io import BytesIO


class Shipment(models.Model):
    _name = 'honey.shipment'
    _description = 'Honey Sticks Shipment'
    _order = 'shipment_date desc, name'

    name = fields.Char(
        string='Shipment Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Basic information
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
    region_id = fields.Many2one(
        'honey.region',
        string='Region',
        related='sale_order_id.honey_region_id',
        store=True
    )
    agent_id = fields.Many2one(
        'honey.agent',
        string='Agent',
        related='sale_order_id.honey_agent_id',
        store=True
    )
    
    # Shipment details
    shipment_date = fields.Datetime(
        string='Shipment Date',
        required=True,
        default=fields.Datetime.now
    )
    expected_delivery_date = fields.Date(
        string='Expected Delivery Date'
    )
    actual_delivery_date = fields.Date(
        string='Actual Delivery Date'
    )
    
    # Status tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready for Shipment'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Packaging information
    packaging_ids = fields.One2many(
        'honey.packaging',
        'shipment_id',
        string='Packaging'
    )
    total_boxes = fields.Integer(
        string='Total Boxes',
        compute='_compute_packaging_totals',
        store=True
    )
    total_sticks = fields.Integer(
        string='Total Sticks',
        compute='_compute_packaging_totals',
        store=True
    )
    
    # QR confirmation
    qr_code = fields.Char(
        string='QR Code',
        readonly=True
    )
    qr_image = fields.Binary(
        string='QR Code Image',
        readonly=True
    )
    qr_confirmed = fields.Boolean(
        string='QR Confirmed',
        default=False,
        tracking=True
    )
    qr_confirmation_date = fields.Datetime(
        string='QR Confirmation Date'
    )
    qr_confirmed_by = fields.Many2one(
        'res.users',
        string='QR Confirmed By'
    )
    
    # Shipping information
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier'
    )
    tracking_number = fields.Char(
        string='Tracking Number'
    )
    shipping_cost = fields.Float(
        string='Shipping Cost',
        digits=(16, 2)
    )
    
    # Delivery address
    delivery_address = fields.Text(
        string='Delivery Address'
    )
    delivery_contact = fields.Char(
        string='Delivery Contact'
    )
    delivery_phone = fields.Char(
        string='Delivery Phone'
    )
    
    # Special instructions
    special_instructions = fields.Text(
        string='Special Instructions'
    )
    urgent_delivery = fields.Boolean(
        string='Urgent Delivery',
        default=False
    )
    
    # KPI tracking
    processing_time = fields.Float(
        string='Processing Time (Hours)',
        compute='_compute_processing_time',
        store=True
    )
    delivery_time = fields.Float(
        string='Delivery Time (Days)',
        compute='_compute_delivery_time',
        store=True
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('packaging_ids.boxes_count', 'packaging_ids.sticks_count')
    def _compute_packaging_totals(self):
        for record in self:
            record.total_boxes = sum(record.packaging_ids.mapped('boxes_count'))
            record.total_sticks = sum(record.packaging_ids.mapped('sticks_count'))

    @api.depends('sale_order_id.date_order', 'shipment_date')
    def _compute_processing_time(self):
        for record in self:
            if record.sale_order_id.date_order and record.shipment_date:
                delta = record.shipment_date - record.sale_order_id.date_order
                record.processing_time = delta.total_seconds() / 3600  # Convert to hours
            else:
                record.processing_time = 0.0

    @api.depends('shipment_date', 'actual_delivery_date')
    def _compute_delivery_time(self):
        for record in self:
            if record.shipment_date and record.actual_delivery_date:
                delta = record.actual_delivery_date - record.shipment_date.date()
                record.delivery_time = delta.days
            else:
                record.delivery_time = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.shipment') or _('New')
        return super().create(vals)

    def action_generate_qr_code(self):
        """Generate QR code for shipment"""
        for record in self:
            if not record.qr_code:
                # Generate unique QR code
                qr_data = f"SHIPMENT:{record.name}:{record.sale_order_id.name}:{record.customer_id.name}"
                record.qr_code = qr_data
                
                # Generate QR code image
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                record.qr_image = base64.b64encode(buffer.getvalue())

    def action_confirm_qr(self):
        """Confirm QR delivery"""
        for record in self:
            if not record.qr_code:
                record.action_generate_qr_code()
            
            record.qr_confirmed = True
            record.qr_confirmation_date = fields.Datetime.now()
            record.qr_confirmed_by = self.env.user.id
            
            # Update sale order QR status
            record.sale_order_id.action_confirm_qr()
            
            # Update shipment status
            record.state = 'delivered'
            record.actual_delivery_date = fields.Date.today()

    def action_pack(self):
        """Pack shipment"""
        for record in self:
            if record.state != 'ready':
                raise ValidationError(_('Shipment must be ready before packing.'))
            record.state = 'packed'

    def action_ship(self):
        """Ship the order"""
        for record in self:
            if record.state != 'packed':
                raise ValidationError(_('Shipment must be packed before shipping.'))
            record.state = 'shipped'
            record.shipment_date = fields.Datetime.now()

    def action_deliver(self):
        """Mark as delivered"""
        for record in self:
            if record.state != 'shipped':
                raise ValidationError(_('Shipment must be shipped before delivery.'))
            record.state = 'delivered'
            record.actual_delivery_date = fields.Date.today()

    def action_return(self):
        """Mark as returned"""
        for record in self:
            if record.state not in ['shipped', 'delivered']:
                raise ValidationError(_('Only shipped or delivered orders can be returned.'))
            record.state = 'returned'

    def action_cancel(self):
        """Cancel shipment"""
        for record in self:
            if record.state in ['delivered']:
                raise ValidationError(_('Cannot cancel delivered shipments.'))
            record.state = 'cancelled'


class Packaging(models.Model):
    _name = 'honey.packaging'
    _description = 'Honey Sticks Packaging'

    shipment_id = fields.Many2one(
        'honey.shipment',
        string='Shipment',
        required=True,
        ondelete='cascade'
    )
    
    # Packaging details
    package_type = fields.Selection([
        ('box', 'Box'),
        ('display', 'Display'),
        ('gift_box', 'Gift Box'),
        ('bulk', 'Bulk Package'),
    ], string='Package Type', required=True, default='box')
    
    package_size = fields.Char(
        string='Package Size',
        required=True
    )
    
    # Quantities
    boxes_count = fields.Integer(
        string='Number of Boxes',
        required=True,
        default=1
    )
    sticks_count = fields.Integer(
        string='Number of Sticks',
        required=True
    )
    displays_count = fields.Integer(
        string='Number of Displays',
        default=0
    )
    
    # Product information
    honey_type = fields.Selection([
        ('acacia', 'Acacia Honey'),
        ('linden', 'Linden Honey'),
        ('sunflower', 'Sunflower Honey'),
        ('buckwheat', 'Buckwheat Honey'),
        ('wildflower', 'Wildflower Honey'),
        ('manuka', 'Manuka Honey'),
    ], string='Honey Type', required=True)
    
    batch_numbers = fields.Char(
        string='Batch Numbers'
    )
    
    # Quality information
    quality_grade = fields.Selection([
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    ], string='Quality Grade', required=True, default='standard')
    
    # Packaging materials
    box_material = fields.Char(
        string='Box Material'
    )
    label_template = fields.Char(
        string='Label Template'
    )
    
    # Weight and dimensions
    weight = fields.Float(
        string='Weight (kg)',
        digits=(8, 3)
    )
    length = fields.Float(
        string='Length (cm)',
        digits=(8, 2)
    )
    width = fields.Float(
        string='Width (cm)',
        digits=(8, 2)
    )
    height = fields.Float(
        string='Height (cm)',
        digits=(8, 2)
    )
    
    # Status
    packed = fields.Boolean(
        string='Packed',
        default=False
    )
    packed_by = fields.Many2one(
        'res.users',
        string='Packed By'
    )
    packed_date = fields.Datetime(
        string='Packed Date'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    def action_pack(self):
        """Mark package as packed"""
        for record in self:
            record.packed = True
            record.packed_by = self.env.user.id
            record.packed_date = fields.Datetime.now()
