# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaterialRequirement(models.Model):
    _name = 'honey.material.requirement'
    _description = 'Material Requirements for Production Batches'

    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch',
        required=True
    )
    material_id = fields.Many2one(
        'product.product',
        string='Material',
        required=True,
        domain=[('type', '=', 'product')]
    )
    material_type = fields.Selection([
        ('honey', 'Honey'),
        ('tape', 'Packaging Tape'),
        ('display', 'Display Box'),
        ('cardboard', 'Cardboard Box'),
        ('label', 'Label'),
        ('other', 'Other'),
    ], string='Material Type', required=True)
    
    # Количества
    required_quantity = fields.Float(
        string='Required Quantity',
        required=True
    )
    used_quantity = fields.Float(
        string='Used Quantity',
        default=0.0
    )
    unit = fields.Many2one(
        'uom.uom',
        string='Unit',
        related='material_id.uom_id',
        store=True
    )
    
    # Стоимость
    unit_cost = fields.Float(
        string='Unit Cost',
        related='material_id.standard_price',
        store=True
    )
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True
    )
    
    # Статус
    status = fields.Selection([
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
        ('used', 'Used'),
        ('shortage', 'Shortage'),
    ], string='Status', default='pending')

    @api.depends('used_quantity', 'unit_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.used_quantity * record.unit_cost

    @api.model
    def create_requirements_for_batch(self, batch):
        """Создание требований к материалам для партии"""
        # Стандартные материалы для мёдовых стиков
        materials = [
            {
                'material_type': 'honey',
                'required_quantity': batch.total_stickers * 0.008,  # 8г на стик
                'name': 'Honey - ' + dict(batch._fields['honey_type'].selection)[batch.honey_type]
            },
            {
                'material_type': 'tape',
                'required_quantity': 1,  # 1 рулон на партию
                'name': 'Packaging Tape Roll'
            },
            {
                'material_type': 'display',
                'required_quantity': batch.total_stickers / 100,  # 100 стиков в дисплее
                'name': 'Display Box'
            },
            {
                'material_type': 'cardboard',
                'required_quantity': 1,  # 1 картонная коробка
                'name': 'Cardboard Box'
            },
        ]
        
        for material_data in materials:
            # Поиск существующего продукта или создание нового
            product = self.env['product.product'].search([
                ('name', 'ilike', material_data['name'])
            ], limit=1)
            
            if not product:
                product = self.env['product.product'].create({
                    'name': material_data['name'],
                    'type': 'product',
                    'categ_id': self.env.ref('product.product_category_all').id,
                })
            
            self.create({
                'batch_id': batch.id,
                'material_id': product.id,
                'material_type': material_data['material_type'],
                'required_quantity': material_data['required_quantity'],
            })
