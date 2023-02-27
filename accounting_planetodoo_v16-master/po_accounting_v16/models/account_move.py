from odoo import fields, models, api,_
from datetime import datetime
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
import json
from lxml import etree
from datetime import datetime
from odoo.tools import (
    float_compare,
    format_date,
    formatLang,
    get_lang,)
from collections import defaultdict

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_default_currency(self):
        ''' Get the default currency from either the journal, either the default journal's company. '''
        journal = self._search_default_journal()
        return journal and (journal.currency_id or journal.company_id.currency_id) or False

    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
                                  states={'draft': [('readonly', False)]},
                                  string='Currency',
                                  default=_get_default_currency)
    partial_lines = fields.One2many('partial.line', 'entry_id')
    pending_amt = fields.Float(compute="compute_pending_amt")
    custom_payment_type = fields.Selection([('inbound', 'Inbound'), ('outbound', 'outbound')])
    taxes_id = fields.Many2one('account.tax', copy=False, string="Applicable TDS")
    deductee_type_id = fields.Many2one(ondelete='restrict', related='partner_id.deductee_type_id')
    total_invoiced = fields.Float(compute="compute_total_invoice")
    adv_pay_amt = fields.Float(string="Amount")
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
                                             readonly=False, store=True, copy=False,
                                             compute='_compute_payment_method_line_id',
                                             domain="[('id', 'in', available_payment_method_line_ids)]",
                                             help="Manual: Pay or Get paid by any method outside of Odoo.\n"
                                                  "Payment Acquirers: Each payment acquirer has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
                                                  "Check: Pay bills by check and print it from Odoo.\n"
                                                  "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
                                                  "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
                                                  "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')

    is_checked = fields.Boolean("Checked",default=False,tracking=True,copy=False)
    to_check = fields.Boolean(
        string='To Check',
        tracking=True,copy=False,
        help="If this checkbox is ticked, it means that the user was not sure of all the related "
             "information at the time of the creation of the move and that the move needs to be "
             "checked again.",
    )
    checker_id = fields.Many2one('res.users',"Checker")

    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_company(self.journal_id.company_id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=',
                     'receivable' if self.move_type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date,
                                                                  currency=self.company_id.currency_id)
                if self.currency_id == self.company_id.currency_id:
                    # Single-currency.
                    return [(b[0], b[1], b[1], pt.label) for b, pt in
                            zip(to_compute, self.invoice_payment_term_id.line_ids)]  # Custom code here
                else:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                               currency=self.currency_id)
                    return [(b[0], b[1], ac[1], lb.label) for b, ac, lb in zip(to_compute, to_compute_currency)]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency, '')]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            # for date_maturity, balance, amount_currency,label, retention, advance  in to_compute:
            for date_maturity, balance, amount_currency, label in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'name': label,
                        # 'custom_label':label,  #added label
                        # 'retention': retention, #added retention
                        # 'advance': advance #added advance
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                        'account.move.line'].create
                    candidate = create_method({
                        'name': label or self.payment_reference or '',
                        # 'custom_label': label or self.payment_reference or '',  #added label
                        # 'retention': retention,  # added retention
                        # 'advance': advance,  # added advance
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,

                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.payment_reference = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity

    # Function to Compute Total Invoice for Current Financial Year
    def compute_total_invoice(self):
        fiscal_year = self.env['account.fiscal.year'].search([], limit=1)
        domain = [('partner_id', '=', self.partner_id.id), ('move_type', '=', self.move_type), ('state', '=', 'posted')]
        if fiscal_year:
            domain.extend((('invoice_date', '>=', fiscal_year.date_from), ('invoice_date', '<=', fiscal_year.date_to)))
        self.total_invoiced = sum(self.env['account.move'].search(domain).mapped('amount_total'))

    # Function to get Current year financial Invoices
    def get_current_financial_year_moves(self):
        fiscal_year = self.env['account.fiscal.year'].search([], limit=1)
        domain = [('partner_id', '=', self.partner_id.id), ('move_type', '=', self.move_type), ('state', '=', 'posted')]
        if fiscal_year:
            domain.extend((('invoice_date', '>=', fiscal_year.date_from), ('invoice_date', '<=', fiscal_year.date_to)))
        move_ids = self.env['account.move'].search(domain)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', move_ids.ids)]
        }

    @api.onchange('taxes_id')
    def populate_in_line_items(self):
        if self.taxes_id:
            for line in self.invoice_line_ids:
                # line.update({'tax_ids': [(4, _id) for _id in self.taxes_ids.ids if _id not in line.tax_ids.ids]})
                line.update({'tax_ids': (4, self.taxes_id.id if self.taxes_id.id not in line.tax_ids.ids else False)})
        container = {'records': self}
        self._sync_dynamic_lines(container)

    def remove_del_taxes_ids(self, del_taxes):
        for line in self.invoice_line_ids:
            line.update({'tax_ids': [(3, tax) for tax in del_taxes]})
            line._onchange_mark_recompute_taxes()
        container = {'records': self}
        self._sync_dynamic_lines(container)

    # def write(self, values):
    #     if 'taxes_id' in values:
    #         del_taxes = set(self.taxes_id.id).difference(set(values.get('taxes_id')[0][2]))
    #         if del_taxes:
    #             self.remove_del_taxes_ids(del_taxes)
    #     return super(AccountMoveInherit, self).write(values)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(AccountMoveInherit, self).get_view(view_id, view_type, **options)
        if view_type == 'form':
            move_type = [("customer_rank", ">", 0)] if self._context.get('default_move_type') == "out_invoice" else [
                ("supplier_rank", ">", 0)]
            tds_tax = [('is_tds', '=', True), ('id', '=', self.partner_id.tds_tax_id.id)]
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('domain', f"{move_type}")
                res['arch'] = etree.tostring(doc)
        return res

    @api.depends('partial_lines.amount')
    def compute_pending_amt(self):
        amount = self.adv_pay_amt - sum(self.partial_lines.mapped('amount'))
        if amount < 0:
            raise ValidationError('You are trying to reconcile more than the payment amount')
        self.pending_amt = amount

    def _get_valid_liquidity_accounts(self):
        return (
            self.journal_id.default_account_id.id,
            self.payment_method_line_id.payment_account_id.id,
            self.journal_id.company_id.account_journal_payment_debit_account_id.id,
            self.journal_id.company_id.account_journal_payment_credit_account_id.id,
            self.journal_id.inbound_payment_method_line_ids.payment_account_id.id,
            self.journal_id.outbound_payment_method_line_ids.payment_account_id.id,
        )

    def _search_default_journal(self):
        res = super(AccountMoveInherit, self)._search_default_journal()
        if self._context.get('default_custom_payment_type'):
            return False
            # res = self.env['account.journal'].search([('type', '=', 'bank')])
        return res and res[0] or False

    @api.onchange('journal_id', 'payment_method_line_id', 'adv_pay_amt')
    def create_move_line(self):
        os_line = self.line_ids.filtered(lambda x: x.is_os_line)
        if self.custom_payment_type == 'inbound' and self.payment_method_line_id:
            account_id = self.payment_method_line_id.payment_account_id or self.journal_id.company_id.account_journal_payment_debit_account_id
            if not os_line:
                self.line_ids = [(0, 0, {'account_id': account_id.id, 'debit': self.adv_pay_amt, 'is_os_line': True,
                                         'partner_id': self.partner_id.id})]
            else:
                self.update(dict(line_ids=[(1, os_line.id, {'account_id': account_id.id,
                                                            'debit': self.adv_pay_amt,
                                                            'partner_id': self.partner_id.id})]))
        elif self.custom_payment_type == 'outbound' and self.payment_method_line_id:
            account_id = self.payment_method_line_id.payment_account_id or self.journal_id.company_id.account_journal_payment_credit_account_id
            if not os_line:
                self.line_ids = [(0, 0, {'account_id': account_id.id, 'credit': self.adv_pay_amt, 'is_os_line': True,
                                         'partner_id': self.partner_id.id})]
            else:
                self.update(dict(line_ids=[(1, os_line.id, {'account_id': account_id.id, 'credit': self.adv_pay_amt,
                                                            'partner_id': self.partner_id.id})]))

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(AccountMoveInherit, self).get_view(view_id,view_type, **options)
        if view_type == 'form' and self._context.get('default_custom_payment_type'):
            doc = etree.XML(res['arch'])
            domain = "[('type', '=', 'bank')]"
            for node in doc.xpath("//field[@name='journal_id']"):
                node.set('domain', domain)
                test = node.get("modifiers")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['domain'] = domain
                node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_fields' because it's a stored editable one.
        '''
        for pay in self:
            payment_type = pay.custom_payment_type
            available_payment_method_lines = pay.journal_id._get_available_payment_method_lines(payment_type)
            # Select the first available one by default.
            if pay.payment_method_line_id in available_payment_method_lines:
                pay.payment_method_line_id = pay.payment_method_line_id
            elif available_payment_method_lines:
                pay.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_line_id = False

    @api.depends('journal_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            payment_type = pay.custom_payment_type
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(payment_type)

    def action_reconcile_lines(self):
        if sum(self.partial_lines.filtered(lambda x: x.reconciled_id).mapped('amount')) == self.adv_pay_amt and \
                self.partial_lines.filtered(lambda x: not x.reconciled_id):
            raise ValidationError('You cannot reconcile more Invoices\Bills.')
        if sum(self.partial_lines.filtered(lambda x: x.reconciled_id).mapped('amount')) == self.adv_pay_amt:
            raise ValidationError('You have reconciled all the line items')
        if self.partial_lines.filtered(lambda x: x.payment_line.id not in self.line_ids.ids):
            raise ValidationError('Incorrect Payment Selected For Reconciliation.')
        acc_type = 'asset_receivable' if self.custom_payment_type == 'inbound' else 'liability_payable'
        for rec in self.partial_lines.filtered(lambda x: not x.reconciled_id and x.amount > 0):
            payment_move_line = rec.payment_line
            if abs(payment_move_line.amount_residual) < rec.amount:
                raise ValidationError(f'You are only allowed to Reconcile {abs(payment_move_line.amount_residual)} '
                                      f'{payment_move_line.currency_id.symbol} for {rec.move_id.name}')
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

    def validate_payment(self):
        if not self.partner_id:
            raise ValidationError("Partner is Mandatory")
        if sum(self.line_ids.mapped('debit')) != self.adv_pay_amt:
            raise ValidationError('Payment Amount and Sum of Line item should be same')
        if not self.line_ids.filtered(lambda x: x.account_id.id in self._get_valid_liquidity_accounts()):
            raise ValidationError('No Outstanding Account Found in Below Line Items')
        if not self.line_ids.filtered(lambda x: x.account_id.account_type in ('liability_payable', 'asset_receivable')):
            raise ValidationError('Payable/Receivable Account Not Found')

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        if self._context.get('default_custom_payment_type'):
            self.validate_payment()
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(AccountMoveInherit, self).fields_get(allfields, attributes)
        payment_type = self._context.get("default_custom_payment_type")
        if payment_type:
            if payment_type == 'inbound':
                domain = [('customer_rank', ">", 0)]
            elif payment_type == 'outbound':
                domain = [('supplier_rank', ">", 0)]
            res["partner_id"]["domain"] = domain
        return res

    # For hsn in invoice
    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        res = super(AccountMoveInherit, self)._onchange_quick_edit_line_ids()
        for line in self.invoice_line_ids:
            if line.product_id:
                move_type = line.move_id.move_type
                hsn_p = line.product_id.purchase_hsn.hsnsac_code
                hsn_s = line.product_id.sale_hsn.hsnsac_code
                search1 = line.env['hsn.code'].search([('hsnsac_code', '=', hsn_s)])
                search2 = line.env['hsn.code'].search([('hsnsac_code', '=', hsn_p)])
                if search1 or search2:
                    line.hsn_id = search2.id if move_type == 'in_invoice' else search1.id
        return res

    def send_for_checking(self):
        return {
            'name': _('Send for Checker'),
            'res_model': 'send.checker',
            'view_mode': 'form',
            'target': 'new',
            'move_id': self.id,
            'type': 'ir.actions.act_window'
        }

    def button_set_checked(self):
        for move in self:
            move.to_check = False
            move.is_checked = True

    def reject(self):
        for move in self:
            move.is_checked = False
            move.to_check = False

    def button_draft(self):
        res = super(AccountMoveInherit, self).button_draft()
        for move in self:
            move.is_checked = False
            move.to_check = False
        return res

    @api.depends('date', 'auto_post')
    def _compute_hide_post_button(self):
        for record in self:
            record.hide_post_button = (record.state != 'draft' \
                or record.auto_post != 'no') and record.date > fields.Date.today() or (record.is_checked == False or record.state != 'draft')
            if self.env.user.has_group('po_accounting_v16.group_account_position_manager') and (record.state == 'draft' and record.auto_post == 'no'):
                record.hide_post_button = False

    @api.onchange('partner_id','journal_id')
    def _onchange_partner_id(self):
        res = super(AccountMoveInherit, self)._onchange_partner_id()
        if self.partner_id.tds_tax_id:
            self.taxes_id = self.partner_id.tds_tax_id.id
        if self.partner_id and self.journal_id:
            if self.partner_id.state_id.id == self.journal_id.l10n_in_gstin_partner_id.state_id.id:
                fiscal_position = self.env['account.fiscal.position'].sudo().search([('state','=','intra'),('gstin_unit','=',self.journal_id.l10n_in_gstin_partner_id.id)],limit=1)
                self.fiscal_position_id = fiscal_position.id if fiscal_position else False
            else:
                fiscal_position = self.env['account.fiscal.position'].sudo().search([('state', '=', 'inter'),('gstin_unit','=',self.journal_id.l10n_in_gstin_partner_id.id)], limit=1)
                self.fiscal_position_id = fiscal_position.id if fiscal_position else False
            for line in self.invoice_line_ids:
                line.tax_ids = line._get_computed_taxes()
        return res

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if not self.env.su and not (self.env.user.has_group('account.group_account_invoice') or self.env.user.has_group('po_accounting_v16.group_account_checker') or self.env.user.has_group('po_accounting_v16.group_payments_checker')):
            raise AccessError(_("You don't have the access rights to post an invoice."))

        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if invoice.quick_edit_mode and invoice.quick_edit_total_amount and invoice.quick_edit_total_amount != invoice.amount_total:
                raise UserError(_(
                    "The current total is %s but the expected total is %s. In order to post the invoice/bill, "
                    "you can adjust its lines or the expected Total (tax inc.).",
                    formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                    formatLang(self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                ))
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                raise UserError(_(
                    "The recipient bank account linked to this invoice is archived.\n"
                    "So you cannot confirm the invoice."
                ))
            if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                raise UserError(_(
                    "You cannot validate an invoice with a negative total amount. "
                    "You should create a credit note instead. "
                    "Use the action menu to transform it into a credit note or refund."
                ))

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif invoice.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            for move in future_moves:
                if move.auto_post == 'no':
                    move.auto_post = 'at_date'
                msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        for move in to_post:
            if move.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
            if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))
            if move.auto_post != 'no' and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
            if not move.journal_id.active:
                raise UserError(_(
                    "You cannot post an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))
            if move.display_inactive_currency_warning:
                raise UserError(_(
                    "You cannot validate a document with an inactive currency: %s",
                    move.currency_id.name
                ))

            if move.line_ids.account_id.filtered(lambda account: account.deprecated):
                raise UserError(_("A line of this move is using a deprecated account, you cannot post it."))

            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                move.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report)

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.line_ids._create_analytic_lines()
        to_post.write({
            'state': 'posted',
            'posted_before': True,
        })

        # Trigger copying for recurring invoices
        to_post.filtered(lambda m: m.auto_post not in ('no', 'at_date'))._copy_recurring_entries()

        for invoice in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(lambda aml:
                aml.partner_id != invoice.commercial_partner_id
                and aml.display_type not in ('line_note', 'line_section')
            )
            if wrong_lines:
                wrong_lines.write({'partner_id': invoice.commercial_partner_id.id})

            invoice.message_subscribe([
                p.id
                for p in [invoice.partner_id]
                if p not in invoice.sudo().message_partner_ids
            ])

            # Compute 'ref' for 'out_invoice'.
            if invoice.move_type == 'out_invoice' and not invoice.payment_reference:
                to_write = {
                    'payment_reference': invoice._get_invoice_computed_reference(),
                    'line_ids': []
                }
                for line in invoice.line_ids.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable')):
                    to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
                invoice.write(to_write)

            if (
                invoice.is_sale_document()
                and invoice.journal_id.sale_activity_type_id
                and (invoice.journal_id.sale_activity_user_id or invoice.invoice_user_id).id not in (self.env.ref('base.user_root').id, False)
            ):
                invoice.activity_schedule(
                    date_deadline=min((date for date in invoice.line_ids.mapped('date_maturity') if date), default=invoice.date),
                    activity_type_id=invoice.journal_id.sale_activity_type_id.id,
                    summary=invoice.journal_id.sale_activity_note,
                    user_id=invoice.journal_id.sale_activity_user_id.id or invoice.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for invoice in to_post:
            if invoice.is_sale_document():
                customer_count[invoice.partner_id] += 1
            elif invoice.is_purchase_document():
                supplier_count[invoice.partner_id] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices if amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        )._invoice_paid_hook()

        return to_post

class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    is_os_line = fields.Boolean()
    # Inherited this function to populate tax from Account.Move
    hsn_id = fields.Many2one('hsn.code', string='Hsn Code')
    custom_label = fields.Char('Custom Label')

    def _get_computed_taxes(self):
        res = super(AccountMoveLineInherit, self)._get_computed_taxes()
        if self.move_id.taxes_id:
            return res + self.move_id.taxes_id
        return res

    def _get_computed_account(self):
        self.ensure_one()
        self = self.with_company(self.move_id.journal_id.company_id)

        if not self.product_id:
            return
        # Custom Code
        analytical_rule = self.env['account.analytic.default'].search([('product_id', '=', self.product_id.id),
                                                                       ('journal_id', '=', self.journal_id.id)])
        if analytical_rule:
            return analytical_rule[0].custom_account_id.id
        # End of Custom Code
        fiscal_position = self.move_id.fiscal_position_id
        # Custom Code
        if fiscal_position:
            product_tax = self.product_id.taxes_id if self.move_id.is_sale_document(
                include_receipts=True) else self.product_id.supplier_taxes_id if self.move_id.is_purchase_document(
                include_receipts=True) else False
            tax_id = product_tax and product_tax[0].ids or self.tax_ids and self.tax_ids[0]._origin.ids or []
            fiscal_tax_account = fiscal_position.tax_ids.filtered(
                lambda x: x.tax_dest_id.id in tax_id or x.tax_src_id.id in tax_id)
            if fiscal_tax_account:
                return fiscal_tax_account[0].account_id.id
        if self.product_id.property_account_expense_id:
            return self.product_id.property_account_expense_id.id
        # End of Custom Code
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            return accounts['income'] or self.account_id
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            return accounts['expense'] or self.account_id

    # This function is Responsilbe for setting Analytical Account
    # Inherited it to select Analytical Account and Tag based on Journal
    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_account(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec and rec.filtered(lambda x: x.journal_id.id == self.journal_id.id):
                    record.analytic_account_id = rec.analytic_id
                    record.analytic_tag_ids = rec.analytic_tag_ids

class PartialLines(models.Model):
    _name = 'partial.line'

    entry_id = fields.Many2one('account.move', auto_join=True,domain=[('payment_state','in',('not_paid','partial')),('state','=','posted')])
    payment_line = fields.Many2one('account.move.line', string="Payment")
    move_id = fields.Many2one('account.move', required=True)
    payment_id = fields.Many2one('account.payment')
    partner_id = fields.Many2one('res.partner')
    move_amt = fields.Float(readonly=True, string="Move Amount")
    residual_amount = fields.Float(readonly=True, string="Residual Amount")
    amount = fields.Float()
    reconciled_id = fields.Many2one('account.partial.reconcile')

    @api.onchange('move_id')
    def set_required_data(self):
        for rec in self:
            rec.amount = 0
            if rec.move_id:
                rec.residual_amount = rec.move_id.amount_residual
                rec.move_amt = rec.move_id.amount_total_signed
            else:
                rec.residual_amount = rec.move_amt = 0

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(PartialLines, self).fields_get(allfields, attributes)
        payment_type = self._context.get("default_custom_payment_type") or self._context.get('payment_type')
        if payment_type:
            if payment_type == 'inbound':
                domain = "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')," \
                         " ('partner_id', '=', partner_id), ('amount_residual', '>', 0)]"
                name, move_amt = "Invoices", 'Invoice Amount'
            else:
                domain = "[('move_type', '=', 'in_invoice'), ('state', '=', 'posted')," \
                         " ('partner_id', '=', partner_id), ('amount_residual', '>', 0)]"
                name, move_amt = "Bills", 'Bill Amount'
            res["move_id"]["domain"] = domain
            res["move_id"]["string"] = name
            res["move_amt"]["string"] = move_amt
        return res

    @api.onchange('amount')
    def validate_amount(self):
        if self.amount and self.amount > self.residual_amount:
            raise ValidationError(r'Amount should not be greater than Invoice\Bill Residual Amount.')

    @api.ondelete(at_uninstall=False)
    def verify_line_before_unlink(self):
        for rec in self:
            if rec.reconciled_id and rec.payment_id.state == 'posted':
                raise ValidationError('You cannot delete reconciled Lines')

    def button_undo_reconciliation(self):
        self.reconciled_id.unlink()

    @api.model
    def create(self, values):
        res = super(PartialLines, self).create(values)
        if res.entry_id:
            payment_type = 'asset_receivable' if res.entry_id.custom_payment_type == 'inbound' else 'liability_payable'
            payment_line = res.entry_id.line_ids.filtered(lambda x: x.account_id.account_type == payment_type)
            if len(payment_line) == 1:
                res.payment_line = payment_line.id
        return res

