# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import qrcode
import base64
from io import BytesIO


class QRConfirmation(models.Model):
    _name = 'honey.qr.confirmation'
    _description = 'QR Confirmation System'

    name = fields.Char(
        string='QR Reference',
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
    
    # QR Code information
    qr_code = fields.Char(
        string='QR Code',
        required=True,
        readonly=True
    )
    qr_image = fields.Binary(
        string='QR Code Image',
        readonly=True
    )
    
    # Confirmation details
    confirmation_type = fields.Selection([
        ('delivery', 'Delivery Confirmation'),
        ('pickup', 'Pickup Confirmation'),
        ('return', 'Return Confirmation'),
        ('inspection', 'Inspection Confirmation'),
    ], string='Confirmation Type', required=True, default='delivery')
    
    confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        required=True,
        default=lambda self: self.env.user
    )
    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        required=True,
        default=fields.Datetime.now
    )
    
    # Location information
    confirmation_location = fields.Char(
        string='Confirmation Location'
    )
    gps_coordinates = fields.Char(
        string='GPS Coordinates'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Verification
    verified_by = fields.Many2one(
        'res.users',
        string='Verified By'
    )
    verification_date = fields.Datetime(
        string='Verification Date'
    )
    verification_notes = fields.Text(
        string='Verification Notes'
    )
    
    # Photos and attachments
    confirmation_photo = fields.Binary(
        string='Confirmation Photo'
    )
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Attachments',
        domain=[('res_model', '=', 'honey.qr.confirmation')]
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.qr.confirmation') or _('New')
        
        # Generate QR code if not provided
        if not vals.get('qr_code'):
            shipment = self.env['honey.shipment'].browse(vals['shipment_id'])
            qr_data = f"QR:{vals['name']}:{shipment.name}:{shipment.sale_order_id.name}"
            vals['qr_code'] = qr_data
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            vals['qr_image'] = base64.b64encode(buffer.getvalue())
        
        return super().create(vals)

    def action_confirm(self):
        """Confirm QR delivery"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft confirmations can be confirmed.'))
            
            record.state = 'confirmed'
            
            # Update shipment status
            if record.shipment_id:
                record.shipment_id.action_confirm_qr()

    def action_verify(self):
        """Verify QR confirmation"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_('Only confirmed records can be verified.'))
            
            record.state = 'verified'
            record.verified_by = self.env.user.id
            record.verification_date = fields.Datetime.now()

    def action_cancel(self):
        """Cancel QR confirmation"""
        for record in self:
            if record.state in ['verified']:
                raise ValidationError(_('Cannot cancel verified confirmations.'))
            record.state = 'cancelled'

    def action_generate_qr(self):
        """Generate new QR code"""
        for record in self:
            qr_data = f"QR:{record.name}:{record.shipment_id.name}:{record.sale_order_id.name}"
            record.qr_code = qr_data
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            record.qr_image = base64.b64encode(buffer.getvalue())


class QRScanner(models.Model):
    _name = 'honey.qr.scanner'
    _description = 'QR Code Scanner'

    name = fields.Char(
        string='Scanner Name',
        required=True
    )
    
    # Scanner details
    scanner_type = fields.Selection([
        ('mobile', 'Mobile App'),
        ('handheld', 'Handheld Scanner'),
        ('fixed', 'Fixed Scanner'),
        ('camera', 'Camera Scanner'),
    ], string='Scanner Type', required=True)
    
    location = fields.Char(
        string='Location'
    )
    
    # User assignment
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned User'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    total_scans = fields.Integer(
        string='Total Scans',
        compute='_compute_scan_statistics',
        store=True
    )
    successful_scans = fields.Integer(
        string='Successful Scans',
        compute='_compute_scan_statistics',
        store=True
    )
    last_scan_date = fields.Datetime(
        string='Last Scan Date',
        compute='_compute_scan_statistics',
        store=True
    )

    @api.depends('assigned_user_id')
    def _compute_scan_statistics(self):
        for record in self:
            if record.assigned_user_id:
                confirmations = self.env['honey.qr.confirmation'].search([
                    ('confirmed_by', '=', record.assigned_user_id.id)
                ])
                record.total_scans = len(confirmations)
                record.successful_scans = len(confirmations.filtered(lambda r: r.state == 'confirmed'))
                if confirmations:
                    record.last_scan_date = max(confirmations.mapped('confirmation_date'))
                else:
                    record.last_scan_date = False
            else:
                record.total_scans = 0
                record.successful_scans = 0
                record.last_scan_date = False


class QRReport(models.Model):
    _name = 'honey.qr.report'
    _description = 'QR Confirmation Report'
    _auto = False

    confirmation_date = fields.Date(string='Confirmation Date', readonly=True)
    month = fields.Char(string='Month', readonly=True)
    year = fields.Integer(string='Year', readonly=True)
    region_id = fields.Many2one('honey.region', string='Region', readonly=True)
    agent_id = fields.Many2one('honey.agent', string='Agent', readonly=True)
    confirmation_type = fields.Selection([
        ('delivery', 'Delivery Confirmation'),
        ('pickup', 'Pickup Confirmation'),
        ('return', 'Return Confirmation'),
        ('inspection', 'Inspection Confirmation'),
    ], string='Confirmation Type', readonly=True)
    total_confirmations = fields.Integer(string='Total Confirmations', readonly=True)
    successful_confirmations = fields.Integer(string='Successful Confirmations', readonly=True)
    success_rate = fields.Float(string='Success Rate (%)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    qc.confirmation_date::date AS confirmation_date,
                    to_char(qc.confirmation_date, 'YYYY-MM') AS month,
                    extract(year from qc.confirmation_date) AS year,
                    s.region_id,
                    s.agent_id,
                    qc.confirmation_type,
                    count(qc.id) AS total_confirmations,
                    count(CASE WHEN qc.state = 'confirmed' THEN 1 END) AS successful_confirmations,
                    CASE 
                        WHEN count(qc.id) > 0 THEN 
                            (count(CASE WHEN qc.state = 'confirmed' THEN 1 END)::float / count(qc.id)::float) * 100
                        ELSE 0 
                    END AS success_rate
                FROM honey_qr_confirmation qc
                JOIN honey_shipment s ON qc.shipment_id = s.id
                GROUP BY qc.confirmation_date::date, s.region_id, s.agent_id, qc.confirmation_type
            )
        """ % self._table)
