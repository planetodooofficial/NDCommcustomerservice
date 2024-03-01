from odoo import models, api, fields, _


class InheritProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'mail.thread', 'mail.activity.mixin', 'image.mixin']

    category_name = fields.Char(string='Category Name', tracking=True)
    category_description = fields.Char(string='Product Category Description', tracking=True)
    indian_hsn = fields.Many2one('hsn.master', string='Indian HSN', tracking=True)
    digit_heading_4 = fields.Char(related='indian_hsn.digit_heading_4')
    digit_heading_6 = fields.Char(related='indian_hsn.digit_heading_6')
    digit_heading_8 = fields.Char(related='indian_hsn.digit_heading_8')
    remarks = fields.Char(string='Remarks', tracking=True)

    #  Notification Tab
    basic_customs_no = fields.Many2one('notification.master', tracking=True)
    basic_customs_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    basic_customs_remark = fields.Char(related='basic_customs_no.notification_remarks')
    basic_customs_sr_remark = fields.Char(related='basic_customs_sr_no.notification_serial_remarks')
    basic_customs_no_tags = fields.Many2many(related='basic_customs_no.notification_tags')
    so_number = fields.Char()

    @api.onchange('basic_customs_no')
    def serial_number(self):
        for rec in self:
            rec.so_number = rec.basic_customs_no.notification_number


    social_welfare_no = fields.Many2one('notification.master', tracking=True)
    social_welfare_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    social_welfare_remark = fields.Char(related='social_welfare_no.notification_remarks')
    social_welfare_sr_remark = fields.Char(related='social_welfare_sr_no.notification_serial_remarks')
    social_welfare_no_tags = fields.Many2many(related='social_welfare_no.notification_tags')
    social_so_number = fields.Char()

    @api.onchange('social_welfare_no')
    def social_serial_number(self):
        for rec in self:
            rec.social_so_number = rec.social_welfare_no.notification_number

    health_cess_no = fields.Many2one('notification.master', tracking=True)
    health_cess_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    health_cess_remark = fields.Char(related='health_cess_no.notification_remarks')
    health_cess_sr_remark = fields.Char(related='health_cess_sr_no.notification_serial_remarks')
    health_cess_no_tags = fields.Many2many(related='health_cess_no.notification_tags')
    health_so_number = fields.Char()

    @api.onchange('health_cess_no')
    def health_serial_number(self):
        for rec in self:
            rec.health_so_number = rec.health_cess_no.notification_number

    aidc_no = fields.Many2one('notification.master', tracking=True)
    aidc_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    aidc_remark = fields.Char(related='aidc_no.notification_remarks')
    aidc_sr_remark = fields.Char(related='aidc_sr_no.notification_serial_remarks')
    aidc_no_tags = fields.Many2many(related='aidc_no.notification_tags')
    aidc_so_number = fields.Char()

    @api.onchange('aidc_no')
    def aidc_serial_number(self):
        for rec in self:
            rec.aidc_so_number = rec.aidc_no.notification_number

    excise_no = fields.Many2one('notification.master', tracking=True)
    excise_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    excise_remark = fields.Char(related='excise_no.notification_remarks')
    excise_sr_remark = fields.Char(related='excise_sr_no.notification_serial_remarks')
    excise_no_tags = fields.Many2many(related='excise_no.notification_tags')
    excise_so_number = fields.Char()

    @api.onchange('excise_no')
    def excise_serial_number(self):
        for rec in self:
            rec.excise_so_number = rec.excise_no.notification_number

    road_infra_no = fields.Many2one('notification.master', tracking=True)
    road_infra_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    road_infra_remark = fields.Char(related='road_infra_no.notification_remarks')
    road_infra_sr_remark = fields.Char(related='road_infra_sr_no.notification_serial_remarks')
    road_infra_no_tags = fields.Many2many(related='road_infra_no.notification_tags')
    road_so_number = fields.Char()

    @api.onchange('road_infra_no')
    def road_serial_number(self):
        for rec in self:
            rec.road_so_number = rec.road_infra_no.notification_number

    compensation_no = fields.Many2one('notification.master', tracking=True)
    compensation_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    compensation_remark = fields.Char(related='compensation_no.notification_remarks')
    compensation_sr_remark = fields.Char(related='compensation_sr_no.notification_serial_remarks')
    compensation_no_tags = fields.Many2many(related='compensation_no.notification_tags')
    compensation_so_number = fields.Char()

    @api.onchange('compensation_no')
    def compensation_serial_number(self):
        for rec in self:
            rec.compensation_so_number = rec.compensation_no.notification_number

    igst_no = fields.Many2one('notification.master', tracking=True)
    igst_sr_no = fields.Many2one('notification.serial.master', tracking=True)
    igst_remark = fields.Char(related='igst_no.notification_remarks')
    igst_sr_remark = fields.Char(related='igst_sr_no.notification_serial_remarks')
    igst_no_tags = fields.Many2many(related='igst_no.notification_tags')
    igst_so_number = fields.Char()

    @api.onchange('igst_no')
    def igst_serial_number(self):
        for rec in self:
            rec.igst_so_number = rec.igst_no.notification_number

    # non tariff barriers(tab)
    bis = fields.Boolean(string='BIS', tracking=True)
    wpc = fields.Boolean(string='WPC', tracking=True)
    aerb = fields.Boolean(string='AERB', tracking=True)
    fssai = fields.Boolean(string='FSSAI', tracking=True)
    cdsco = fields.Boolean(string='CDSCO', tracking=True)
    pq = fields.Boolean(string='P&Q', tracking=True)
    apeda = fields.Boolean(string='APEDA', tracking=True)
    medical_device = fields.Boolean(string='Medical Device', tracking=True)
    pims_applicable = fields.Boolean(string='PIMS applicable', tracking=True)
    chims_applicable = fields.Boolean(string='CHIMS applicable', tracking=True)
    sims_applicable = fields.Boolean(string='SIMS applicable', tracking=True)

    bis_remark = fields.Char(tracking=True)
    wpc_remark = fields.Char(tracking=True)
    aerb_remark = fields.Char(tracking=True)
    fssai_remark = fields.Char(tracking=True)
    cdsco_remark = fields.Char(tracking=True)
    pq_remark = fields.Char(tracking=True)
    apeda_remark = fields.Char(tracking=True)
    medical_device_remark = fields.Char(tracking=True)
    pims_applicable_remark = fields.Char(tracking=True)
    chims_applicable_remark = fields.Char(tracking=True)
    sims_applicable_remark = fields.Char(tracking=True)

    #     CCR from ICEGATE (Part of Non Tariff Barriers tab)
    ccr_remark = fields.Char(related='indian_hsn.ccr_notes', string='Remark', tracking=True, readonly=True)
    ccr_date = fields.Date(string='Date', tracking=True)
    ccr_link = fields.Char(string='CCR link', tracking=True)

    #     Attachments tab - Product level

    product_images = fields.Binary(string='Product Images')
    catalog = fields.Binary(string='Catalog')
    other = fields.Binary(string='Other')

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         if not self.env.context.get('hide_code'):
    #             name = '[' + rec.reference + ']' + rec.name
    #         else:
    #             name = rec.name
    #         result.append((rec.id, name))
    #     return result
