from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class PaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency):
        """Get the distribution of this payment term.
        :param date_ref: The move date to take into account
        :param currency: the move's currency
        :param company: the company issuing the move
        :param tax_amount: the signed tax amount for the move
        :param tax_amount_currency: the signed tax amount for the move in the move's currency
        :param untaxed_amount: the signed untaxed amount for the move
        :param untaxed_amount_currency: the signed untaxed amount for the move in the move's currency
        :param sign: the sign of the move
        :return (list<tuple<datetime.date,tuple<float,float>>>): the amount in the company's currency and
            the document's currency, respectively for each required payment date
        """
        self.ensure_one()
        company_currency = company.currency_id
        tax_amount_left = tax_amount
        tax_amount_currency_left = tax_amount_currency
        untaxed_amount_left = untaxed_amount
        untaxed_amount_currency_left = untaxed_amount_currency
        total_amount = tax_amount + untaxed_amount
        total_amount_currency = tax_amount_currency + untaxed_amount_currency
        result = []

        for line in self.line_ids.sorted(lambda line: line.value == 'balance'):
            term_vals = {
                'desc':line.desc,
                'percent':line.value_amount,
                'value':line.value,
                'date': line._get_due_date(date_ref),
                'has_discount': line.discount_percentage,
                'discount_date': None,
                'discount_amount_currency': 0.0,
                'discount_balance': 0.0,
                'discount_percentage': line.discount_percentage,
            }

            if line.value == 'fixed':
                term_vals['company_amount'] = sign * company_currency.round(line.value_amount)
                term_vals['foreign_amount'] = sign * currency.round(line.value_amount)
                company_proportion = tax_amount/untaxed_amount if untaxed_amount else 1
                foreign_proportion = tax_amount_currency/untaxed_amount_currency if untaxed_amount_currency else 1
                line_tax_amount = company_currency.round(line.value_amount * company_proportion) * sign
                line_tax_amount_currency = currency.round(line.value_amount * foreign_proportion) * sign
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
            elif line.value == 'percent':
                term_vals['company_amount'] = company_currency.round(total_amount * (line.value_amount / 100.0))
                term_vals['foreign_amount'] = currency.round(total_amount_currency * (line.value_amount / 100.0))
                line_tax_amount = company_currency.round(tax_amount * (line.value_amount / 100.0))
                line_tax_amount_currency = currency.round(tax_amount_currency * (line.value_amount / 100.0))
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
            else:
                line_tax_amount = line_tax_amount_currency = line_untaxed_amount = line_untaxed_amount_currency = 0.0

            tax_amount_left -= line_tax_amount
            tax_amount_currency_left -= line_tax_amount_currency
            untaxed_amount_left -= line_untaxed_amount
            untaxed_amount_currency_left -= line_untaxed_amount_currency

            if line.value == 'balance':
                term_vals['company_amount'] = tax_amount_left + untaxed_amount_left
                term_vals['foreign_amount'] = tax_amount_currency_left + untaxed_amount_currency_left
                line_tax_amount = tax_amount_left
                line_tax_amount_currency = tax_amount_currency_left
                line_untaxed_amount = untaxed_amount_left
                line_untaxed_amount_currency = untaxed_amount_currency_left

            if line.discount_percentage:
                if company.early_pay_discount_computation in ('excluded', 'mixed'):
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] - line_untaxed_amount * line.discount_percentage / 100.0)
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] - line_untaxed_amount_currency * line.discount_percentage / 100.0)
                else:
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] * (1 - (line.discount_percentage / 100.0)))
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] * (1 - (line.discount_percentage / 100.0)))
                term_vals['discount_date'] = date_ref + relativedelta(days=line.discount_days)

            result.append(term_vals)
        return result

class PaymentTermLineInherit(models.Model):
    _inherit = "account.payment.term.line"
    _order = "sequence,id"

    label = fields.Char(string='Label')
    desc = fields.Char("Description")
    sequence = fields.Integer(default=10)

