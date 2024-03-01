from odoo import models, api, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class NotificationTags(models.Model):
    _name = 'notification.tags'
    _rec_name = 'name'

    name = fields.Char('Name')
    color = fields.Integer(string='Color')

class NotificationMaster(models.Model):
    _name = 'notification.master'
    _rec_name = 'notification_uid'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    notification_uid = fields.Char(copy=False, readonly=True, default=lambda self: _('New'))
    notification_stage = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft', tracking=True)
    notification_description = fields.Char(string='Notification Description', tracking=True)
    notification_tags = fields.Many2many('notification.tags',string='Notification Tags')
    notification_number = fields.Char(string='Notification Number', required=True, tracking=True)
    notification_date = fields.Date(string='Notification Date', tracking=True)
    notification_main_text = fields.Char(string='Notification Main Text', tracking=True)
    notification_remarks = fields.Char(string='Notification Remarks', tracking=True)
    notification_validity = fields.Date(string='Notification Validity', tracking=True)
    is_edit = fields.Boolean(default=False)

    def name_get(self):
        result = []
        for rec in self:
            if not self.env.context.get('hide_code'):
                name = rec.notification_uid
            else:
                name = rec.notification_number
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get('notification_uid', _('New')) == _('New'):
            vals['notification_uid'] = self.env['ir.sequence'].next_by_code('notification.master') or _('New')
        res = super(NotificationMaster, self).create(vals)
        return res

    def validate_notification(self):
        self.notification_stage = 'confirm'
        self.is_edit = True

    def cancel_notification(self):
        self.notification_stage = 'draft'

    def edit_only_button(self):
        self.is_edit = False

    def readonly_button(self):
        self.is_edit = True

    @api.constrains('notification_number')
    def unique_notification_number(self):
        search_notification_number = self.env['notification.master'].search(
            [('notification_number', '=', self.notification_number), ('id', '!=', self.id)])
        if search_notification_number:
            raise ValidationError(_('Notification Number Already Exist'))


class NotificationSerialMaster(models.Model):
    _name = 'notification.serial.master'
    _rec_name = 'notification_serial_no'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    notification_serial_stage = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft',
                                                 tracking=True)
    serial_uid = fields.Many2one('notification.master', string='Notification Serial Uid', required=True, tracking=True)
    notification_serial_description = fields.Char(string='Notification Description', tracking=True,
                                                  related='serial_uid.notification_description')
    notification_serial_number = fields.Char(string='Notification Number', required=True, tracking=True,
                                             related='serial_uid.notification_number')
    notification_serial_date = fields.Date(string='Notification Date', tracking=True,
                                           related='serial_uid.notification_date')
    notification_serial_main_text = fields.Char(string='Notification Main Text', tracking=True,
                                                related='serial_uid.notification_main_text')
    notification_serial_remarks = fields.Char(string='Remarks', tracking=True,)
    notification_serial_no = fields.Char(string='Serial No', tracking=True)
    notification_serial_no_text = fields.Char(string='Serial No Text', tracking=True)
    affected_hsn = fields.Text(string="Affected HSN")

    def validate_serial_notification(self):
        self.notification_serial_stage = 'confirm'

    @api.constrains('serial_uid')
    def serial_number_unique_code(self):
        search_serial_no = self.env['notification.serial.master'].search([('serial_uid', '=', self.serial_uid.id ), ('notification_serial_no', '=', self.notification_serial_no), ('id', '!=', self.id)])
        if search_serial_no:
            raise ValidationError(_('Serial Number Already Exist'))



