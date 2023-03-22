from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import datetime


# Creating Master Reason
class ReasonReasons(models.Model):
    _name = 'reason.reasons'
    _description = "Master Description"

    name = fields.Char(string="Reason Name")

class CustomerService(models.Model):
    _inherit = "sale.order"

    cancellation = fields.Boolean(string="Cancellation Requested", readonly=True)
    canc_req_datetime = fields.Datetime(string="Cancellation Request Datetime")
    rto_req = fields.Boolean(string="RTO Requested", readonly=True)
    rto_req_datetime = fields.Datetime(string="RTO Requested Datetime")
    return_request = fields.Boolean(string="Return Requested", readonly=True)
    return_request_datetime = fields.Datetime(string="Return Requested Datetime")
    refund_request_check = fields.Boolean(string="Refund Requested", readonly=True)
    refund_request_datetime = fields.Datetime(string="Refund Requested Datetime")
    viniculam_status_id = fields.Many2one('sale.order', 'Sales Connector')
    vinculum_status = fields.Selection([('Confirmed', 'Confirmed'),
                                        ('Allocated', 'Allocated'),
                                        ('Cancelled', 'Cancelled'),
                                        ('Closed', 'Closed'),
                                        ('Delivered', 'Delivered'),
                                        ('Delivery created', 'Delivery Created'),
                                        ('Packed', 'Packed'),
                                        ('Part Allocated', 'Part Allocated'),
                                        ('Part Picked', 'Part Picked'),
                                        ('Partially Shipped', 'Partially Shipped'),
                                        ('Pending', 'Pending'),
                                        ('Pick complete', 'Pick Complete'),
                                        ('Shipped & Returned', 'Shipped & Returned'),
                                        ('Shipped complete', 'Shipped Complete'),
                                        ('In process', 'In process'),
                                        ],
                                       copy=False)
    custom_state = fields.Selection(
        [('cancellation_requested', 'Cancellation Requested'), ('rto_requested', 'RTO Requested'),
         ('rvp_requested', 'RVP Requested'), ('returned', 'Returned'),
         ('refund_requested', 'Refund Requested'),('order_cancel','Order cancelled') ,('audited', 'Audited'), ('refunded', 'Refunded')],
        string='Status', store=True, readonly=True, tracking=True, copy=False)

    approval_status = fields.Selection(
        [('draft', 'Draft'), ('waiting_for_approval', 'Waiting for Approval'), ('approved', 'Approved'),('reject','Rejected')], readonly=True, tracking=True, copy=False)

    claim_status = fields.Selection(
        [('not_required', 'Not Required'), ('insurance', 'Insurance'),
         ('damage_claim_with_courier', 'Damage Claim with Courier'), ('warehouse', 'Warehouse')], readonly=True, tracking=True, copy=False)

    state = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('sale', "Sales Order"),
            ('done', "Locked"),
            ('delivered', "Delivered"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    @api.depends('vinculum_status')
    def _check_viniculam_status(self):
        if self.vinculum_status == "Shipped & Returned":
            self.custom_state = 'returned'
        else:
            self.custom_state = False

    def request_cancellation_button(self):
        if len(self.order_line) > 1:
            raise ValidationError('You cannot cancel if line ids greater than 1')
        elif self.order_line.product_uom_qty > 1:
            raise ValidationError("Cannot cancel due to multiple quantities")
        else:
            self.rto_req = False
            self.return_request = False
            self.canc_req_datetime = datetime.today()
            self.custom_state = "cancellation_requested"
            self.approval_status = "waiting_for_approval"

    def approve_cancellation(self):
        self.cancellation = True
        self.state = "cancel"
        self.custom_state = "order_cancel"
        self.approval_status = "approved"

    def rto_button(self):
        self.rto_req = True
        self.return_request = False
        self.rto_req_datetime = datetime.today()
        self.custom_state = "rto_requested"

    def return_button(self):
        self.return_request = True
        self.return_request_datetime = datetime.today()

    def approve_funds(self):
        self.custom_state = "audited"
        self.approval_status = "approved"

    def reject_funds(self):
        return {
            'name': 'Reject Reason',
            'res_model': 'reasons.wiz',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
        }

    def send_approved(self):
        pass

    def vaniculum_button(self):
        pass

    def reverse_pick(self):
        pass

    def marked_delivered(self):
        self.state = "delivered"

    def refund_request(self):
        self.custom_state = "refund_requested"
        self.approval_status = "waiting_for_approval"
        self.refund_request_check = True
        self.refund_request_datetime = datetime.today()

    def mark_refunded(self):
        self.custom_state = "refunded"


class DelCarrier(models.Model):
    _inherit = 'delivery.carrier'

    spoc = fields.Char('Email')
