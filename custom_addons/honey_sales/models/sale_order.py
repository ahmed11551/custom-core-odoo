# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Honey Sticks specific fields
    honey_region_id = fields.Many2one(
        'honey.region',
        string='Sales Region',
        related='partner_id.honey_region_id',
        store=True,
        readonly=True
    )
    honey_agent_id = fields.Many2one(
        'honey.agent',
        string='Sales Agent',
        related='partner_id.honey_agent_id',
        store=True,
        readonly=True
    )
    
    # QR confirmation workflow
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
    
    # Commission tracking
    commission_ids = fields.One2many(
        'honey.commission',
        'sale_order_id',
        string='Commissions'
    )
    total_commission = fields.Float(
        string='Total Commission',
        digits=(16, 2),
        compute='_compute_total_commission',
        store=True
    )
    
    # Regional analytics
    honey_customer_type = fields.Selection([
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('distributor', 'Distributor'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
    ], string='Customer Type', related='partner_id.honey_customer_type', store=True)
    
    # Status tracking
    honey_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('qr_confirmed', 'QR Confirmed'),
    ], string='Honey Status', compute='_compute_honey_status', store=True)
    
    # Delivery tracking
    delivery_status = fields.Selection([
        ('pending', 'Pending'),
        ('ready', 'Ready for Shipment'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
    ], string='Delivery Status', default='pending', tracking=True)
    
    # Special requirements
    special_instructions = fields.Text(
        string='Special Instructions'
    )
    urgent_delivery = fields.Boolean(
        string='Urgent Delivery',
        default=False
    )

    @api.depends('commission_ids.amount')
    def _compute_total_commission(self):
        for record in self:
            record.total_commission = sum(record.commission_ids.mapped('amount'))

    @api.depends('state', 'qr_confirmed')
    def _compute_honey_status(self):
        for record in self:
            if record.state == 'cancel':
                record.honey_status = 'cancel'
            elif record.qr_confirmed:
                record.honey_status = 'qr_confirmed'
            elif record.state == 'done':
                record.honey_status = 'done'
            elif record.state == 'sale':
                record.honey_status = 'sale'
            elif record.state == 'sent':
                record.honey_status = 'sent'
            else:
                record.honey_status = 'draft'

    def action_confirm_qr(self):
        """Confirm QR delivery and create commissions"""
        for record in self:
            if record.state not in ['sale', 'done']:
                raise ValidationError(_('Order must be confirmed before QR confirmation.'))
            
            if record.qr_confirmed:
                raise ValidationError(_('Order is already QR confirmed.'))
            
            record.qr_confirmed = True
            record.qr_confirmation_date = fields.Datetime.now()
            record.qr_confirmed_by = self.env.user.id
            
            # Create commission if agent exists
            if record.honey_agent_id:
                commission_rate = record.honey_agent_id.commission_rate
                # Check for commission rules
                if hasattr(self.env['honey.commission.rule'], 'get_commission_rate'):
                    commission_rate = self.env['honey.commission.rule'].get_commission_rate(
                        record.honey_agent_id,
                        record.partner_id,
                        record.amount_total,
                        record.date_order.date()
                    )
                
                self.env['honey.commission'].create({
                    'agent_id': record.honey_agent_id.id,
                    'sale_order_id': record.id,
                    'base_amount': record.amount_total,
                    'commission_rate': commission_rate,
                    'state': 'confirmed',
                    'qr_confirmed': True,
                    'qr_confirmation_date': fields.Datetime.now(),
                })
            
            # Update delivery status
            record.delivery_status = 'delivered'

    def action_cancel_qr(self):
        """Cancel QR confirmation and adjust commissions"""
        for record in self:
            if not record.qr_confirmed:
                raise ValidationError(_('Order is not QR confirmed.'))
            
            record.qr_confirmed = False
            record.qr_confirmation_date = False
            record.qr_confirmed_by = False
            
            # Cancel related commissions
            for commission in record.commission_ids:
                if commission.state == 'confirmed':
                    commission.action_cancel()
            
            # Update delivery status
            record.delivery_status = 'shipped'

    def action_view_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commissions'),
            'res_model': 'honey.commission',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }

    @api.model
    def create(self, vals):
        """Override create to set honey fields from partner"""
        if 'partner_id' in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner.honey_region_id:
                vals['honey_region_id'] = partner.honey_region_id.id
            if partner.honey_agent_id:
                vals['honey_agent_id'] = partner.honey_agent_id.id
        return super().create(vals)

    def write(self, vals):
        """Override write to update honey fields when partner changes"""
        if 'partner_id' in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            vals['honey_region_id'] = partner.honey_region_id.id if partner.honey_region_id else False
            vals['honey_agent_id'] = partner.honey_agent_id.id if partner.honey_agent_id else False
        return super().write(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Honey Sticks specific fields
    honey_product_type = fields.Selection([
        ('honey_stick', 'Honey Stick'),
        ('display', 'Display'),
        ('packaging', 'Packaging'),
        ('other', 'Other'),
    ], string='Product Type', compute='_compute_honey_product_type', store=True)
    
    # Batch tracking
    batch_number = fields.Char(
        string='Batch Number'
    )
    production_date = fields.Date(
        string='Production Date'
    )
    expiry_date = fields.Date(
        string='Expiry Date'
    )
    
    # Quality tracking
    quality_grade = fields.Selection([
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    ], string='Quality Grade', default='standard')

    @api.depends('product_id')
    def _compute_honey_product_type(self):
        for record in self:
            if record.product_id:
                # Check product category or tags for honey stick type
                if 'honey' in record.product_id.name.lower() or 'stick' in record.product_id.name.lower():
                    record.honey_product_type = 'honey_stick'
                elif 'display' in record.product_id.name.lower():
                    record.honey_product_type = 'display'
                elif 'packaging' in record.product_id.name.lower() or 'box' in record.product_id.name.lower():
                    record.honey_product_type = 'packaging'
                else:
                    record.honey_product_type = 'other'
            else:
                record.honey_product_type = 'other'
