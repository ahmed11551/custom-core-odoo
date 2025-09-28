# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class QualityControl(models.Model):
    _name = 'honey.quality.control'
    _description = 'Quality Control for Production Batches'
    _order = 'control_date desc'

    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch',
        required=True
    )
    control_date = fields.Datetime(
        string='Control Date',
        default=fields.Datetime.now,
        required=True
    )
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        required=True,
        default=lambda self: self.env.user
    )
    
    # Результаты контроля
    result = fields.Selection([
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional'),
    ], string='Result', required=True)
    
    # Параметры контроля
    temperature = fields.Float(
        string='Temperature (°C)',
        help='Температура при производстве'
    )
    humidity = fields.Float(
        string='Humidity (%)',
        help='Влажность воздуха'
    )
    ph_level = fields.Float(
        string='pH Level',
        help='Уровень pH мёда'
    )
    viscosity = fields.Float(
        string='Viscosity',
        help='Вязкость мёда'
    )
    
    # Визуальный контроль
    color_check = fields.Boolean(
        string='Color Check',
        help='Проверка цвета мёда'
    )
    clarity_check = fields.Boolean(
        string='Clarity Check',
        help='Проверка прозрачности'
    )
    consistency_check = fields.Boolean(
        string='Consistency Check',
        help='Проверка консистенции'
    )
    
    # Микробиологический контроль
    bacteria_count = fields.Float(
        string='Bacteria Count',
        help='Количество бактерий'
    )
    yeast_count = fields.Float(
        string='Yeast Count',
        help='Количество дрожжей'
    )
    mold_count = fields.Float(
        string='Mold Count',
        help='Количество плесени'
    )
    
    # Примечания
    notes = fields.Text(
        string='Control Notes'
    )
    recommendations = fields.Text(
        string='Recommendations'
    )
    
    # Фотографии
    photo_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Photos',
        domain=[('res_model', '=', 'honey.quality.control')]
    )

    @api.model
    def create(self, vals):
        """Создание контроля качества с обновлением статуса партии"""
        control = super().create(vals)
        control._update_batch_quality_status()
        return control

    def _update_batch_quality_status(self):
        """Обновление статуса качества партии"""
        for control in self:
            if control.batch_id:
                if control.result == 'passed':
                    control.batch_id.quality_status = 'passed'
                elif control.result == 'failed':
                    control.batch_id.quality_status = 'failed'
                else:
                    control.batch_id.quality_status = 'pending'