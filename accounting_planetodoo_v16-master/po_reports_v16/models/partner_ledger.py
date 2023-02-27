from odoo import fields, models, api
from odoo.exceptions import AccessError


class ResPartnerSale(models.Model):
    _inherit = 'res.partner'

    @api.model
    def sale_partner_ledger(self):
        if self.supplier_rank > 0 and self.customer_rank < 1:
            raise AccessError("You are not allowed to access partner ledger for this partner")
        return {
            'name': "Partner Ledger",
            'type': 'ir.actions.act_window',
            'res_model': 'partner.ledger',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_partner_id': self.id, 'default_type': 'partner_ledger'},
            'target': 'new',
        }

    @api.model
    def ledger_confirm(self):
        if self.supplier_rank > 0 and self.customer_rank < 1:
            raise AccessError("You are not allowed to access partner ledger for this partner")
        return {
            'name': "Ledger Confirm",
            'type': 'ir.actions.act_window',
            'res_model': 'partner.ledger',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_partner_id': self.id, 'default_type': 'ledger_confirm'},
            'target': 'new',
        }


class PartnerLedger(models.TransientModel):
    _name = 'partner.ledger'

    start_date = fields.Date(string='From Date', default=fields.Date.today().replace(day=1))
    end_date = fields.Date(string='To Date', default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Partner', help='Select Partner for movement')
    journal_id = fields.Many2many('account.journal', string='Journal Id')
    type = fields.Selection([('partner_ledger', 'Partner Ledger'), ('sales_register', 'Sales Register'),
                             ('purchase_register', 'Purchase Register'),
                             ('detail_purchase_register', 'Detail Purchase Register'),
                             ('ledger_confirm', 'Ledger Confirm'), ('detail_sales_register', 'Detail Sales Register')])

    def print_report(self):
        if self.type == 'partner_ledger':
            data = {'partner_id': self.partner_id.id, 'start_date': self.start_date, 'end_date': self.end_date}
            return self.env.ref('po_reports_v16.action_report_partner_ledger_pdf').report_action(self, data)
        elif self.type == 'ledger_confirm':
            data = {'partner_id': self.partner_id.id, 'start_date': self.start_date, 'end_date': self.end_date}
            return self.env.ref('po_reports_v16.action_ledger_confirm_report_pdf').report_action(self, data)
        else:
            move_type = self._context.get('move_type')
            url = self.get_base_url() + f'/download/reports?report_for={self.type}&start_date={self.start_date}&end_date={self.end_date}&company_id={self.env.company.id}&move_type={move_type}&journal_id={self.journal_id.ids or False}'
            return {'type': 'ir.actions.act_url', 'url': url}


class CustomReport(models.AbstractModel):
    _name = "report.po_reports_v16.po_report_pdf"

    def _get_report_values(self, docids, data=None):
        cr = self._cr
        query = """select sum(l.debit - l.credit) as opening_bal
                    from account_move_line l
                    join account_move m on l.move_id = m.id
                    join account_account a on l.account_id = a.id
                    where a.account_type in ('payable', 'receivable')  and m.state = 'posted' and
                    a.reconcile = True and l.partner_id = %s and l.date < %s and m.company_id = %s"""
        cr.execute(query, [data['partner_id'], data['start_date'], self.env.company.id])
        openbal = cr.dictfetchall()
        cr = self._cr
        query = """
                select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
                l.name as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit,m.invoice_origin as so_num
                from account_move_line l
                join account_move m on l.move_id = m.id
                join res_partner p on l.partner_id = p.id
                join account_account a on l.account_id = a.id
                join account_journal j on l.journal_id = j.id
                where a.reconcile = True and l.partner_id = %s and (m.date between %s and %s) and 
                a.account_type in ('payable', 'receivable') and m.state = 'posted' and m.state != 'cancel'
                and m.company_id = %s order by m.date"""
        cr.execute(query, [data['partner_id'], data['start_date'], data['end_date'], self.env.company.id])
        dat = cr.dictfetchall()
        return {
            'doc_ids': self.ids,
            'doc_model': 'partner.ledger',
            'openbal': openbal,
            'dat': dat,
            'data': data,
            'company_id': self.env['res.partner'].browse(data['partner_id']).company_id,
        }


class ConfirmLedger(models.AbstractModel):
    _name = "report.po_reports_v16.report_ledger_confirm"

    def payment_data(self, data):
        # Domains for filtering according to fields in form view
        lst = []
        search_domain1 = []

        if data['partner_id']:
            search_domain1.append(('partner_id', '=', data['partner_id']))
        # Date Filter
        if data['start_date'] and data['end_date']:
            search_domain1.append(('date', '>=', data['start_date']))
            search_domain1.append(('date', '<=', data['end_date']))

        # Filter records according to account payment
        ov_payment_lines = self.env['account.payment'].search(search_domain1)
        for payment in ov_payment_lines:
            lst.append((payment.name, payment.date, payment.amount_total))
        return lst, sum(ov_payment_lines.mapped('amount_total'))

    def invoice_data(self, data):
        lst2 = []

        search_domain = [('move_type', '=', 'out_invoice')]

        if data['partner_id']:
            search_domain.append(('partner_id', '=', data['partner_id']))
        # Date Filter
        if data['start_date'] and data['end_date']:
            search_domain.append(('invoice_date', '>=', data['start_date']))
            search_domain.append(('invoice_date', '<=', data['end_date']))

        # Filter records according to account move
        ov_invoice_lines = self.env['account.move'].search(search_domain)
        for invoice in ov_invoice_lines:
            lst2.append((invoice.name, invoice.date, invoice.amount_total))
        return lst2, sum(ov_invoice_lines.mapped('amount_total'))

    def _get_report_values(self, docids, data):
        payment_data, payment_total = self.payment_data(data)
        invoice_data, invoice_total = self.invoice_data(data)

        return {
            'doc_ids': docids,
            'data': data,
            'doc_model': 'partner.ledger',
            'payment_data': payment_data,
            'invoice_data': invoice_data,
            'invoice_total': invoice_total,
            'payment_total': payment_total,
        }