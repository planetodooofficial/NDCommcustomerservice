from odoo import models, fields, api, _
from datetime import date, timedelta
import json
from lxml import etree

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    payments_by_terms = fields.One2many('po.payments.term', 'po_id')
    to_check = fields.Boolean("To Check",tracking=True,copy=False,default=False)
    is_checked = fields.Boolean("Checked",tracking=True,copy=False,default=False)

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super(PurchaseOrderInherit, self)._get_view(view_id, view_type, **options)
        if view_type == 'form':
            for node in arch.xpath("//button[@id='draft_confirm']"):
                if self.env.user.has_group('po_accounting_v16.group_purchase_position_manager'):
                    node.set('attrs',"{'invisible': [('state','!=','draft')]}")
                else:
                    node.set('attrs',"{'invisible': ['|',('is_checked','!=',True),('state','!=','draft')]}")

            for node in arch.xpath("//button[@id='bid_confirm']"):
                if self.env.user.has_group('po_accounting_v16.group_purchase_position_manager'):
                    node.set('attrs',"{'invisible': [('state','!=','sent')]}")
                else:
                    node.set('attrs',"{'invisible': ['|',('is_checked','!=',True),('state','!=','sent')]}")

        return arch, view

    def send_for_checking(self):
        return {
            'name': _('Send for Checker'),
            'res_model': 'send.checker',
            'view_mode': 'form',
            'target': 'new',
            'po_id': self.id,
            'type': 'ir.actions.act_window'
        }

    def button_set_checked(self):
        for po in self:
            po.to_check = False
            po.is_checked = True

    def get_fiscal_position(self):
        state = 'inter' if self.partner_id.state_id.id != self.l10n_in_journal_id.l10n_in_gstin_partner_id.state_id.id else 'intra'
        domain = [('state', '=', state), ('gstin_unit', '=', self.l10n_in_journal_id.l10n_in_gstin_partner_id.id)]
        return self.env['account.fiscal.position'].search(domain, limit=1).id or False

    # This method helps to set Fiscal Position and taxes in purchase.order.line according to fiscal position
    @api.onchange('l10n_in_journal_id', 'partner_id')
    def set_order_line(self):
        self.update({'fiscal_position_id': False})
        if self.l10n_in_journal_id and self.partner_id:
            self.update({'fiscal_position_id': self.get_fiscal_position()})
        for line in self.order_line:
            taxes = line._get_computed_taxes()
            taxes = line.order_id.fiscal_position_id.map_tax(taxes)
            line.taxes_id = taxes and taxes.ids or False

    @api.onchange('payment_term_id')
    def compute_payments_by_terms(self):
        for order in self:
            order.payments_by_terms = False
            values = []
            if order.payment_term_id:
                payment_terms = order.payment_term_id._compute_terms(
                    date_ref=order.date_order or fields.Date.today(),
                    currency=order.currency_id or order.company_id.currency_id,
                    tax_amount_currency=order.amount_tax,
                    tax_amount=order.amount_tax,
                    untaxed_amount_currency=order.amount_untaxed,
                    untaxed_amount=order.amount_untaxed,
                    company=order.company_id,
                    sign=1
                )
                percent = 0.0
                for term in payment_terms:
                    percent += term['percent']
                    if term['value'] == 'balance':
                        term['percent'] = 100 - percent
                    values.append((0, 0,
                                   {
                                       'name': term['desc'],
                                       'percent': term['percent'] or 0.0,
                                       'due_date': term['date'],
                                       'value': term['company_amount'],
                                       'po_id': order.id
                                   }))

                order.payments_by_terms = values



class POPaymentsByTerms(models.Model):
    _name = 'po.payments.term'
    _order = "sequence,id"

    name = fields.Char("Description")
    sequence = fields.Integer(default=10)
    po_id = fields.Many2one('purchase.order')
    value = fields.Float("Amount")
    percent = fields.Float("Amount in %")
    due_date = fields.Date("Due Date")
    # is_payment_received = fields.Boolean("Payment Received ?")
    payment_recv_date = fields.Date("Payment Received Date")
    amount_received = fields.Float("Amount Received")
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', readonly=True,
                                  required=True)

    def open_create_payment_wizard(self):
        res_id = self.env['payment.wiz'].sudo().create({
            'term_id': self.id,
            'po_order_id': self.po_id.id,
            'amount': self.value - self.amount_received,
            'payment_date': date.today(),
            'memo': "Advance Payment for" + str(self.po_id.name)
        })
        return {
            'name': _('Register Payment'),
            'res_model': 'payment.wiz',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window'
        }

    def view_payments(self):
        payments = self.env['account.payment'].sudo().search([('term_id', '=', self.id)])
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('term_id', '=', self.id)],
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id
            })
        return action

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    # This Function helps us to get Taxes for setting in line items on change of Partner, Journal
    # First it will take tax from product if in product tax is not set then from journal->Account and Tax and then
    # from Company
    # This function will run from sale.order when user will change Partner or Journal
    hsn_id = fields.Many2one('hsn.code', string=' HSN / SAC Code')

    #onchange for hsn

    @api.onchange('product_id')
    def hsn_purchase(self):
        hsn = self.product_id.purchase_hsn
        self.hsn_id = hsn.id

    def _get_computed_taxes(self):
        self.ensure_one()
        tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.order_id.company_id) or \
                  self.order_id.l10n_in_journal_id.default_account_id.tax_ids or self.order_id.company_id.account_purchase_tax_id
        return tax_ids

    # Adding Purchase HSN Code in Bills

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLineInherit, self)._prepare_account_move_line(move)
        hsn = self.product_id.purchase_hsn
        res.update({'hsn_id': hsn.id})
        return res
