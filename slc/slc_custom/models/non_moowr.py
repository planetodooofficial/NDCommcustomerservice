from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta

from markupsafe import escape, Markup
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError


class NonMoowr(models.Model):
    _name = 'non.moowr'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Purchase Order"
    _rec_names_search = ['name', 'partner_ref']
    _order = 'priority desc, id desc'

    is_create_moowr = fields.Boolean(default=False)
    shipment_ids = fields.One2many('boe.shipment', 'shipment_id')
    container_ids = fields.One2many('boe.container', 'container_id')
    name = fields.Char('Order Reference', required=False, index='trigram', copy=False, default='New')
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)
    origin = fields.Char('Source Document', copy=False,
                         help="Reference of the document that generated this purchase order "
                              "request (e.g. a sales order)")
    partner_ref = fields.Char('Vendor Reference', copy=False,
                              help="Reference of the sales order or bid sent by the vendor. "
                                   "It's used to do the matching when you receive the "
                                   "products as this reference is usually written on the "
                                   "delivery order sent by your vendor.")
    date_order = fields.Datetime('Order Deadline', required=False, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
    date_approve = fields.Datetime('Confirmation Date', readonly=1, index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Entity', required=False,
                                 change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    dest_address_id = fields.Many2one('res.partner',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                      string='Dropship Address',
                                      help="Put an address if you want to deliver directly from the vendor to the customer. "
                                           "Otherwise, keep empty to deliver to your own company.")
    currency_id = fields.Many2one('res.currency', 'Currency', required=False,
                                  default=lambda self: self.env.company.currency_id.id)
    state = fields.Selection([
        ('draft', 'BOE Draft'),
        # ('sent', 'BOE Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'BOE Validated'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    is_state = fields.Boolean(default=False)
    is_cancel = fields.Boolean(default=False)
    order_line = fields.One2many('non.moowr.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    notes = fields.Html('Terms and Conditions')

    invoice_count = fields.Integer(compute="_compute_invoice", string='Bill Count', copy=False, default=0, store=True)
    invoice_ids = fields.Many2many('account.move', string='Bills', copy=False, store=True)
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', store=True, readonly=True, copy=False, default='no')
    date_planned = fields.Datetime(
        string='Expected Arrival', index=True, copy=False, store=True, readonly=False,
        help="Delivery date promised by vendor. This date is used to determine expected arrival of products.")
    date_calendar_start = fields.Datetime(readonly=True, store=True)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True,
                                     tracking=True)
    tax_totals = fields.Binary(exportable=False)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True)

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        # Avoid access error on fiscal position, when reading a purchase order with company != user.company_ids
        compute_sudo=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', states={'done': [('readonly', True)]},
                                  help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    # product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product')
    user_id = fields.Many2one(
        'res.users', string='Buyer', index=True, tracking=True,
        default=lambda self: self.env.user, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=False, index=True,
                                 default=lambda self: self.env.company.id)
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code', string="Country code")
    currency_rate = fields.Float("Currency Rate", store=True,
                                 readonly=True,
                                 help='Ratio between the purchase order currency and the company currency')

    mail_reminder_confirmed = fields.Boolean("Reminder Confirmed", default=False, readonly=True, copy=False,
                                             help="True if the reminder email is confirmed by the vendor.")
    mail_reception_confirmed = fields.Boolean("Reception Confirmed", default=False, readonly=True, copy=False,
                                              help="True if PO reception is confirmed by the vendor.")

    receipt_reminder_email = fields.Boolean('Receipt Reminder Email', related='partner_id.receipt_reminder_email',
                                            readonly=False)
    reminder_date_before_receipt = fields.Integer('Days Before Receipt',
                                                  related='partner_id.reminder_date_before_receipt', readonly=False)
    is_exim = fields.Boolean(default=False)
    exim_count = fields.Integer(compute="_count_exim")


    #Function to show count of EXIM created from BOE
    def _count_exim(self):
        self.exim_count = self.env['purchase.order'].search_count([('source_document', '=', self.id)])

    # Function to show EXIM or Moowr document created from BOE on smart button
    def moowr_view(self):
        return {
            'name': 'EXIM Type I Draft',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'domain': [('source_document', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
        }

    def _compute_access_url(self):
        super(NonMoowr, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/purchase/%s' % (order.id)

    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            if po.partner_ref:
                name += ' (' + po.partner_ref + ')'
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
            result.append((po.id, name))
        return result

    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            self.order_line.filtered(lambda line: not line.display_type).date_planned = self.date_planned

    # Function to show validation if we are trying to delete purchase order before cancelling it
    @api.ondelete(at_uninstall=False)
    def _unlink_if_cancelled(self):
        for order in self:
            if not order.state == 'cancel':
                raise UserError(_('In order to delete a purchase order, you must cancel it first.'))

    def _must_delete_date_planned(self, field_name):
        # To be overridden
        return field_name == 'order_line'

    def onchange(self, values, field_name, field_onchange):
        """Override onchange to NOT to update all date_planned on PO lines when
        date_planned on PO is updated by the change of date_planned on PO lines.
        """
        result = super(NonMoowr, self).onchange(values, field_name, field_onchange)
        if self._must_delete_date_planned(field_name) and 'value' in result:
            already_exist = [ol[1] for ol in values.get('order_line', []) if ol[1]]
            for line in result['value'].get('order_line', []):
                if line[0] < 2 and 'date_planned' in line[2] and line[1] in already_exist:
                    del line[2]['date_planned']
        return result

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Purchase Order-%s' % (self.name)

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        # Ensures all properties and fiscal positions
        # are taken with the company of the order
        # if not defined, with_company doesn't change anything.
        self = self.with_company(self.company_id)
        if not self.partner_id:
            self.fiscal_position_id = False
            self.currency_id = self.env.company.currency_id.id
        else:
            self.fiscal_position_id = self.env['account.fiscal.position']._get_fiscal_position(self.partner_id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id
        return {}


    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id or not self.env.user.has_group('purchase.group_warning_purchase'):
            return

        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.purchase_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.purchase_warn and partner.purchase_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.purchase_warn != 'block' and partner.parent_id and partner.parent_id.purchase_warn == 'block':
                partner = partner.parent_id
            title = _("Warning for %s", partner.name)
            message = partner.purchase_warn_msg
            warning = {
                'title': title,
                'message': message
            }
            if partner.purchase_warn == 'block':
                self.update({'partner_id': False})
            return {'warning': warning}
        return {}

    # ------------------------------------------------------------
    # MAIL.THREAD
    # ------------------------------------------------------------

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_rfq_as_sent'):
            self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})
        return super(NonMoowr, self.with_context(
            mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def _notify_get_recipients_groups(self, msg_vals=None):
        """ Tweak 'view document' button for portal customers, calling directly
        routes for confirm specific to PO model. """
        groups = super(NonMoowr, self)._notify_get_recipients_groups(msg_vals=msg_vals)
        if not self:
            return groups

        self.ensure_one()
        try:
            customer_portal_group = next(group for group in groups if group[0] == 'portal_customer')
        except StopIteration:
            pass
        else:
            access_opt = customer_portal_group[2].setdefault('button_access', {})
            if self.env.context.get('is_reminder'):
                access_opt['title'] = _('View')
                actions = customer_portal_group[2].setdefault('actions', list())
                actions.extend([
                    {'url': self.get_confirm_url(confirm_type='reminder'), 'title': _('Accept')},
                    {'url': self.get_update_url(), 'title': _('Update Dates')},
                ])
            else:
                access_opt['title'] = _('Confirm')
                access_opt['url'] = self.get_confirm_url(confirm_type='reception')

        return groups

    def _notify_by_email_prepare_rendering_context(self, message, msg_vals, model_description=False,
                                                   force_email_company=False, force_email_lang=False):
        render_context = super()._notify_by_email_prepare_rendering_context(
            message, msg_vals, model_description=model_description,
            force_email_company=force_email_company, force_email_lang=force_email_lang
        )
        subtitles = [render_context['record'].name]
        # don't show price on RFQ mail
        if self.state not in ['draft', 'sent']:
            if self.date_order:
                subtitles.append(_('%(amount)s due\N{NO-BREAK SPACE}%(date)s',
                                   amount=format_amount(self.env, self.amount_total, self.currency_id,
                                                        lang_code=render_context.get('lang')),
                                   date=format_date(self.env, self.date_order, date_format='short',
                                                    lang_code=render_context.get('lang'))
                                   ))
            else:
                subtitles.append(
                    format_amount(self.env, self.amount_total, self.currency_id, lang_code=render_context.get('lang')))
        render_context['subtitles'] = subtitles
        return render_context

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'purchase':
            if init_values['state'] == 'to approve':
                return self.env.ref('purchase.mt_rfq_approved')
            return self.env.ref('purchase.mt_rfq_confirmed')
        elif 'state' in init_values and self.state == 'to approve':
            return self.env.ref('purchase.mt_rfq_confirmed')
        elif 'state' in init_values and self.state == 'done':
            return self.env.ref('purchase.mt_rfq_done')
        elif 'state' in init_values and self.state == 'sent':
            return self.env.ref('purchase.mt_rfq_sent')
        return super(NonMoowr, self)._track_subtype(init_values)

    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

    def button_approve(self, force=False):
        self = self.filtered(lambda order: order._approval_allowed())
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    def button_draft(self):
        self.write({'state': 'draft'})
        return {}

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        a = self.is_state = True
        b = self.is_cancel = True
        return a and b

    def _add_supplier_to_product(self):
        pass

    def button_cancel(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(
                        _("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

        self.write({'state': 'cancel', 'mail_reminder_confirmed': False})

    def button_unlock(self):
        self.write({'state': 'purchase'})

    def button_done(self):
        self.write({'state': 'done', 'priority': '0'})

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (
                x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(
            ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
            'partner_id': partner_invoice.id,
            'fiscal_position_id': (
                    self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.invalidate_model(['invoice_ids'])
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        self.check_access_rights('read')

        result = {
            'all_to_send': 0,
            'all_waiting': 0,
            'all_late': 0,
            'my_to_send': 0,
            'my_waiting': 0,
            'my_late': 0,
            'all_avg_order_value': 0,
            'all_avg_days_to_purchase': 0,
            'all_total_last_7_days': 0,
            'all_sent_rfqs': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }

        one_week_ago = fields.Datetime.to_string(fields.Datetime.now() - relativedelta(days=7))

        query = """SELECT COUNT(1)
                      FROM mail_message m
                      JOIN purchase_order po ON (po.id = m.res_id)
                      WHERE m.create_date >= %s
                        AND m.model = 'purchase.order'
                        AND m.message_type = 'notification'
                        AND m.subtype_id = %s
                        AND po.company_id = %s;
                   """

        self.env.cr.execute(query, (one_week_ago, self.env.ref('purchase.mt_rfq_sent').id, self.env.company.id))
        res = self.env.cr.fetchone()
        result['all_sent_rfqs'] = res[0] or 0

        # easy counts
        po = self.env['purchase.order']
        result['all_to_send'] = po.search_count([('state', '=', 'draft')])
        result['my_to_send'] = po.search_count([('state', '=', 'draft'), ('user_id', '=', self.env.uid)])
        result['all_waiting'] = po.search_count([('state', '=', 'sent'), ('date_order', '>=', fields.Datetime.now())])
        result['my_waiting'] = po.search_count(
            [('state', '=', 'sent'), ('date_order', '>=', fields.Datetime.now()), ('user_id', '=', self.env.uid)])
        result['all_late'] = po.search_count(
            [('state', 'in', ['draft', 'sent', 'to approve']), ('date_order', '<', fields.Datetime.now())])
        result['my_late'] = po.search_count(
            [('state', 'in', ['draft', 'sent', 'to approve']), ('date_order', '<', fields.Datetime.now()),
             ('user_id', '=', self.env.uid)])

        # Calculated values ('avg order value', 'avg days to purchase', and 'total last 7 days') note that 'avg order value' and
        # 'total last 7 days' takes into account exchange rate and current company's currency's precision.
        # This is done via SQL for scalability reasons
        query = """SELECT AVG(COALESCE(po.amount_total / NULLIF(po.currency_rate, 0), po.amount_total)),
                             AVG(extract(epoch from age(po.date_approve,po.create_date)/(24*60*60)::decimal(16,2))),
                             SUM(CASE WHEN po.date_approve >= %s THEN COALESCE(po.amount_total / NULLIF(po.currency_rate, 0), po.amount_total) ELSE 0 END)
                      FROM purchase_order po
                      WHERE po.state in ('purchase', 'done')
                        AND po.company_id = %s
                   """
        self._cr.execute(query, (one_week_ago, self.env.company.id))
        res = self.env.cr.fetchone()
        result['all_avg_days_to_purchase'] = round(res[1] or 0, 2)
        currency = self.env.company.currency_id
        result['all_avg_order_value'] = format_amount(self.env, res[0] or 0, currency)
        result['all_total_last_7_days'] = format_amount(self.env, res[2] or 0, currency)

        return result

    def _send_reminder_mail(self, send_single=False):
        if not self.user_has_groups('purchase.group_send_reminder'):
            return

        template = self.env.ref('purchase.email_template_edi_purchase_reminder', raise_if_not_found=False)
        if template:
            orders = self if send_single else self._get_orders_to_remind()
            for order in orders:
                date = order.date_planned
                if date and (send_single or (date - relativedelta(
                        days=order.reminder_date_before_receipt)).date() == datetime.today().date()):
                    if send_single:
                        return order._send_reminder_open_composer(template.id)
                    else:
                        order.with_context(is_reminder=True).message_post_with_template(template.id,
                                                                                        email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
                                                                                        composition_mode='comment')

    def send_reminder_preview(self):
        self.ensure_one()
        if not self.user_has_groups('purchase.group_send_reminder'):
            return

        template = self.env.ref('purchase.email_template_edi_purchase_reminder', raise_if_not_found=False)
        if template and self.env.user.email and self.id:
            template.with_context(is_reminder=True).send_mail(
                self.id,
                force_send=True,
                raise_exception=False,
                email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
                email_values={'email_to': self.env.user.email, 'recipient_ids': []},
            )
            return {'toast_message': escape(_("A sample email has been sent to %s.", self.env.user.email))}

    def _send_reminder_open_composer(self, template_id):
        self.ensure_one()
        try:
            compose_form_id = self.env['ir.model.data']._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]
        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Purchase Order')
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def get_confirm_url(self, confirm_type=None):
        """Create url for confirm reminder or purchase reception email for sending
        in mail."""
        if confirm_type in ['reminder', 'reception']:
            param = url_encode({
                'confirm': confirm_type,
                'confirmed_date': self.date_planned and self.date_planned.date(),
            })
            return self.get_portal_url(query_string='&%s' % param)
        return self.get_portal_url()

    def get_update_url(self):
        """Create portal url for user to update the scheduled date on purchase
        order lines."""
        update_param = url_encode({'update': 'True'})
        return self.get_portal_url(query_string='&%s' % update_param)

    def confirm_reminder_mail(self, confirmed_date=False):
        for order in self:
            if order.state in ['purchase', 'done'] and not order.mail_reminder_confirmed:
                order.mail_reminder_confirmed = True
                date = confirmed_date or self.date_planned.date()
                order.message_post(
                    body=_("%s confirmed the receipt will take place on %s.", order.partner_id.name, date))

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        return (
                self.company_id.po_double_validation == 'one_step'
                or (self.company_id.po_double_validation == 'two_step'
                    and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()))
                or self.user_has_groups('purchase.group_purchase_manager'))

    def _confirm_reception_mail(self):
        for order in self:
            if order.state in ['purchase', 'done'] and not order.mail_reception_confirmed:
                order.mail_reception_confirmed = True
                order.message_post(body=_("The order receipt has been acknowledged by %s.", order.partner_id.name))

    def _update_date_planned_for_lines(self, updated_dates):
        # create or update the activity
        activity = self.env['mail.activity'].search([
            ('summary', '=', _('Date Updated')),
            ('res_model_id', '=', 'purchase.order'),
            ('res_id', '=', self.id),
            ('user_id', '=', self.user_id.id)], limit=1)
        if activity:
            self._update_update_date_activity(updated_dates, activity)
        else:
            self._create_update_date_activity(updated_dates)

        # update the date on PO line
        for line, date in updated_dates:
            line._update_date_planned(date)

    # Fields to mapped with purchase order
    unit_name = fields.Char(string='Company/Unit Name')
    # mode = fields.Selection([('air', 'Air'), ('sea', 'Sea')])
    # mode_new = fields.Char(string="Mode")
    erp_job_number = fields.Char(string='CB JOB Number')
    client_ref_number = fields.Char(string='Client Ref Number')
    business_tags = fields.Char(string="Business Tags", store=True)

    bill_of_entry = fields.Binary(string='Bill of Entry')
    awb = fields.Binary(string='AWB/HBL')
    mawb = fields.Binary(string='MAWB/MBL')
    packing_list = fields.Binary(string='Packing List')
    duty_payment_challan = fields.Binary(string='Duty Payment Challan')

    invoice_tab_ids = fields.One2many('invoice.nonmoowr.line', 'invoicing_id')

    # New Field to be added
    port_code = fields.Char(string="Port Code", store=True)
    be = fields.Char(string="BE No", store=True, required=True)
    be_date = fields.Date(string="BE Date", store=True)
    be_type = fields.Char(string="BE Type", store=True)
    be_type_description = fields.Char(string="BE Type Description", store=True, compute= "fetch_be_description_according_to_be_type", readonly = True)
    iec = fields.Char(string="IEC", store=True)
    iec_br_code = fields.Char(string="IEC Br code", store=True)
    status = fields.Char(string="Status", store=True)
    gstin = fields.Char(string="GSTIN", store=True)
    cb_code = fields.Char(string="CB Code", store=True)
    invoice_count_new = fields.Char(string="Invoice Count", store=True)
    item_count = fields.Char(string="Item Count", store=True)
    container = fields.Char(string="Container", store=True)
    pkgs = fields.Char(string="Pkgs", store=True)
    gwt = fields.Char(string="G.WT (KGS)", store=True)
    be_status = fields.Char(string="BE Status", store=True)
    mode_new = fields.Char(string="Mode")
    def_be = fields.Char(string="DEF BE", store=True)
    kacha = fields.Char(string="KACHA", store=True)
    sec = fields.Char(string="SEC 48", store=True)
    reimp = fields.Char(string="REIMP", store=True)
    adv_be = fields.Char(string="ADV BE (Y/N/P)", store=True)
    assess = fields.Char(string="ASSESS", store=True)
    exam = fields.Char(string="EXAM", store=True)
    hss = fields.Char(string="HSS", store=True)
    first_check = fields.Char(string="FIRST CHECK", store=True)
    prov_final = fields.Char(string="PROV/FINAL", store=True, required=True)
    country_of_origin = fields.Char(string="COUNTRY OF ORIGIN", store=True)
    country_of_consignment = fields.Char(string="COUNTRY OF CONSIGNMENT", store=True)
    port_of_loading = fields.Char(string="PORT OF LOADING", store=True)
    port_of_shipment = fields.Char(string="PORT OF SHIPMENT", store=True)
    importner_name = fields.Char(string="IMPORTER NAME", store=True)
    importer_address = fields.Char(string="IMPORTER ADDRESS", store=True)
    cb_name = fields.Char(string="CB NAME", store=True)
    ad_code = fields.Char(string="AD CODE", store=True)
    aeo = fields.Char(string="AEO", store=True)
    ucr = fields.Char(string="UCR", store=True)
    bcd = fields.Char(string="BCD", store=True)
    acd = fields.Char(string="ACD", store=True)
    sws = fields.Char(string="SWS", store=True)
    nccd = fields.Char(string="NCCD", store=True)
    add = fields.Char(string="ADD", store=True)
    cvd = fields.Char(string="CVD", store=True)
    igst = fields.Char(string="IGST", store=True)
    g_cess = fields.Char(string="G.CESS", store=True)
    tot_ass_val = fields.Float(string="TOT.ASS VAL", store=True)
    sg = fields.Char(string="SG", store=True)
    saed = fields.Char(string="SAED", store=True)
    gsia = fields.Char(string="GSIA", store=True)
    tta = fields.Char(string="TTA", store=True)
    health = fields.Char(string="HEALTH", store=True)
    total_duty = fields.Float(string="TOTAl DUTY", store=True)
    int = fields.Char(string="INT", store=True)
    pnlty = fields.Char(string="PNLTY", store=True)
    fine = fields.Char(string="FINE", store=True)
    tot_amount = fields.Char(string="TOT. AMOUNT", store=True)

    bond_no_1 = fields.Char(string="BOND NO 1", store=True)
    port_1 = fields.Char(string="PORT 1", store=True)
    bond_cd_1 = fields.Char(string="BOND CD 1", store=True)
    debt_amt_1 = fields.Char(string="DEBT AMT 1", store=True)
    bg_amt_1 = fields.Char(string="BG AMT 1", store=True)
    bond_no_2 = fields.Char(string="BOND NO 2", store=True)
    port_2 = fields.Char(string="PORT 2", store=True)
    bond_cd_2 = fields.Char(string="BOND CD 2", store=True)
    debt_amt_2 = fields.Char(string="DEBT AMT 2", store=True)
    bg_amt_2 = fields.Char(string="BG AMT 2", store=True)
    sr_no_1 = fields.Char(string="SR. NO. 1", store=True)
    challan_no_1 = fields.Char(string="CHALLAN NO 1", store=True)
    paid_on_1 = fields.Char(string="PAID ON 1", store=True)
    amount_rs_1 = fields.Char(string="AMOUNT Rs. 1", store=True)
    sr_no_2 = fields.Char(string="SR. NO. 2", store=True)
    challan_no_2 = fields.Char(string="CHALLAN NO 2", store=True)
    paid_no_2 = fields.Char(string="PAID ON 2", store=True)
    amount_rs_2 = fields.Char(string="AMOUNT Rs. 2", store=True)
    wbe_no = fields.Char(string="WBE NO.", store=True)
    date = fields.Char(string="DATE", store=True)
    wbe_site = fields.Char(string="WBE SITE", store=True)
    wh_code = fields.Char(string="WH CODE", store=True)
    submission_date = fields.Date(string="Submission Date", store=True)
    submission_time = fields.Char(string="Submission Time", store=True)
    assessment_date = fields.Date(string="Assessment Date", store=True)
    assessment_time = fields.Char(string="Assessment Time", store=True)
    examination_date = fields.Date(string="Examination Date", store=True)
    examination_time = fields.Char(string="Examination Time", store=True)
    ooc_date = fields.Date(string="OOC Date", store=True)
    occ_time = fields.Char(string="OOC Time", store=True)
    occ_no = fields.Char(string="OOC NO", store=True)

    # Function to get be type description on the basis of be type, and also
    # through validation if BE type is except W, H or X
    @api.depends('be_type')
    def fetch_be_description_according_to_be_type(self):
        for rec in self:
            if rec.be:
                if rec.be_type == 'H':
                    rec.be_type_description = 'Home'
                elif rec.be_type == 'W':
                    rec.be_type_description = 'Inbond'
                elif rec.be_type == 'X':
                    rec.be_type_description = 'Exbond'
                else:
                    raise ValidationError("Please enter BE Type value in 'W', 'H' or 'X'")

    # Function to show sub category of exim txn category
    @api.onchange('exim_txn_category')
    def exim_sub_category_change_according_to_category(self):
        if self.exim_txn_category:
            var = {'domain': {
                'exim_txn_subcategory_id': [('category_name', '=', self.exim_txn_category)]}}
            return var

    @api.depends('order_line')
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = (
                    max(sale.mapped('order_line.sequence') or [0]) + 1)

    max_line_sequence = fields.Integer(
        string='Max sequence in lines',
        compute='_compute_max_line_sequence',
        store=True
    )

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.order_line:
                line.sequence = current_sequence
                current_sequence += 1

    # Function to through Validation if BE number already exist in BOE
    def write(self, line_values):
        search_be = self.env['non.moowr'].search(
            [('be', '=', line_values.get('be')), ('id', '!=', line_values.get('id'))])
        if search_be:
            raise ValidationError('BE already exist')
        res = super(NonMoowr, self).write(line_values)
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(NonMoowr,
                     self.with_context(keep_line_sequence=True)).copy(default)

    #  Function to create sequence and serial number of BOE
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('non.moowr') or _('New')
        search_be = self.env['non.moowr'].search([('be', '=', vals.get('be')), ('id', '!=', vals.get('id'))])
        if search_be:
            raise ValidationError('BE already exist')
        res = super(NonMoowr, self).create(vals)
        return res

    # Function to create purchase order or moowr or EXIM from BOE on create MOOWR button
    def create_purchase_order(self):
        if self.be_type == 'W':
            gwt = False
            pkgs = False
            search_custom_station = False
            if self.mode_new == 'Air':
                mode = 'air'
            elif self.mode_new == 'Sea':
                mode = 'sea'
            else:
                mode = ''
            model = self.env['non.moowr']
            label = False
            search_bond_no = False
            debt_amt_1 = False
            mawb_mbl = False
            # awb_hbl = False
            supplier = False
            if self.port_code:
                search_custom_station = self.env['customs.station'].search([('custom_station_name', '=', self.port_code)])
            if self.bond_no_1:
                search_bond_no = self.env['bond.master'].search([('bond_number', '=', self.bond_no_1)])
            try:
                if self.debt_amt_1:
                    field_labels = model.fields_get(allfields=['debt_amt_1'])
                    label = field_labels['debt_amt_1']['string']
                    debt_amt_1 = int(self.debt_amt_1)
                if self.pkgs:
                    field_labels = model.fields_get(allfields=['pkgs'])
                    label = field_labels['pkgs']['string']
                    pkgs = int(self.pkgs)

                if self.gwt:
                    field_labels = model.fields_get(allfields=['gwt'])
                    label = field_labels['gwt']['string']
                    gwt = float(self.gwt)
            except:
                raise UserError(_(f"Change value type of field {label}"))
            if self.shipment_ids:
                for i in self.shipment_ids:
                    # if awb_hbl == False:
                    #     awb_hbl = i.hawb_no
                    if mawb_mbl == False:
                        mawb_mbl = i.mawb_mbl
            if self.invoice_tab_ids:
                for j in self.invoice_tab_ids:
                    if supplier == False:
                        supplier = j.suppliers_name

            header_values = {'source_document': self.id,
                             'partner_id': self.partner_id.id,
                             'exim_txn_category': 'moowr',
                             # 'exim_txn_subcategory_id': ,
                             'mode': mode,
                             'boe': self.be,
                             'boe_date': self.be_date,
                             'erp_job_number': self.erp_job_number,
                             # 'awb_hbl': awb_hbl,
                             'mawb_mbl': mawb_mbl,
                             'client_ref_number': self.client_ref_number,
                             'gross_weight': gwt,
                             'gross_weight_uom': 'kgs',
                             'total_packages': pkgs,
                             'custom_stations': search_custom_station.id if search_custom_station != False else False,
                             'consignor': supplier,
                             'country_of_consignment': self.country_of_consignment,
                             'total_duty': self.total_duty,
                             'importer_name': self.importner_name,
                             'po_bond_number_debited': search_bond_no.id if search_bond_no != False else False,
                             'po_bond_debit_value': debt_amt_1,
                             'provisional': True if self.prov_final.lower() == 'p' else False,
                             }
            purchase_id = self.env['purchase.order'].create(header_values)

            invoice_tab_list = []
            for rec in self.invoice_tab_ids:
                rec_invoice = (0, 0, {
                    'invsno': rec.invsno,
                    'invoice_number': rec.invoice_no,
                    'invoice_date': rec.invoice_date,
                    'supplier': rec.suppliers_name,
                    'inco_terms': rec.incoterm,
                    'invoice_total': rec.inv_value,
                    'invoice_amount': rec.ass_value,
                    'related_party': rec.reltd
                })
                invoice_tab_list.append(rec_invoice)
            purchase_id.write({'invoice_tab_ids': invoice_tab_list})

            product_tab_list = []
            for line in self.order_line:
                model_line = self.env['non.moowr.line']

                line_label = False
                add_amount = False
                cvd_amount = False
                sg_amount = False
                if not line.product_id:
                    raise UserError(_(f"Product is required"))
                try:
                    if line.add_amount:
                        field_labels = model_line.fields_get(allfields=['add_amount'])
                        line_label = field_labels['add_amount']['string']
                        add_amount = round(line.add_amount)
                    if line.cvd_amount:
                        field_labels = model_line.fields_get(allfields=['cvd_amount'])
                        line_label = field_labels['cvd_amount']['string']
                        cvd_amount = round(line.cvd_amount)
                    if line.sg_amount:
                        field_labels = model_line.fields_get(allfields=['sg_amount'])
                        line_label = field_labels['sg_amount']['string']
                        sg_amount = round(line.sg_amount)
                except:
                    raise UserError(_(f"Change value type of field {line_label}"))

                rec_product = (0, 0, {
                    'invsno': line.invsno,
                    'itemsn': line.itemsn,
                    'invoice_no': line.invoice_no_new,
                    'product_id': line.product_id.id,
                    'caidc': line.caidc_amount,
                    'assessable_value': line.assess_value,
                    'basic_duty_rate': line.bcd_rate,
                    'total_basic_duty': line.bcd_amount,
                    'sws_rate': line.sws_rate,  # deepak label change kar
                    'sws_duty_amt': line.sws_amount,
                    'igst_rate': line.igst_rate,
                    'igst_amount': line.igst_amount,
                    'acd': line.acd_amount,
                    'sad': line.sad_amount,
                    'total_duty': line.total_duty,
                    'country_of_origin': line.coo,
                    'invoice_curr': line.prev_currency_code,
                    'name': line.item_description,
                    'product_qty': line.cqty,
                    'unit': line.cuqc,
                    'cth': line.cth,
                    'price_unit': line.upi,
                    'chcess': line.chcess_amount,
                    'spexd': round(line.sp_exd_amount),  # field missing in purchase order
                    'tta_amount': line.tta_amount,
                    'cess': round(line.cess_amount),
                    'eaidc': round(line.eaidc_amount),
                    'cusedc': round(line.cus_edc_amount),
                    'cushec': round(line.cus_hec_amount),
                    'ncd': round(line.ncd_amount),
                    'aggr': round(line.aggr_amount),
                    'add': add_amount,
                    'cvd': cvd_amount,
                    'sg': sg_amount})
                product_tab_list.append(rec_product)
            purchase_id.write({'order_line': product_tab_list})
            self.is_create_moowr = True
        else:
            raise ValidationError('BE Description is not Inbound')
        self.is_exim = True

    # Function to show extra fields of header on More info header button
    def extra_fields_to_show(self):
        return {
            'name': "Order Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'non.moowr',
            'view_id': self.env.ref('slc_custom.boe_form').id,
            'res_id': self.id,
            'target': 'new',
        }

    # def boe_cost_record_button(self):
    #     tree_view_id = self.env.ref('slc_custom.view_boe_cost_dimension_tree').id
    #     form_view_id = self.env.ref('slc_custom.view_boe_cost_dimension_form').id
    #
    #     return {
    #         'name': 'Boe Cost Record',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'boe.cost.dimension',
    #         'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
    #         'view_mode': 'tree,form',
    #         'target': 'current',
    #     }
    #
    # def boe_performance_record_button(self):
    #     pass


class NonMoowrLine(models.Model):
    _name = 'non.moowr.line'
    _inherit = 'analytic.mixin'
    _rec_name = 'name'

    name = fields.Char(string="Items")
    sequence = fields.Integer(string='Sequence', default=10)
    order_id = fields.Many2one('non.moowr', string='Order Reference', index=True, required=False,
                               ondelete='cascade')

    # new field to be added
    product_id = fields.Many2one('product.product', string='Product', compute='_fetch_product_from_material_code')
    invsno = fields.Integer(string="INVSNO", store=True)
    itemsn = fields.Integer(string="ITEMSN", store=True)
    invoice_no_new = fields.Char(string="INVOICE NO", store=True)
    part_code = fields.Char(string="PART CODE", store=True)
    cth = fields.Char(string="CTH", store=True)
    ceth = fields.Char(string="CETH", store=True)
    item_description = fields.Char(string="ITEM DESCRIPTION", store=True, required=True)
    fs = fields.Char(string="FS", store=True)
    pq = fields.Char(string="PQ", store=True)
    dc = fields.Char(string="DC", store=True)
    wc = fields.Char(string="WC", store=True)
    aq = fields.Char(string="AQ", store=True)
    upi = fields.Float(string="UPI", store=True)
    coo = fields.Char(string="COO", store=True)
    cqty = fields.Float(string="CQTY", store=True, required=True)
    cuqc = fields.Char(string="CUQC", store=True)
    sqty = fields.Float(string="SQTY", store=True)
    suqc = fields.Char(string="SUQC", store=True)
    sch = fields.Char(string="SCH", store=True)
    stnd_pr = fields.Char(string="STND/PR", store=True)
    rsp = fields.Char(string="RSP", store=True)
    reimp = fields.Char(string="REIMP", store=True)
    prov = fields.Char(string="PROV", store=True)
    end_use = fields.Char(string="END USE", store=True)
    prodn = fields.Char(string="PRODN", store=True)
    cntrl = fields.Char(string="CNTRL", store=True)
    qualfr = fields.Char(string="QUALFR", store=True)
    contnt = fields.Char(string="CONTNT", store=True)
    stmnt = fields.Char(string="STMNT", store=True)
    sub_docs = fields.Char(string="SUB DOCS", store=True)
    assess_value = fields.Float(string="ASSESS VALUE", store=True)
    total_duty = fields.Float(string="TOTAL DUTY", store=True)
    bcd_notn_no = fields.Char(string="BCD NOTN NO", store=True)
    acd_notn_no = fields.Char(string="ACD  NOTN NO", store=True)
    sws_notn_no = fields.Char(string="SWS NOTN NO", store=True)
    sad_notn_no = fields.Char(string="SAD NOTN NO", store=True)
    igst_notn_no = fields.Char(string="IGST NOTN NO", store=True)
    g_cess_notn_no = fields.Char(string="G CESS  NOTN NO", store=True)
    add_notn_no = fields.Char(string="ADD NOTN NO", store=True)
    cvd_notn_no = fields.Char(string="CVD NOTN NO", store=True)
    sg_notn_no = fields.Char(string="SG  NOTN NO", store=True)
    t_value_notn_no = fields.Char(string="T VALUE  NOTN NO", store=True)
    bcd_notn_sno = fields.Char(string="BCD NOTN SNO", store=True)
    acd_notn_sno = fields.Char(string="ACD  NOTN SNO", store=True)
    sws_notn_sno = fields.Char(string="SWS NOTN SNO", store=True)
    sad_notn_sno = fields.Char(string="SAD NOTN SNO", store=True)
    igst_notn_sno = fields.Char(string="IGST NOTN SNO", store=True)
    g_cess_notn_sno = fields.Char(string="G CESS  NOTN SNO", store=True)
    add_notn_sno = fields.Char(string="ADD NOTN SNO", store=True)
    cvd_notn_sno = fields.Char(string="CVD NOTN SNO", store=True)
    sg_notn_sno = fields.Char(string="SG  NOTN SNO", store=True)
    t_value_notn_sno = fields.Char(string="T VALUE  NOTN SNO", store=True)
    bcd_rate = fields.Char(string="BCD RATE", store=True)
    acd_rate = fields.Char(string="ACD  RATE", store=True)
    sws_rate = fields.Char(string="SWS Rate", store=True)
    sad_rate = fields.Char(string="SAD RATE", store=True)
    igst_rate = fields.Char(string="IGST RATE", store=True)
    g_cess_rate = fields.Char(string="G CESS  RATE", store=True)
    add_rate = fields.Char(string="ADD RATE", store=True)
    cvd_rate = fields.Char(string="CVD RATE", store=True)
    sg_rate = fields.Char(string="SG  RATE", store=True)
    t_value_rate = fields.Char(string="T VALUE  RATE", store=True)
    bcd_amount = fields.Float(string="BCD AMOUNT", store=True)
    acd_amount = fields.Float(string="ACD  AMOUNT", store=True)
    sws_amount = fields.Float(string="SWS AMOUNT", store=True)
    sad_amount = fields.Float(string="SAD AMOUNT", store=True)
    igst_amount = fields.Float(string="IGST AMOUNT", store=True)
    g_cess_amount = fields.Float(string="G CESS  AMOUNT", store=True)
    add_amount = fields.Float(string="ADD AMOUNT", store=True)
    cvd_amount = fields.Float(string="CVD AMOUNT", store=True)
    sg_amount = fields.Float(string="SG  AMOUNT", store=True)
    t_value_amount = fields.Float(string="T VALUE  AMOUNT", store=True)
    bcd_duty_fg = fields.Char(string="BCD Duty FG", store=True)
    acd_duty_fg = fields.Char(string="ACD  Duty FG", store=True)
    sws_duty_fg = fields.Char(string="SWS Duty FG", store=True)
    sad_duty_fg = fields.Char(string="SAD Duty FG", store=True)
    igst_duty_fg = fields.Char(string="IGST Duty FG", store=True)
    g_cess_duty_fg = fields.Char(string="G CESS  Duty FG", store=True)
    add_duty_fg = fields.Char(string="ADD Duty FG", store=True)
    cvd_duty_fg = fields.Char(string="CVD Duty FG", store=True)
    sg_duty_fg = fields.Char(string="SG  Duty FG", store=True)
    t_value_duty_fg = fields.Char(string="T VALUE  Duty FG", store=True)
    sp_exd_notn_no = fields.Char(string="SP EXD NOTN NO", store=True)
    chcess_notn_no = fields.Char(string="CHCESS NOTN NO", store=True)
    tta_notn_no = fields.Char(string="TTA NOTN NO", store=True)
    cess_notn_no = fields.Char(string="CESS NOTN NO", store=True)
    caidc_notn_no = fields.Char(string="CAIDC NOTN NO", store=True)
    eaidc_notn_no = fields.Char(string="EAIDC NOTN NO", store=True)
    cus_edc_notn_no = fields.Char(string="CUS EDC NOTN NO", store=True)
    cus_hec_notn_no = fields.Char(string="CUS HEC NOTN NO", store=True)
    ncd_notn_no = fields.Char(string="NCD NOTN NO", store=True)
    aggr_notn_no = fields.Char(string="AGGR NOTN NO", store=True)
    sp_exd_notn_sno = fields.Char(string="SP EXD NOTN SNO", store=True)
    chcess_notn_sno = fields.Char(string="CHCESS NOTN SNO", store=True)
    tta_notn_sno = fields.Char(string="TTA NOTN SNO", store=True)
    cess_notn_sno = fields.Char(string="CESS NOTN SNO", store=True)
    caidc_notn_sno = fields.Char(string="CAIDC NOTN SNO", store=True)
    eaidc_notn_sno = fields.Char(string="EAIDC NOTN SNO", store=True)
    cus_edc_notn_sno = fields.Char(string="CUS EDC NOTN SNO", store=True)
    cus_hec_notn_sno = fields.Char(string="CUS HEC NOTN SNO", store=True)
    ncd_notn_sno = fields.Char(string="NCD NOTN SNO", store=True)
    aggr_notn_sno = fields.Char(string="AGGR NOTN SNO", store=True)
    sp_exd_rate = fields.Char(string="SP EXD RATE", store=True)
    chcess_rate = fields.Char(string="CHCESS RATE", store=True)
    tta_rate = fields.Char(string="TTA RATE", store=True)
    cess_rate = fields.Char(string="CESS RATE", store=True)
    caidc_rate = fields.Char(string="CAIDC RATE", store=True)
    eaidc_rate = fields.Char(string="EAIDC RATE", store=True)
    cus_edc_rate = fields.Char(string="CUS EDC RATE", store=True)
    cus_hec_rate = fields.Char(string="CUS HEC RATE", store=True)
    ncd_rate = fields.Char(string="NCD RATE", store=True)
    aggr_rate = fields.Char(string="AGGR RATE", store=True)
    sp_exd_amount = fields.Float(string="SP EXD Amount", store=True)
    chcess_amount = fields.Float(string="CHCESS Amount", store=True)
    tta_amount = fields.Float(string="TTA Amount", store=True)
    cess_amount = fields.Float(string="CESS Amount", store=True)
    caidc_amount = fields.Char(string="CAIDC Amount", store=True)
    eaidc_amount = fields.Float(string="EAIDC Amount", store=True)
    cus_edc_amount = fields.Float(string="CUS EDC Amount", store=True)
    cus_hec_amount = fields.Float(string="CUS HEC Amount", store=True)
    ncd_amount = fields.Float(string="NCD Amount", store=True)
    aggr_amount = fields.Float(string="AGGR Amount", store=True)
    sp_exd_duty_fg = fields.Char(string="SP EXD Duty Fg", store=True)
    chcess_duty_fg = fields.Char(string="CHCESS Duty Fg", store=True)
    tta_duty_fg = fields.Char(string="TTA Duty Fg", store=True)
    cess_duty_fg = fields.Char(string="CESS Duty Fg", store=True)
    caidc_duty_fg = fields.Char(string="CAIDC Duty Fg", store=True)
    eaidc_duty_fg = fields.Char(string="EAIDC Duty Fg", store=True)
    cus_edc_duty_fg = fields.Char(string="CUS EDC Duty Fg", store=True)
    cus_hec_duty_fg = fields.Char(string="CUS HEC Duty Fg", store=True)
    ncd_duty_fg = fields.Char(string="NCD Duty Fg", store=True)
    aggr_duty_fg = fields.Char(string="AGGR Duty Fg", store=True)
    ref_no = fields.Char(string="REF NO", store=True)
    ref_dt = fields.Char(string="REF DT", store=True)
    prt_cd = fields.Char(string="SVB-PRT CD", store=True)
    lab = fields.Char(string="LAB", store=True)
    p_f = fields.Char(string="LAB-P/F", store=True)
    load_date = fields.Char(string="LOAD DATE", store=True)
    load_pf = fields.Char(string="LOAD-P/F")
    be_no = fields.Char(string="BE NO", store=True, required=True)
    prev_be_no = fields.Char(string="PREV BE NO", store=True)
    be_date = fields.Char(string="PREV BE DATE", store=True)
    prt_cd_new = fields.Char(string="PREV PRT CD", store=True)
    prev_unitprice = fields.Char(string="PREV UNITPRICE", store=True)
    prev_currency_code = fields.Char(string="PREV CURRENCY CODE", store=True)
    notn_no = fields.Char(string="NOTN NO", store=True)
    slno = fields.Char(string="SLNO", store=True)
    frt = fields.Char(string="FRT", store=True)
    ins = fields.Char(string="INS", store=True)
    duty = fields.Char(string="DUTY", store=True)
    sb_no = fields.Char(string="SB NO", store=True)
    sb_dt = fields.Char(string="SB DT", store=True)
    port_cd = fields.Char(string="PORT CD", store=True)
    sinv = fields.Char(string="SINV", store=True)
    simtemn = fields.Char(string="SIMTEMN", store=True)
    type = fields.Char(string="TYPE", store=True)
    manufact_cd = fields.Char(string="MANUFACT CD", store=True)
    source_cy = fields.Char(string="SOURCE CY", store=True)
    trans_cy = fields.Char(string="TRANS CY", store=True)
    address = fields.Char(string="ADDRESS", store=True)
    accessory_item_details = fields.Char(string="ACCESSORY ITEM DETAILS", store=True)
    lic_slno = fields.Char(string="LIC SLNO", store=True)
    lic_no = fields.Char(string="LIC NO", store=True)
    lic_date = fields.Char(string="LIC DATE", store=True)
    code = fields.Char(string="CODE", store=True)
    port = fields.Char(string="PORT", store=True)
    debit_value = fields.Char(string="DEBIT VALUE", store=True)
    qty = fields.Char(string="QTY", store=True)
    debit_qty = fields.Char(string="DEBIT QTY", store=True)
    certificate_number = fields.Char(string="CERTIFICATE NUMBER", store=True)
    date = fields.Char(string="DATE", store=True)
    type_new = fields.Char(string="CERT-TYPE", store=True)
    prc_level = fields.Char(string="PRC LEVEL", store=True)
    iec = fields.Char(string="IEC", store=True)
    branch_slno = fields.Char(string="BRANCH SLNO", store=True)
    info_type = fields.Char(string="INFO TYPE", store=True)
    qualifier = fields.Char(string="QUALIFIER", store=True)
    info_cd = fields.Char(string="INFO CD", store=True)
    info_text = fields.Char(string="INFO TEXT", store=True)
    info_msr = fields.Char(string="INFO MSR", store=True)
    uqc = fields.Char(string="UQC", store=True)
    c_sno = fields.Char(string="C SNO", store=True)
    new_name = fields.Char(string="NAME", store=True)
    code_new = fields.Char(string="SWD-CODE", store=True)
    percentage = fields.Char(string="PERCENTAGE", store=True)
    yield_pct = fields.Char(string="YIELD PCT", store=True)
    ing = fields.Char(string="ING", store=True)
    control_type = fields.Char(string="CONTROL TYPE", store=True)
    location = fields.Char(string="LOCATION", store=True)
    srt_dt = fields.Char(string="SRT DT", store=True)
    end_dt = fields.Char(string="END DT", store=True)
    res_cd = fields.Char(string="RES CD", store=True)
    res_text = fields.Char(string="RES TEXT", store=True)

    # Function to fetch product from product.product when part_code
    # which is matching with material code in product is filled
    @api.depends('part_code')
    def _fetch_product_from_material_code(self):
        for rec in self:
            material_code_id = self.env['product.product'].search([('material_code', '!=', None)])
            # product_tab_id = self.env['product.product'].search([('material_code_id.material_code', '=', rec.part_code)])
            product_tab_id = material_code_id.filtered(lambda x:x.material_code == rec.part_code)
            rec.product_id = product_tab_id.id

    # Function to show extra field of product line on addition field button
    def view_product_line(self):
        return {
            'name': "Product Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'non.moowr.line',
            'view_id': self.env.ref('slc_custom.product_line_form').id,
            'res_id': self.id,
            'target': 'current',
        }

    def _validate_analytic_distribution(self):
        pass

    # @api.model
    # def create(self, vals):
    #     if not self.env.context.get('Product'):
    #         invoice = vals.get('invoice_no_new')
    #         search_po = self.env['non.moowr'].search([('be', '=', vals.get('be_no'))])
    #         if not search_po:
    #             raise ValidationError('BE No is not correct or does not exist')
    #         a = len(search_po.order_line) + 1
    #         if a == int(search_po.item_count):
    #             print('Hello')
    #         else:
    #             raise ValidationError('Item line doess not match with item counts')
    #         search_invoice = self.env['invoice.nonmoowr.line'].search([('invoice_no', '=', invoice), ('invoicing_id', '=', vals.get('order_id'))])
    #         if not search_invoice:
    #             raise ValidationError('This Invoice is not created yet')
    #         if vals.get('invsno') == 0:
    #             raise ValidationError('Process cannot complete as Invoice serial number is missing')
    #     res = super(NonMoowrLine, self).create(vals)
    #     return res

    # def write(self, vals):
    #     res = super(NonMoowrLine, self).create(vals)
    #     # return res
    #     # if not self.env.context.get('Product'):
    #     invoice = vals.get('invoice_no_new')
    #     search_invoice = self.env['invoice.nonmoowr.line'].search([('invoice_no', '=', invoice)])
    #     if not search_invoice:
    #         raise ValidationError('This Invoice is not created yet')
    #     # res = super(NonMoowrLine, self).create(vals)
    #     return res


class NonMoowrInvoiceOrderLine(models.Model):
    _name = 'invoice.nonmoowr.line'

    invoicing_id = fields.Many2one('non.moowr')
    state = fields.Selection([
        ('draft', 'BOE'),
        ('sent', 'BOE Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'BOE Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    # new field to be added
    invsno = fields.Integer(string='INVSNO', required=True)
    be = fields.Char(string='BE No', required=True)
    invoice_no = fields.Char(string='Invoice No')
    invoice_date = fields.Char(string='Invoice Date')
    purchase_order_no_and_dt = fields.Char(string='PURCHASE ORDER NO. & DT')
    lc_no_dt = fields.Char(string='LC NO & DT')
    contract_no_date = fields.Char(string='CONTRACT NO & DATE')
    buyers_name = fields.Char(string="BUYER'S NAME")
    buyers_address = fields.Char(string="BUYER'S ADDRESS")
    sellers_name = fields.Char(string="SELLER'S NAME")
    sellers_address = fields.Char(string="SELLER'S ADDRESS")
    suppliers_name = fields.Char(string="SUPPLIER'S NAME")
    suppliers_address = fields.Char(string="SUPPLIER'S ADDRESS")
    third_party_name = fields.Char(string='THIRD PARTY NAME')
    third_party_address = fields.Char(string='THIRD PARTY ADDRESS')
    aeo = fields.Char(string='AEO')
    ad_code = fields.Char(string='AD CODE')
    inv_value = fields.Float(string='INV VALUE')
    freight = fields.Char(string='FREIGHT')
    insurance = fields.Char(string='INSURANCE')
    hss = fields.Char(string='HSS')
    loading = fields.Char(string='LOADING')
    commn = fields.Char(string='COMMN')
    pay_terms = fields.Char(string='PAY TERMS')
    valuation_method = fields.Char(string='VALUATION METHOD')
    currency = fields.Char(string='CURRENCY')
    incoterm = fields.Char(string='INCOTERM')
    reltd = fields.Char(string='RELTD')
    svb_ch = fields.Char(string='SVB CH')
    svb_no = fields.Char(string='SVB NO')
    date = fields.Date(string='DATE')
    loa = fields.Char(string='LOA')
    c_b = fields.Char(string='C&B')
    coc = fields.Char(string='CoC')
    cop = fields.Char(string='CoP')
    hnd_chg = fields.Char(string='HND CHG')
    gs = fields.Char(string='G&S')
    doc_chg = fields.Char(string='DOC CHG')
    coo = fields.Char(string='COO')
    r_lf = fields.Char(string='R & LF')
    oth_cost = fields.Char(string='OTH COST')
    ld_uld = fields.Char(string='LD/ULD')
    ws = fields.Char(string='WS')
    otc = fields.Char(string='OTC')
    misc_charge = fields.Char(string='MISC CHARGE')
    ass_value = fields.Char(string='ASS. VALUE')

    """Function to through validation if we are creating BOE manually,
       and BE already exist in invoice tab or if invoice number is duplicate 
       or if invoice serial number is zero or missing
    """
    @api.model
    def create(self, vals):
        # search_be = self.env['non.moowr'].search([('be', '=', vals.get('be'))])
        if not self.env.context.get('invoice'):
            search_po = self.env['non.moowr'].search([('be', '=', vals.get('be'))])
            if not search_po:
                raise ValidationError('BE No is not correct or does not exist')
            invoice = vals.get('invoice_no')
            serach_invoice_no = self.env['invoice.nonmoowr.line'].search(
                [('invoice_no', '=', invoice), ('invoicing_id', '=', vals.get('invoicing_id'))])
            if serach_invoice_no:
                raise ValidationError('Invoice No already exist')
            if vals.get('invsno') <= 0:
                raise ValidationError('Invoice serial number cannot be zero or negative')
            # a = len(search_po.invoice_tab_ids)
            # if a == int(search_po.invoice_count_new):
            #     print('hello')
            # else:
            #     raise ValidationError('Invoice Item lines does not match with invoice counts')
        res = super(NonMoowrInvoiceOrderLine, self).create(vals)
        return res

    """
    Function to through validation if we are updating BOE manually,
    and BE already exist in Invoice tab or if invoice number is duplicate 
    or there are more line as mentioned on header invoice count field
    or if invoice serial number is zero or missing
    """
    def write(self, vals):
        a = len(self.invoicing_id.invoice_tab_ids)
        print(a)
        if a > int(self.invoicing_id.invoice_count_new):
            raise ValidationError('More Lines')
        invoice = vals.get('invoice_no')
        serach_invoice_no = self.env['invoice.nonmoowr.line'].search(
            [('invoice_no', '=', invoice), ('invoicing_id', '=', self.invoicing_id.id)])
        if serach_invoice_no:
            raise ValidationError('Invoice No already exist')
        if vals.get('invsno') and vals.get('invsno') <= 0:
            raise ValidationError('Invoice serial number cannot be zero or negative')
        res = super(NonMoowrInvoiceOrderLine, self).write(vals)
        return res

    # Function to show extra fields of invoice line on additional fields button
    def view_invoice_line(self):
        return {
            'name': "Product Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.nonmoowr.line',
            'view_id': self.env.ref('slc_custom.invoice_form').id,
            'res_id': self.id,
            'target': 'current',
        }


class BoeShipment(models.Model):
    _name = 'boe.shipment'
    state = fields.Selection([
        ('draft', 'BOE'),
        ('sent', 'BOE Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'BOE Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    igm_no = fields.Char(string="IGM NO")
    igm_date = fields.Date(string="IGM DATE")
    inw_date = fields.Date(string="INW DATE")
    gigmno = fields.Char(string="GIGMNO")
    gigmdt = fields.Date(string="GIGMDT")
    mawb_date = fields.Date(string="MAWB DATE")
    hawb_no = fields.Char(string="HAWB/HBL")
    hawb_date = fields.Date(string="HAWB DATE")
    mawb_mbl = fields.Char(string="MAWB/MBL")
    pkg = fields.Char(string="PKG")
    gw = fields.Char(string="GW")
    be = fields.Char(string="BE No", required=True)
    # awb_hbl = fields.Char()

    shipment_id = fields.Many2one('non.moowr')
    is_state_confirm = fields.Boolean(default=False)

    """Function to through validation if we are creating BOE manually,
           and BE already exist in shipment tab or missing or IGM No is duplicate
        """
    @api.model
    def create(self, vals):
        if not self.env.context.get('shipment'):
            search_po = self.env['non.moowr'].search([('be', '=', vals.get('be'))])
            if not search_po:
                raise ValidationError('BE No is not correct or does not exist')
            igm = vals.get('igm_no')
            serach_igm_no = self.env['boe.shipment'].search(
                [('igm_no', '=', igm), ('shipment_id', '=', vals.get('shipment_id'))])
            if serach_igm_no:
                raise ValidationError('IGM No already exist')
        res = super(BoeShipment, self).create(vals)
        return res

    """Function to through validation if we are updating BOE manually,
               and BE already exist in shipment tab or missing or IGM No is duplicate
            """
    def write(self, vals):
        igm = vals.get('igm_no')
        serach_igm_no = self.env['boe.shipment'].search(
            [('igm_no', '=', igm), ('shipment_id', '=', vals.get('shipment_id'))])
        if serach_igm_no:
            raise ValidationError('IGM No already exist')
        res = super(BoeShipment, self).create(vals)
        return res

    @api.depends('shipment_id')
    def state_cal(self):
        if self.shipment_id.is_state == True:
            self.is_state_confirm = True


class BoeContainer(models.Model):
    _name = 'boe.container'

    container_id = fields.Many2one('non.moowr')
    state = fields.Selection([
        ('draft', 'BOE'),
        ('sent', 'BOE Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'BOE Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    # is_edit_only = fields.Boolean(related="container_id.")

    container_no = fields.Char(string="Container Number")
    seal_no = fields.Char(string="Seal Number")
    truck_no = fields.Char(string="Truck Number")
    fcl_lcl = fields.Char(string="FCL/LCL")
    be = fields.Char(string="BE No", required=True)

    # @api.model
    # def create(self, vals):
    #     if not self.env.context.get('container'):
    #         search_po = self.env['non.moowr'].search([('be', '=', vals.get('be'))])
    #         if not search_po:
    #             raise ValidationError('BE No is not correct or does not exist')
    #         container = vals.get('container_no')
    #         serach_container_no = self.env['boe.container'].search([('container_no', '=', container)])
    #         if serach_container_no:
    #             raise ValidationError('Container No already exist')
    #     res = super(BoeContainer, self).create(vals)
    #     return res
