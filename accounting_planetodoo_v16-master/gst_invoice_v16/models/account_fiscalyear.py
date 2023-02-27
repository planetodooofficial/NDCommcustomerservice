# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import time
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError
from odoo.osv import expression


class AccountFiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    _order = "date_start, id"

    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
        default=lambda self: self.env.company)
    date_start = fields.Date('Start Date', required=True,
        default=lambda *a: time.strftime('%Y-%m-01 %H:59:%S'))
    date_stop = fields.Date('End Date', required=True,
        default=lambda *a: time.strftime('%Y-12-31 %H:59:%S'))
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')

    @api.constrains('date_start', 'date_stop')
    def _check_duration(self):
        if self.date_stop < self.date_start:
            raise UserError(_('Error!\nThe start date of a fiscal year must precede its end date.'))

    def create_period3(self):
        return self.create_period(3)

    def create_period1(self):
        return self.create_period(1)

    def create_period(self, interval=1):
        period_obj = self.env['account.period']
        for fy in self:
            date_start = fy.date_start
            period_obj.create({
                'name': "%s %s" % (_('Opening Period'), date_start.strftime('%Y')),
                'code': date_start.strftime('00/%Y'),
                'date_start': date_start,
                'date_stop': date_start,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while date_start < fy.date_stop:
                date_end = date_start + relativedelta(months=interval, days=-1)
                if date_end > fy.date_stop:
                    date_end = fy.date_stop
                period_obj.create({
                    'name': date_start.strftime('%b-%Y'),
                    'code': date_start.strftime('%m/%Y'),
                    'date_start': date_start,
                    'date_stop': date_end,
                    'fiscalyear_id': fy.id,
                })
                date_start = date_start + relativedelta(months=interval)
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        objs = self.search(expression.AND([domain, args]), limit=limit)
        return objs.name_get()


class AccountPeriod(models.Model):
    _name = "account.period"
    _description = "Account period"
    _order = "date_start, special desc"

    @api.depends('date_stop')
    def _get_special(self):
        from_date = fields.Date.today() - timedelta(days=30)
        for obj in self:
            if obj.date_stop and obj.date_stop < from_date:
                obj.special = True
            else:
                obj.special = False

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period',
                             help="These periods can overlap.", compute='_get_special')
    date_start = fields.Date('Start of Period', required=True)
    date_stop = fields.Date('End of Period', required=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 related='fiscalyear_id.company_id', store=True, readonly=True)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'The name of the period must be unique per company!'),
    ]

    @api.constrains('date_start', 'date_stop')
    def _check_duration_and_year_limit(self):
        if self.date_stop < self.date_start:
            raise UserError(
                _('Error!\nThe duration of the Period(s) is/are invalid.'))
        for obj_period in self:
            if obj_period.special:
                continue
            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                raise UserError(
                    _('Error!\nThe duration of the Period(s) is/are invalid.'))
            pidObjs = self.search([('date_stop', '>=', obj_period.date_start),
                                   ('date_start', '<=', obj_period.date_stop),
                                   ('id', '<>', obj_period.id)])
            for period in pidObjs:
                if period.special:
                    continue
                pastMonth = fields.Date.today() + relativedelta(months=-1)
                dateStop = period.date_stop
                if dateStop > pastMonth and dateStop < fields.Date.today():
                    continue
                if period.fiscalyear_id.company_id.id == obj_period.fiscalyear_id.company_id.id:
                    raise UserError(_('Error!\nThe period is invalid. ' \
                        'Either some periods are overlapping ' \
                        'or the period\'s dates are not matching the scope of the fiscal year.'))

    @api.returns('self')
    def next(self, period, step):
        ids = self.search([('date_start', '>', period.date_start)])
        if len(ids) >= step:
            return ids[step - 1]
        return False

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        objs = self.search(expression.AND([domain, args]), limit=limit)
        return objs.name_get()

    def write(self, vals):
        if 'company_id' in vals:
            move_lines = self.env['account.move.line'].search([
                ('period_id', 'in', self.ids)
            ])
            if move_lines:
                raise UserError(
                    _('Warning!'),
                    _('This journal already contains items for this period, therefore you cannot modify its company field.'))
        return super(AccountPeriod, self).write(vals)
