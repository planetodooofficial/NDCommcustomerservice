from lxml import etree
from odoo.tools.misc import formatLang, format_date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

INV_LINES_PER_STUB = 9

class PaymentInherit(models.Model):
    _inherit = 'account.payment'

    partial_lines = fields.One2many('partial.line', 'payment_id')
    pending_amt = fields.Float(compute="compute_pending_amt")
    advance_order_ids = fields.One2many('advance.payment.orders','payment_id',string="Advance Orders")
    is_advance = fields.Boolean(default=False, string="Advance?")
    # check_number = fields.Char(
    #     string="Check Number",
    #     store=True,
    #     readonly=False,
    #     copy=False,
    #     compute='_compute_check_number',
    #     inverse='_inverse_check_number',
    #     help="The selected journal is configured to print check numbers. If your pre-printed check paper already has numbers "
    #          "or if the current numbering is wrong, you can change it in the journal configuration page.",
    # )

    # rangesrc_id = fields.Many2one('cheque.range.line', domain="[('accjournal_id', '=', journal_id)]", string='Range', readonly=False, compute='rangevalidation', store=True)
    remarks = fields.Char(string='Remarks')
    # Field used for domain in button
    payment_method_name = fields.Char('Payment Method Name', related='payment_method_id.name')

    # check_amount_in_words = fields.Char(compute='amt_in_words', string='Amount in Words')
    beneficiary_name = fields.Char('Beneficiary Name', related='partner_id.name', store=True)
    acc_payee = fields.Boolean('Account Payee')
    so_order_id = fields.Many2one('sale.order', string="Order")
    po_order_id = fields.Many2one('purchase.order', string="Order")
    term_id = fields.Many2one('payments.by.term')
    to_check = fields.Boolean("To Check",tracking=True,copy=False,default=False)
    is_checked = fields.Boolean("Checked",tracking=True,copy=False,default=False)
    checker_id = fields.Many2one('res.users',"Checker")

    def send_for_checking(self):

        return {
            'name': _('Send for Checker'),
            'res_model': 'send.checker',
            'view_mode': 'form',
            'target': 'new',
            'payment_id': self.id,
            'type': 'ir.actions.act_window'
        }

    def button_set_checked(self):
        for payment in self:
            payment.to_check = False
            payment.is_checked = True

    def action_draft(self):
        res = super(PaymentInherit, self).action_draft()
        for payment in self:
            payment.to_check = False
            payment.is_checked = False
        return res

    def custom_action_post(self):
        self.action_post()

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super(PaymentInherit, self)._get_view(view_id, view_type, **options)
        if view_type == 'form':
            for node in arch.xpath("//button[@name='action_post']"):
                if self.env.user.has_group('po_accounting_v16.group_payments_position_manager'):
                    node.set('invisible', 'False')
                else:
                    node.set('attrs', "{'invisible': ['|',('is_checked','!=',True),('state','!=','draft')]}")
        return arch, view

    @api.onchange('is_advance', 'partner_id')
    def unlink_advances(self):
        self.advance_order_ids.unlink()

    @api.depends('partial_lines.amount')
    def compute_pending_amt(self):
        amount = self.amount - sum(self.partial_lines.mapped('amount'))
        if amount < 0:
            raise ValidationError('You are trying to reconcile more than the payment amount')
        self.pending_amt = amount

    def action_reconcile_lines(self):
        acc_type = 'asset_receivable' if self.payment_type == 'inbound' else 'liability_payable'
        payment_move_line = self.move_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)[0]
        for rec in self.partial_lines.filtered(lambda x: not x.reconciled_id and x.amount > 0):
            data = {'amount': rec.amount,
                    'credit_amount_currency': rec.amount,
                    'debit_amount_currency': rec.amount,
                    'max_date': datetime.now().date()}
            move_line_id = rec.move_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)[0]
            data['debit_move_id'], data['credit_move_id'] = (move_line_id.id, payment_move_line.id) \
                if rec.move_id.move_type == 'out_invoice' else (payment_move_line.id, move_line_id.id)
            reconciled_id = self.env['account.partial.reconcile'].create(data)
            rec.reconciled_id = reconciled_id.id
        payment_move_line._compute_amount_residual()

class AdvanceOrder(models.Model):
    _name = 'advance.payment.orders'

    sale_id = fields.Many2one('sale.order', domain=[('state', '=', 'sale')])
    purchase_id = fields.Many2one('purchase.order', domain=[('state', '=', 'purchase')])
    partner_id = fields.Many2one('res.partner')
    payment_terms = fields.Many2one('account.payment.term', readonly=True)
    order_amount = fields.Float(readonly=True)
    advance_amount = fields.Float()
    payment_id = fields.Many2one('account.payment', auto_join=True)


    # @api.onchange('sale_id')
    # def set_sales_field(self):
    #     self.payment_terms = self.sale_id.payment_term_id.id
    #     self.order_amount = self.sale_id.amount_total
    #
    # @api.onchange('purchase_id')
    # def set_purchase_field(self):
    #     self.payment_terms = self.purchase_id.payment_term_id.id
    #     self.order_amount = self.purchase_id.amount_total
    #
    # @api.onchange('advance_amount')
    # def validate_advance_amount(self):
    #     if self.advance_amount > self.order_amount:
    #         raise ValidationError('Advance Amount cannot be greater than the Order Amount.')
