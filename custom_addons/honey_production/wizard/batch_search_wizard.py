# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BatchSearchWizard(models.TransientModel):
    _name = 'honey.batch.search.wizard'
    _description = 'Batch Search Wizard by Sticker Number'

    sticker_number = fields.Integer(
        string='Sticker Number',
        required=True,
        help='Введите номер стика для поиска партии'
    )
    search_result = fields.Text(
        string='Search Result',
        readonly=True
    )
    found_batch_id = fields.Many2one(
        'honey.production.batch',
        string='Found Batch',
        readonly=True
    )

    def action_search(self):
        """Поиск партии по номеру стика"""
        self.ensure_one()
        
        if not self.sticker_number:
            raise UserError(_('Please enter a sticker number.'))
        
        # Поиск партии по номеру стика
        batch = self.env['honey.production.batch'].search([
            ('sticker_start_number', '<=', self.sticker_number),
            ('sticker_end_number', '>=', self.sticker_number)
        ], limit=1)
        
        if batch:
            self.found_batch_id = batch.id
            self.search_result = f"""
НАЙДЕННАЯ ПАРТИЯ:

Номер партии: {batch.name}
Дата производства: {batch.production_date}
Сорт мёда: {dict(batch._fields['honey_type'].selection)[batch.honey_type]}
Номер рулона: {batch.tape_roll_number}
Диапазон стиков: {batch.sticker_start_number} - {batch.sticker_end_number}
Общее количество стиков: {batch.total_stickers}
Статус партии: {dict(batch._fields['state'].selection)[batch.state]}
Статус качества: {dict(batch._fields['quality_status'].selection)[batch.quality_status]}

HACCP инструктаж: {'✓ Подписан' if batch.haccp_instructions_signed else '✗ Не подписан'}
BG инструктаж: {'✓ Подписан' if batch.bg_instructions_signed else '✗ Не подписан'}

Время производства: {batch.production_date}
            """
        else:
            self.found_batch_id = False
            self.search_result = f"""
ПАРТИЯ НЕ НАЙДЕНА

Стикер с номером {self.sticker_number} не найден ни в одной партии.

Возможные причины:
- Неправильно введен номер стика
- Стикер не был произведен
- Партия была удалена из системы
- Ошибка в нумерации стиков
            """

    def action_view_batch(self):
        """Открыть найденную партию"""
        self.ensure_one()
        if not self.found_batch_id:
            raise UserError(_('No batch found to view.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Batch'),
            'res_model': 'honey.production.batch',
            'res_id': self.found_batch_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_clear_search(self):
        """Очистить результаты поиска"""
        self.ensure_one()
        self.sticker_number = 0
        self.search_result = ''
        self.found_batch_id = False
