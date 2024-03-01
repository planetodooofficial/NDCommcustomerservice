from odoo import models, api, fields, _

class PerformanceDimension(models.Model):
    _name = "performance.dimension"

    be_no = fields.Char(string='BE No.', readonly=True)
    hawb_no = fields.Char(string='HAWB No', readonly=True)
    mawb_no = fields.Char(string='MAWB No.', readonly=True)
    cb_job_number = fields.Char(string= 'CB Job number', readonly=True)
    linked_cb = fields.Char(string='Linked CB', readonly=True)
    business_tags = fields.Char(string='Business tags', readonly=True)
    be_date = fields.Char(string='BE Date', readonly=True)
    hawb_date = fields.Char(string='HAWB Date', readonly=True)
    mawb_date = fields.Char(string='MAWB Date', readonly=True)
    client_ref_number = fields.Char(string='Client Ref Number', readonly=True)
    linked_ff = fields.Char(string='Linked FF', readonly=True)
    sales_team = fields.Char(string='Sales team', readonly=True)
    linked_tpt = fields.Char(string='Linked TPT', readonly=True)

    pre_alert_received = fields.Char(string='Pre-alert Received(Complete)')
    checklist_prepared = fields.Char(string='Checklist Prepared')
    checklist_approved = fields.Char(string='Checklist Approved')
    be_filed = fields.Char(string='BE Filed', readonly=True)
    be_receipt = fields.Char(string='BE Receipt')
    assessed = fields.Char(string='Assessed', readonly=True)
    duty_paid = fields.Char(string='Duty Paid', readonly=True)
    igm_date = fields.Char(string='IGM Date', readonly=True)
    inw_date = fields.Char(string='INW Date', readonly=True)
    registration_completed = fields.Char(string='Registration Completed')
    do_collected = fields.Char(string='DO Collected')
    examinated = fields.Char(string='Examinated', readonly=True)
    out_of_charge = fields.Char(string='Out of charge', readonly=True)
    delivery = fields.Char(string='Delivery')

    file_sent_for_billing = fields.Char(string='File sent for billing')
    bill_dispatched = fields.Char(string='Bill dispatched')
    pickup_date = fields.Char(string='Pick-up Date')

    tat1 = fields.Integer(string='TAT1', readonly=True)
