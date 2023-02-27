from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re

# class AccountTax(models.Model):
#     _inherit = 'account.tax'
#
#     gstin_unit_id = fields.Many2one('res.partner',"GSTIN Unit")

class AccountMove(models.Model):
    _inherit = 'account.move'

    interbranch_payment_created = fields.Boolean(default=False)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    name = fields.Char(string='Journal Name', required=True,copy=True)
    is_a_default = fields.Boolean("Is a Default",copy=False)
    interbranch = fields.Boolean("Inter Branch",copy=False)
    code = fields.Char(string='Short Code', size=10, required=True, help="Shorter name used for display. The journal entries of this journal will also be named using this prefix by default.")


    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})

        # Find a unique code for the copied journal
        read_codes = self.env['account.journal'].with_context(active_test=False).search_read([('company_id', '=', self.company_id.id)], ['code'])
        all_journal_codes = {code_data['code'] for code_data in read_codes}

        copy_code = self.code
        code_prefix = re.sub(r'\d+', '', self.code).strip()
        counter = 1
        while counter <= len(all_journal_codes) and copy_code in all_journal_codes:
            counter_str = str(counter)
            copy_prefix = code_prefix[:self._fields['code'].size - len(counter_str)]
            copy_code = ("%s%s" % (copy_prefix, counter_str))

            counter += 1

        if counter > len(all_journal_codes):
            # Should never happen, but put there just in case.
            raise UserError(_("Could not compute any code for the copy automatically. Please create it manually."))
        if any(['name','code']) not in default:
            default.update(
                code=copy_code,
                name=_("%s (copy)") % (self.name or ''))
        else:
            default.update(alias_name= '')

        return super(AccountJournal, self).copy(default)

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_a_default = fields.Boolean("Is a Default", copy=False)
    ho_settlement = fields.Boolean("HO Settlement",copy=False)
    interbranch_settlement = fields.Boolean("Interbranch Settlement")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if default.get('code', False):
            return super(AccountAccount, self).copy(default)
        try:
            default['code'] = (str(int(self.code) + 10) or '').zfill(len(self.code))
            if 'name' not in default:
                default.setdefault('name', _("%s (copy)") % (self.name or ''))
            while self.env['account.account'].search([('code', '=', default['code']),
                                                      ('company_id', '=', default.get('company_id', False) or self.company_id.id)], limit=1):
                default['code'] = (str(int(default['code']) + 10) or '')
                if not default['name']:
                    default['name'] = _("%s (copy)") % (self.name or '')
        except ValueError:
            default['code'] = _("%s.copy") % (self.code or '')
            if 'name' not in default:
                default['name'] = self.name
        return super(AccountAccount, self).copy(default)