# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DashboardData(models.Model):
    _name = 'honey.dashboard.data'
    _description = 'Dashboard Data Provider'
    _auto = False

    @api.model
    def get_director_dashboard_data(self):
        """Get data for director dashboard"""
        today = fields.Date.today()
        month_start = today.replace(day=1)
        
        # Sales data
        sales_orders = self.env['sale.order'].search([
            ('date_order', '>=', month_start),
            ('state', 'in', ['sale', 'done'])
        ])
        
        # Shipments data
        shipments = self.env['honey.shipment'].search([
            ('shipment_date', '>=', month_start)
        ])
        
        # Commissions data
        commissions = self.env['honey.commission'].search([
            ('date', '>=', month_start),
            ('state', 'in', ['confirmed', 'paid'])
        ])
        
        # Production data
        production_batches = self.env['honey.production.batch'].search([
            ('planned_start_date', '>=', month_start)
        ])
        
        return {
            'sales': {
                'monthly_sales': sum(sales_orders.mapped('amount_total')),
                'monthly_orders': len(sales_orders),
                'today_shipments': len(shipments.filtered(lambda s: s.shipment_date.date() == today)),
                'week_shipments': len(shipments.filtered(lambda s: s.shipment_date.date() >= today - fields.timedelta(days=7))),
            },
            'commissions': {
                'total_commissions': sum(commissions.mapped('amount')),
                'paid_commissions': sum(commissions.filtered(lambda c: c.state == 'paid').mapped('amount')),
            },
            'production': {
                'total_batches': len(production_batches),
                'completed_batches': len(production_batches.filtered(lambda b: b.state == 'completed')),
                'in_progress_batches': len(production_batches.filtered(lambda b: b.state == 'in_progress')),
            },
            'logistics': {
                'total_shipments': len(shipments),
                'delivered_shipments': len(shipments.filtered(lambda s: s.state == 'delivered')),
                'qr_confirmed': len(shipments.filtered(lambda s: s.qr_confirmed)),
            }
        }

    @api.model
    def get_manager_dashboard_data(self, user_id):
        """Get data for sales manager dashboard"""
        user = self.env['res.users'].browse(user_id)
        manager_regions = self.env['honey.region'].search([('manager_id', '=', user_id)])
        
        today = fields.Date.today()
        month_start = today.replace(day=1)
        
        # Get agents in manager's regions
        agents = self.env['honey.agent'].search([('region_id', 'in', manager_regions.ids)])
        
        # Sales data for manager's regions
        sales_orders = self.env['sale.order'].search([
            ('honey_region_id', 'in', manager_regions.ids),
            ('date_order', '>=', month_start),
            ('state', 'in', ['sale', 'done'])
        ])
        
        return {
            'regions': {
                'total_regions': len(manager_regions),
                'total_agents': len(agents),
                'total_customers': len(self.env['res.partner'].search([
                    ('honey_region_id', 'in', manager_regions.ids),
                    ('is_company', '=', True)
                ])),
            },
            'sales': {
                'monthly_sales': sum(sales_orders.mapped('amount_total')),
                'monthly_orders': len(sales_orders),
                'agents_performance': self._get_agents_performance(agents, month_start),
            },
            'orders': {
                'pending_orders': len(sales_orders.filtered(lambda o: o.state == 'sale')),
                'ready_to_ship': len(sales_orders.filtered(lambda o: o.delivery_status == 'ready')),
                'shipped': len(sales_orders.filtered(lambda o: o.delivery_status == 'shipped')),
            }
        }

    @api.model
    def get_agent_dashboard_data(self, user_id):
        """Get data for sales agent dashboard"""
        agent = self.env['honey.agent'].search([('user_id', '=', user_id)], limit=1)
        if not agent:
            return {}
        
        today = fields.Date.today()
        month_start = today.replace(day=1)
        
        # Agent's sales data
        sales_orders = self.env['sale.order'].search([
            ('honey_agent_id', '=', agent.id),
            ('date_order', '>=', month_start),
            ('state', 'in', ['sale', 'done'])
        ])
        
        # Agent's commissions
        commissions = self.env['honey.commission'].search([
            ('agent_id', '=', agent.id),
            ('date', '>=', month_start),
            ('state', 'in', ['confirmed', 'paid'])
        ])
        
        # Agent's customers
        customers = self.env['res.partner'].search([
            ('honey_agent_id', '=', agent.id),
            ('is_company', '=', True)
        ])
        
        return {
            'sales': {
                'monthly_sales': sum(sales_orders.mapped('amount_total')),
                'monthly_orders': len(sales_orders),
                'target_achievement': agent.target_achievement,
                'monthly_target': agent.monthly_target,
            },
            'commissions': {
                'current_month': sum(commissions.mapped('amount')),
                'last_month': self._get_last_month_commissions(agent.id),
                'expected': self._get_expected_commissions(agent.id),
            },
            'customers': {
                'total_customers': len(customers),
                'active_customers': len(customers.filtered(lambda c: c.honey_status == 'active')),
                'recent_contacts': len(customers.filtered(lambda c: c.last_contact_date and c.last_contact_date >= today - fields.timedelta(days=7))),
            },
            'orders': {
                'pending_orders': len(sales_orders.filtered(lambda o: o.state == 'sale')),
                'qr_pending': len(sales_orders.filtered(lambda o: o.state in ['sale', 'done'] and not o.qr_confirmed)),
            }
        }

    @api.model
    def get_production_dashboard_data(self):
        """Get data for production dashboard"""
        today = fields.Date.today()
        week_start = today - fields.timedelta(days=today.weekday())
        
        # Production batches
        batches_today = self.env['honey.production.batch'].search([
            ('planned_start_date', '>=', today),
            ('planned_start_date', '<', today + fields.timedelta(days=1))
        ])
        
        batches_week = self.env['honey.production.batch'].search([
            ('planned_start_date', '>=', week_start),
            ('planned_start_date', '<', week_start + fields.timedelta(days=7))
        ])
        
        # Material availability
        material_requirements = self.env['honey.material.requirement'].search([
            ('batch_id.state', 'in', ['planned', 'ready', 'in_progress'])
        ])
        
        # Time tracking
        time_records = self.env['honey.time.tracking'].search([
            ('start_time', '>=', today),
            ('state', '=', 'completed')
        ])
        
        return {
            'planning': {
                'today_batches': len(batches_today),
                'week_batches': len(batches_week),
                'in_progress': len(self.env['honey.production.batch'].search([('state', '=', 'in_progress')])),
                'completed_today': len(self.env['honey.production.batch'].search([
                    ('state', '=', 'completed'),
                    ('actual_end_date', '>=', today),
                    ('actual_end_date', '<', today + fields.timedelta(days=1))
                ])),
            },
            'materials': {
                'available': len(material_requirements.filtered(lambda r: r.status == 'available')),
                'shortage': len(material_requirements.filtered(lambda r: r.status == 'shortage')),
                'unavailable': len(material_requirements.filtered(lambda r: r.status == 'unavailable')),
            },
            'time_tracking': {
                'total_hours_today': sum(time_records.mapped('duration')),
                'active_employees': len(time_records.mapped('employee_id')),
                'efficiency': self._calculate_production_efficiency(),
            }
        }

    @api.model
    def get_logistics_dashboard_data(self):
        """Get data for logistics dashboard"""
        today = fields.Date.today()
        week_start = today - fields.timedelta(days=today.weekday())
        
        # Shipments
        shipments_today = self.env['honey.shipment'].search([
            ('shipment_date', '>=', today),
            ('shipment_date', '<', today + fields.timedelta(days=1))
        ])
        
        shipments_week = self.env['honey.shipment'].search([
            ('shipment_date', '>=', week_start),
            ('shipment_date', '<', week_start + fields.timedelta(days=7))
        ])
        
        # QR confirmations
        qr_confirmations = self.env['honey.qr.confirmation'].search([
            ('confirmation_date', '>=', today),
            ('confirmation_date', '<', today + fields.timedelta(days=1))
        ])
        
        # Returns
        returns = self.env['honey.return.request'].search([
            ('return_date', '>=', today - fields.timedelta(days=30))
        ])
        
        return {
            'shipments': {
                'today': len(shipments_today),
                'week': len(shipments_week),
                'ready_to_ship': len(self.env['honey.shipment'].search([('state', '=', 'ready')])),
                'packed': len(self.env['honey.shipment'].search([('state', '=', 'packed')])),
                'shipped': len(self.env['honey.shipment'].search([('state', '=', 'shipped')])),
                'delivered': len(self.env['honey.shipment'].search([('state', '=', 'delivered')])),
            },
            'qr_confirmations': {
                'today': len(qr_confirmations),
                'confirmed': len(qr_confirmations.filtered(lambda q: q.state == 'confirmed')),
                'verified': len(qr_confirmations.filtered(lambda q: q.state == 'verified')),
            },
            'returns': {
                'total_returns': len(returns),
                'pending_returns': len(returns.filtered(lambda r: r.state in ['draft', 'submitted'])),
                'processed_returns': len(returns.filtered(lambda r: r.state in ['processed', 'completed'])),
            },
            'kpi': {
                'avg_processing_time': self._calculate_avg_processing_time(),
                'delivery_success_rate': self._calculate_delivery_success_rate(),
                'return_rate': self._calculate_return_rate(),
            }
        }

    def _get_agents_performance(self, agents, month_start):
        """Get agents performance data"""
        performance = []
        for agent in agents:
            sales_orders = self.env['sale.order'].search([
                ('honey_agent_id', '=', agent.id),
                ('date_order', '>=', month_start),
                ('state', 'in', ['sale', 'done'])
            ])
            
            performance.append({
                'agent_name': agent.name,
                'sales_amount': sum(sales_orders.mapped('amount_total')),
                'orders_count': len(sales_orders),
                'target_achievement': agent.target_achievement,
            })
        
        return sorted(performance, key=lambda x: x['sales_amount'], reverse=True)

    def _get_last_month_commissions(self, agent_id):
        """Get last month commissions for agent"""
        last_month = fields.Date.today().replace(day=1) - fields.timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        
        commissions = self.env['honey.commission'].search([
            ('agent_id', '=', agent_id),
            ('date', '>=', last_month_start),
            ('date', '<=', last_month),
            ('state', 'in', ['confirmed', 'paid'])
        ])
        
        return sum(commissions.mapped('amount'))

    def _get_expected_commissions(self, agent_id):
        """Get expected commissions for agent"""
        pending_orders = self.env['sale.order'].search([
            ('honey_agent_id', '=', agent_id),
            ('state', 'in', ['sale', 'done']),
            ('qr_confirmed', '=', False)
        ])
        
        expected = 0
        for order in pending_orders:
            if order.honey_agent_id:
                commission_rate = order.honey_agent_id.commission_rate / 100
                expected += order.amount_total * commission_rate
        
        return expected

    def _calculate_production_efficiency(self):
        """Calculate production efficiency"""
        # This would calculate based on planned vs actual production
        return 85.0  # Placeholder

    def _calculate_avg_processing_time(self):
        """Calculate average processing time"""
        # This would calculate based on order to shipment time
        return 24.0  # Placeholder in hours

    def _calculate_delivery_success_rate(self):
        """Calculate delivery success rate"""
        # This would calculate based on successful deliveries
        return 95.0  # Placeholder percentage

    def _calculate_return_rate(self):
        """Calculate return rate"""
        # This would calculate based on returns vs total shipments
        return 2.5  # Placeholder percentage
