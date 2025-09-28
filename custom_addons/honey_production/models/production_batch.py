# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductionBatch(models.Model):
    _name = 'honey.production.batch'
    _description = 'Honey Sticks Production Batch'
    _order = 'production_date desc, name'

    name = fields.Char(
        string='Batch Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Основная информация
    production_date = fields.Date(
        string='Production Date',
        required=True,
        default=fields.Date.today
    )
    honey_type = fields.Selection([
        ('acacia', 'Acacia Honey'),
        ('linden', 'Linden Honey'),
        ('sunflower', 'Sunflower Honey'),
        ('buckwheat', 'Buckwheat Honey'),
        ('wildflower', 'Wildflower Honey'),
        ('manuka', 'Manuka Honey'),
    ], string='Honey Type', required=True)
    
    # Нумерация стиков (уникальная система)
    tape_roll_number = fields.Char(
        string='Tape Roll Number',
        required=True,
        help='Номер рулона ленты для упаковки стиков'
    )
    sticker_start_number = fields.Integer(
        string='Start Sticker Number',
        required=True,
        help='Номер стика с которого начинается выпуск'
    )
    sticker_end_number = fields.Integer(
        string='End Sticker Number',
        required=True,
        help='Номер стика которым заканчивается выпуск'
    )
    total_stickers = fields.Integer(
        string='Total Stickers',
        compute='_compute_total_stickers',
        store=True,
        help='Общее количество стиков в партии'
    )
    
    # HACCP контроль (санитарные нормы)
    haccp_instructions_signed = fields.Boolean(
        string='HACCP Instructions Signed',
        default=False,
        help='Подтверждение прохождения инструктажа по HACCP'
    )
    haccp_signature_date = fields.Datetime(
        string='HACCP Signature Date'
    )
    haccp_signed_by = fields.Many2one(
        'res.users',
        string='HACCP Signed By'
    )
    haccp_signature = fields.Binary(
        string='HACCP Signature',
        help='Электронная подпись сотрудника'
    )
    haccp_instructions_text = fields.Text(
        string='HACCP Instructions',
        default='''
        ИНСТРУКЦИЯ ПО HACCP:
        1. Соблюдение личной гигиены
        2. Использование защитной одежды
        3. Контроль температуры производства
        4. Проверка качества сырья
        5. Санитарная обработка оборудования
        '''
    )
    
    # BG инструктаж (охрана труда)
    bg_instructions_signed = fields.Boolean(
        string='BG Instructions Signed',
        default=False,
        help='Подтверждение прохождения инструктажа по охране труда'
    )
    bg_signature_date = fields.Datetime(
        string='BG Signature Date'
    )
    bg_signed_by = fields.Many2one(
        'res.users',
        string='BG Signed By'
    )
    bg_signature = fields.Binary(
        string='BG Signature',
        help='Электронная подпись сотрудника'
    )
    bg_instructions_text = fields.Text(
        string='BG Instructions',
        default='''
        ИНСТРУКЦИЯ ПО ОХРАНЕ ТРУДА:
        1. Правила работы с оборудованием
        2. Использование средств защиты
        3. Действия при авариях
        4. Эвакуационные пути
        5. Первая помощь
        '''
    )
    
    # Учёт времени сотрудников производства
    employee_time_ids = fields.One2many(
        'honey.employee.time',
        'batch_id',
        string='Employee Time Tracking'
    )
    
    # Статус партии
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Контроль качества
    quality_control_ids = fields.One2many(
        'honey.quality.control',
        'batch_id',
        string='Quality Control'
    )
    quality_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], string='Quality Status', default='pending')
    
    # Материалы
    material_requirements_ids = fields.One2many(
        'honey.material.requirement',
        'batch_id',
        string='Material Requirements'
    )
    
    # Примечания
    notes = fields.Text(
        string='Production Notes'
    )

    @api.depends('sticker_start_number', 'sticker_end_number')
    def _compute_total_stickers(self):
        for record in self:
            if record.sticker_start_number and record.sticker_end_number:
                record.total_stickers = record.sticker_end_number - record.sticker_start_number + 1
            else:
                record.total_stickers = 0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('honey.production.batch') or _('New')
        return super().create(vals)

    @api.constrains('sticker_start_number', 'sticker_end_number')
    def _check_sticker_range(self):
        for record in self:
            if record.sticker_start_number >= record.sticker_end_number:
                raise ValidationError(_('Start sticker number must be less than end sticker number.'))

    def action_sign_haccp(self):
        """Подписание инструктажа HACCP"""
        for record in self:
            record.haccp_instructions_signed = True
            record.haccp_signature_date = fields.Datetime.now()
            record.haccp_signed_by = self.env.user.id
            # Здесь можно добавить логику сохранения электронной подписи

    def action_sign_bg(self):
        """Подписание инструктажа по охране труда"""
        for record in self:
            record.bg_instructions_signed = True
            record.bg_signature_date = fields.Datetime.now()
            record.bg_signed_by = self.env.user.id
            # Здесь можно добавить логику сохранения электронной подписи

    def action_start_production(self):
        """Начать производство"""
        for record in self:
            if not record.haccp_instructions_signed or not record.bg_instructions_signed:
                raise ValidationError(_('Both HACCP and BG instructions must be signed before starting production.'))
            record.state = 'in_progress'

    def action_complete_production(self):
        """Завершить производство"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_('Production must be in progress to complete.'))
            record.state = 'completed'

    def action_search_by_sticker(self, sticker_number):
        """Поиск партии по номеру стика"""
        return self.search([
            ('sticker_start_number', '<=', sticker_number),
            ('sticker_end_number', '>=', sticker_number)
        ])


class EmployeeTime(models.Model):
    _name = 'honey.employee.time'
    _description = 'Employee Time Tracking for Production'

    batch_id = fields.Many2one(
        'honey.production.batch',
        string='Production Batch',
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True
    )
    
    # Учёт времени
    login_time = fields.Datetime(
        string='Login Time',
        required=True,
        default=fields.Datetime.now
    )
    logout_time = fields.Datetime(
        string='Logout Time'
    )
    work_duration = fields.Float(
        string='Work Duration (Hours)',
        compute='_compute_duration',
        store=True
    )
    
    # Статус
    state = fields.Selection([
        ('logged_in', 'Logged In'),
        ('logged_out', 'Logged Out'),
    ], string='Status', default='logged_in', tracking=True)
    
    # Примечания
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('login_time', 'logout_time')
    def _compute_duration(self):
        for record in self:
            if record.login_time and record.logout_time:
                delta = record.logout_time - record.login_time
                record.work_duration = delta.total_seconds() / 3600
            else:
                record.work_duration = 0.0

    def action_logout(self):
        """Выход из системы"""
        for record in self:
            if record.state != 'logged_in':
                raise ValidationError(_('Employee must be logged in to logout.'))
            record.logout_time = fields.Datetime.now()
            record.state = 'logged_out'

    def action_login(self):
        """Вход в систему"""
        for record in self:
            if record.state != 'logged_out':
                raise ValidationError(_('Employee must be logged out to login.'))
            record.login_time = fields.Datetime.now()
            record.state = 'logged_in'