# -*- coding: utf-8 -*-

import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api, _


class QRGenerator(models.Model):
    _name = 'honey.qr.generator'
    _description = 'QR Code Generator for Honey Sticks'

    def generate_qr_code(self, data, size=200):
        """Генерация QR кода"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Изменение размера изображения
        img = img.resize((size, size))
        
        # Конвертация в base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_code

    def generate_shipment_qr(self, shipment):
        """Генерация QR кода для отгрузки"""
        data = f"""
        SHIPMENT: {shipment.name}
        DATE: {shipment.shipment_date}
        CUSTOMER: {shipment.customer_id.name}
        BATCHES: {', '.join([batch.name for batch in shipment.batch_ids])}
        TRACKING: {shipment.tracking_number or 'N/A'}
        """
        return self.generate_qr_code(data)

    def generate_batch_qr(self, batch):
        """Генерация QR кода для партии"""
        data = f"""
        BATCH: {batch.name}
        DATE: {batch.production_date}
        HONEY: {batch.honey_type}
        RANGE: {batch.sticker_start_number}-{batch.sticker_end_number}
        ROLL: {batch.tape_roll_number}
        """
        return self.generate_qr_code(data)

    def generate_sticker_qr(self, sticker_number, batch):
        """Генерация QR кода для отдельного стика"""
        data = f"""
        STICKER: {sticker_number}
        BATCH: {batch.name}
        DATE: {batch.production_date}
        HONEY: {batch.honey_type}
        ROLL: {batch.tape_roll_number}
        """
        return self.generate_qr_code(data, size=100)
