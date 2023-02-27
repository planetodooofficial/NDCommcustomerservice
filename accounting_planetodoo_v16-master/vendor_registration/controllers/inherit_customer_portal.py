from odoo import models, api, fields, _
from odoo import fields as odoo_fields, http, tools
from odoo.http import Controller, route, request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError
import base64


class CustomerPortalInherit(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id",
                                "entity_type", "l10n_in_gst_treatment"]

    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "pan_card", "gst_doc", "pan_no",
                               "cancelled_cheque", "acc_number", "bank_id", "swift_code", "usd_account_name",
                               "ifsc_number","is_msme","currency_id","msme_doc"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})
                gst_document = values.get('gst_doc')
                cancel_cheque = values.get('cancelled_cheque')
                pan_card = values.get('pan_card')
                binary_fields = (
                    (cancel_cheque, 'cancelled_cheque', 'check_file_name'), (pan_card, 'pan_card', 'pan_file_name'),
                    (gst_document, 'gst_doc', 'gst_doc_name'))
                values.pop('cancelled_cheque')
                values.pop('pan_card')
                values.pop('gst_doc')
                entity_value = values.get('entity_type')
                l10n_in_gst_treatment = values.get('l10n_in_gst_treatment')
                bank_id = values.get('bank_id', False)
                acc_name = values.get('acc_number', False)
                swift_code = values.get('swift_code', False)
                usd_account_name = values.get('usd_account_name', False)
                ifsc_number = values.get('ifsc_number', False)

                values.pop('bank_id')
                values.pop('acc_number')
                values.pop('swift_code')
                values.pop('usd_account_name')
                values.pop('ifsc_number')
                search_bank = request.env['res.bank'].sudo().search([('name', '=', bank_id), ('bic', '=', ifsc_number)])
                # download_pan = values.get('pan_card')
                values.update({
                    'entity_type': entity_value,
                    'l10n_in_gst_treatment': l10n_in_gst_treatment,
                    # 'pan_card': download_pan
                })
                search_rec = request.env['ir.attachment'].sudo().search([
                    ('res_id', '=', partner.id),
                ])
                search_rec.unlink()
                for rec in binary_fields:
                    attachment = rec[0].read()
                    setattr(partner, rec[1], False)
                    data = request.env['ir.attachment'].sudo().create({
                        'name': rec[0].filename,
                        'display_name': rec[0].filename,
                        'res_name': partner.name,
                        'type': 'binary',
                        'res_model': 'res.partner',
                        'res_id': partner.id,
                        'datas': base64.standard_b64encode(attachment),
                        'res_field': rec[1]
                    })
                    values.update({
                        rec[2]: rec[0].filename,
                    })
                if entity_value:
                    partner.sudo().write(values)
                bank_line_items = []
                if not search_bank:
                    bank_info = {
                        'name': bank_id,
                        'swift_code': swift_code,
                        'bic': ifsc_number,
                        'usd_account_name': usd_account_name
                    }
                    search_bank = search_bank.sudo().create(bank_info)

                    bank_line_ids = (0, 0, {'bank_id': search_bank.id,
                                            'acc_number': acc_name})

                    bank_line_items.append(bank_line_ids)
                    partner.sudo().write({'bank_ids': bank_line_items})
                    # 'line_ids': [(1, rec.id, data)]

                if search_bank:
                    search_bank.update({'swift_code': swift_code,
                                        'usd_account_name': usd_account_name})
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'

        return response

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        partner = request.env.user.partner_id
        if data.get("vat") and partner and partner.vat != data.get("vat"):
            if partner.can_edit_vat():
                if hasattr(partner, "check_vat"):
                    if data.get("country_id"):
                        data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")),
                                                                                   data.get("vat"))
                    partner_dummy = partner.new({
                        'vat': data['vat'],
                        'country_id': (int(data['country_id'])
                                       if data.get('country_id') else False),
                    })
                    try:
                        partner_dummy.check_vat()
                    except ValidationError:
                        error["vat"] = 'error'
            else:
                error_message.append(
                    _('Changing VAT number is not allowed once document(s) have been issued for your account. Please contact us directly for this operation.'))

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message
