import datetime
from datetime import timedelta
import json
import random
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError


class ShopInstance(models.Model):
    _name = "shop.instance"
    _rec_name = "instance_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Shop Instance"

    instance_name = fields.Char(string="Instance Name", tracking=True)
    instance_url = fields.Char(string="Instance URL", required=True, tracking=True)
    instance_username = fields.Char(string="Instance UserName", required=True, tracking=True)
    instance_password = fields.Char(string="Instance Password", required=True, tracking=True)
    instance_type = fields.Many2one("ir.module.module", string="Instance Type",
                                    domain="[('category_id.name', '=', 'PO_Connector'), ('state', '=', 'installed')]",
                                    tracking=True)
    last_import_date = fields.Datetime(string="Last Import Date")
    shop_sales_channel_ids = fields.One2many("shop.sales.channel", "shop_instance_id",
                                             string="Shop Sales Channels")
    shop_import_logs_ids = fields.One2many("shop.import.logs", "shop_instance_id",
                                           string="Shop Import Logs")
    is_active = fields.Boolean(string="Is Active", tracking=True)
    company_id = fields.Many2one("res.company", string="Company",
                                 tracking=True)
    instance_status = fields.Selection([('draft', 'draft'), ('confirm', 'Confirm')], default="draft", string="Status")

    ''' Function to set a shop instance as confirm '''
    def action_confirm(self):
        self.instance_status = 'confirm'

    ''' Function to set a shop instance as draft '''
    def action_reset_to_draft(self):
        self.instance_status = 'draft'

    ''' Function to generate uniq code for states '''
    def uniq_state_code(self, state_name):
        state_name = state_name + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        data = [i for i in state_name.strip() if i != ' ']
        code = "".join(random.choices(data, k=3)).upper()
        if self.env["res.country.state"].search([('code', '=', code)]):
            self.uniq_state_code(state_name)
            data = self.uniq_state_code(state_name)
            print("1",data)
        else:
            print("2",code)
            return code

    ''' Function to validate partners for B2B '''
    def validate_partner(self, customer, company_type, gst_treatment, vat, ship_street, ship_street2, ship_city,
                         ship_state, ship_country,
                         ship_zip, ship_phone, ship_email):
        # To search a bill state, bill country
        search_ship_state = self.env["res.country.state"].search([('name', '=', ship_state)])
        search_ship_country = self.env["res.country"].search(
            [('name', '=', 'India'), ('code', '=', 'IN')])

        if not search_ship_state:
            search_ship_state = self.env["res.country.state"].create({
                'name': ship_state.upper(),
                'code': self.env["shop.instance"].uniq_state_code(ship_state),
                'country_id': search_ship_country.id,
                'is_a_default': False
            })

        # To search the customer
        search_partner = self.env["res.partner"].search(
            [('name', '=', customer), '|', ('active', '=', True),
             ('active', '=', False)], limit=1)

        # To check is that customer exist or not else it will create a new one
        if not search_partner:
            customer_vals = {
                'name': customer,
                'company_type': company_type,
                'l10n_in_gst_treatment': gst_treatment,
                'vat': "" if vat == 0 else vat,
                'street': ship_street,
                'street2': ship_street2,
                'city': ship_city,
                'state_id': search_ship_state.id,
                'zip': ship_zip,
                'country_id': search_ship_country.id,
                'phone': ship_phone,
                'email': ship_email,
            }
            search_partner = self.env["res.partner"].create(customer_vals)
            search_partner.onchange_vat()
        else:
            search_partner.onchange_vat()
        return search_partner

    ''' Function to validate shipping partners for B2B'''
    def validate_ship_address(self, partner, street, street2, city, state, country, zip, phone, email):
        # To search a ship state, ship country
        search_ship_state = self.env["res.country.state"].search([('name', '=', state)])
        search_ship_country = self.env["res.country"].search([('name', '=', 'India'), ('code', '=', 'IN')])

        if not search_ship_state:
            search_ship_state = self.env["res.country.state"].create({
                'name': state.upper(),
                'code': self.env["shop.instance"].uniq_state_code(state),
                'country_id': search_ship_country.id,
                'is_a_default': False
            })
        # To search the delivery address for that particular customer
        delivery_address = self.env["res.partner"].search(
            [('street', '=', street), ('street2', '=', street2), ('city', '=', city),
             ('zip', '=', zip), ('country_id', '=', search_ship_country.id)], limit=1)
        if not delivery_address:
            delivery_address_vals = {
                'parent_id': partner.id,
                'type': 'delivery',
                'street': street,
                'street2': street2,
                'city': city,
                'state_id': search_ship_state.id,
                'zip': zip,
                'country_id': search_ship_country.id,
                'phone': phone,
                'email': email,
            }
            delivery_address = self.env["res.partner"].create(delivery_address_vals)
        return delivery_address

    ''' Function to validate billing partners for B2B'''
    def validate_bill_address(self, partner, street, street2, city, state, country, zip, phone, email):
        # To search a bill state, bill country
        search_bill_state = self.env["res.country.state"].search([('name', '=', state)])
        search_bill_country = self.env["res.country"].search([('name', '=', 'India'), ('code', '=', 'IN')])

        if not search_bill_state:
            search_bill_state = self.env["res.country.state"].create({
                'name': state.upper(),
                'code': self.env["shop.instance"].uniq_state_code(state),
                'country_id': search_bill_country.id,
                'is_a_default': False
            })
        # To search the invoice address for that particular customer
        invoice_address = self.env["res.partner"].search(
            [('street', '=', street), ('street2', '=', street2), ('city', '=', city),
             ('zip', '=', zip), ('country_id', '=', search_bill_country.id)], limit=1)
        if not invoice_address:
            invoice_address_vals = {
                'parent_id': partner.id,
                'type': 'invoice',
                'street': street,
                'street2': street2,
                'city': city,
                'state_id': search_bill_state.id,
                'zip': zip,
                'country_id': search_bill_country.id,
                'phone': phone,
                'email': email,
            }
            invoice_address = self.env["res.partner"].create(invoice_address_vals)
        return invoice_address

    ''' Function to validate partners for B2C '''
    def validate_b2c_partner(self, customer, company_type, gst_treatment, vat, ship_street, ship_street2, ship_city,
                             ship_state, ship_country,
                             ship_zip, ship_phone, ship_email):
        # To search a bill state, bill country
        search_ship_state = self.env["res.country.state"].search([('name', '=', ship_state)])
        search_bill_country = self.env["res.country"].search(
            [('name', '=', 'India'), ('code', '=', 'IN')])

        if not search_ship_state:
            search_ship_state = self.env["res.country.state"].create({
                'name': ship_state.upper(),
                'code': self.env["shop.instance"].uniq_state_code(ship_state),
                'country_id': search_bill_country.id,
                'is_a_default': False
            })

        # To search a customer
        search_partner = self.env["res.partner"].search(
            [('name', '=', customer), '|', ('active', '=', True),
             ('active', '=', False)], limit=1)

        # To check is that customer exists or not else it will create a new one
        if not search_partner:
            customer_vals = {
                'name': customer,
                'customer_rank': 1,
                'company_type': company_type,
                'l10n_in_gst_treatment': gst_treatment,
                'vat': "" if vat == 0 else vat,
                'street': ship_street,
                'street2': ship_street2,
                'city': ship_city,
                'state_id': search_ship_state.id,
                'zip': ship_zip,
                'country_id': search_bill_country.id,
                'phone': ship_phone,
                'email': ship_email,
            }
            search_partner = self.env["res.partner"].create(customer_vals)
        return search_partner

    ''' Function to check customer gstin is present or not. '''
    def check_customer_gstin(self, customer_gstin):
        if 0 if customer_gstin is None else len(customer_gstin) >= 15:
            company_type = "company"
            gst_treatment = "regular"
            vat = customer_gstin
        else:
            company_type = "person"
            gst_treatment = "unregistered"
            vat = ""
        return company_type, gst_treatment, vat

    ''' Function to call validate partner, bill address and ship address functions for B2B '''
    def for_b2b_contact(self, customer, company_type, gst_treatment, vat, bill_street, bill_street2, bill_city,
                                    bill_state, bill_country, bill_zip, bill_phone, bill_email, ship_street,
                                    ship_street2, ship_city, ship_state, ship_country, ship_zip, ship_phone, ship_email):
        partner = self.env["shop.instance"].validate_partner(customer, company_type, gst_treatment, vat,
                                                             bill_street, bill_street2, bill_city,
                                                             bill_state.upper(), bill_country,
                                                             bill_zip, bill_phone, bill_email)
        bill_address = self.env["shop.instance"].validate_bill_address(partner, bill_street,
                                                                       bill_street2, bill_city,
                                                                       bill_state.upper(), bill_country,
                                                                       bill_zip, bill_phone, bill_email)
        ship_address = self.env["shop.instance"].validate_ship_address(partner, ship_street,
                                                                       ship_street2, ship_city,
                                                                       ship_state.upper(), ship_country,
                                                                       ship_zip, ship_phone, ship_email)
        return partner, bill_address, ship_address

    ''' Function to call validate b2c partner function for B2C '''
    def for_b2c_contact(self, customer, company_type, gst_treatment, vat, ship_street, ship_street2, ship_city,
                                ship_state, ship_country, ship_zip, ship_phone, ship_email):
        partner = self.env["shop.instance"].validate_b2c_partner(customer, company_type, gst_treatment, vat,
                                                                 ship_street, ship_street2, ship_city,
                                                                 ship_state.upper(), ship_country,
                                                                 ship_zip, ship_phone, ship_email)
        bill_address = partner
        ship_address = partner
        return partner, bill_address, ship_address

    ''' Function to calculate the taxes and to search it in system. '''
    # def tax_from_fiscal(self, tax, price_unit, discount, order_quantity, company):
    #     tax_amount = float(tax) / float(order_quantity)
    #     unit_price = float(price_unit) - tax_amount
    #     discount_per_unit = float(discount) / float(order_quantity)
    #     tax_after_calc = round((tax_amount / (unit_price - discount_per_unit)) * 100)
    #     search_tax = self.env["account.tax"].search(
    #         [('amount', '=', int(tax_after_calc)), ('is_a_default', '=', True),
    #          ('type_tax_use', '=', 'sale'), ('company_id', '=', company.id),
    #          ('tax_group_id.name', '=', 'GST')])
    #     return search_tax

    ''' Function to remove 0 amount taxes from order lines '''
    def remove_nill_taxes(self, sale_order):
        for so_line in sale_order.order_line:
            search_so_line_nil_tax = so_line.tax_id.search([('amount', '=', 0.0)])
            for nil_tax in search_so_line_nil_tax:
                so_line.tax_id = [(3, nil_tax.id)]

    ''' Function to write exceptions in so import logs tab. '''
    def write_exceptions(self, sale_order, exceptions_list):
        test = ''
        for i in exceptions_list:
            test += '<p>{}</p>'.format(i)
        if len(exceptions_list) > 0:
            sale_order.write({'import_logs': test, 'is_exception': True})

    ''' Function to confirm the orders and to create delivery and invoice. '''
    def sale_order_confirm(self, sale_order):
        if sale_order.sales_channel_id:
            # print("update_sale_order_crone sale_order: ", sale_order)
            sale_order.action_confirm()
            if sale_order.vinculum_order_date:
                order_date = datetime.datetime.strptime(sale_order.vinculum_order_date, "%d/%m/%Y %H:%M:%S")
                order_date = order_date - timedelta(hours=5,minutes=30)
                sale_order.write({'date_order': order_date})
            if sale_order and sale_order.state == "sale":
                search_delivery = self.env["stock.picking"].search([('origin', '=', sale_order.name)])
                for delivery in search_delivery:
                    delivery.write({'location_id': sale_order.location_id.id})
                    if sale_order.vinculum_ship_by_date:
                        ship_date = datetime.datetime.strptime(sale_order.vinculum_ship_by_date, "%d/%m/%Y %H:%M:%S")
                        delivery.write({'scheduled_date': ship_date})
                    if delivery.products_availability == "Not Available":
                        for stock_move_package in delivery.move_ids_without_package:
                            stock_move_package.quantity_done = stock_move_package.product_uom_qty
                    delivery.action_assign()
                    delivery.button_validate()

                if not sale_order.sales_channel_id.is_consumable_product:
                    invoice_vals = sale_order._prepare_invoice()

                    lst = []
                    for so_order_line in sale_order.order_line:
                        lst.append((0, 0, so_order_line._prepare_invoice_line()))

                    invoice_vals['invoice_line_ids'] = lst
                    result = self.env['account.move'].create(invoice_vals)
                    if sale_order.vinculum_ship_by_date:
                        ship_date = datetime.datetime.strptime(sale_order.vinculum_ship_by_date, "%d/%m/%Y %H:%M:%S")
                        result.write({'invoice_date': ship_date})

                    for invoice_line in result.invoice_line_ids:
                        invoice_line.write({'account_id': result.journal_id.default_account_id.id})
                    result.action_post()

    ''' Function to create credit note and return delivery for cancel orders. '''
    def order_credit_note(self, sale_order):
        search_delivery = self.env["stock.picking"].search([('origin', '=', sale_order.name)])

        stock_return_picking_obj = self.env["stock.return.picking"]
        for delivery in search_delivery:
            lst = []
            for move_id_package in delivery.move_ids_without_package:
                reverse_transfer_line_val = (0, 0, {
                    'product_id': move_id_package.product_id.id,
                    'quantity': move_id_package.quantity_done,
                    'uom_id': move_id_package.product_uom.id,
                    'move_id': move_id_package.id,
                    'to_refund': True,
                })
                lst.append(reverse_transfer_line_val)
            reverse_transfer_val = {
                'location_id': delivery.location_id.id,
                'picking_id': delivery.id,
                'product_return_moves': lst
            }
            stock_return_wizard_id = stock_return_picking_obj.create(reverse_transfer_val)
            stock_return_wizard_id.create_returns()

            search_reverse_delivery = self.env["stock.picking"].search([('origin', '=', f'Return of {delivery.name}')])
            search_reverse_delivery.action_set_quantities_to_reservation()
            search_reverse_delivery.button_validate()

        search_invoice = self.env["account.move"].search([('invoice_origin', '=', sale_order.name),
                                                          ('move_type', '=', 'out_invoice')])
        account_move_reversal_obj = self.env["account.move.reversal"]
        invoice_val = {
            'refund_method': 'cancel',
            'date_mode': 'entry',
            'journal_id': search_invoice.journal_id.id,
            'move_ids': [(4, search_invoice.id)]
        }
        account_move_reverse_wizard_id = account_move_reversal_obj.create(invoice_val)
        account_move_reverse_wizard_id.reverse_moves()

    ''' Function to create hsn if does not exist '''
    # def hsn_create(self, amazon_file, order_line, tax, price_unit, discount, order_quantity,
    #                                               wizard_id):
    #     if amazon_file:
    #         hsn_code = order_line['hsn']
    #         hsn_exist = self.env["hsn.code"].search([('hsnsac_code', '=', hsn_code)])
    #         if not hsn_exist:
    #             if amazon_file:
    #                 tax_id = self.tax_from_fiscal(tax, price_unit, discount, order_quantity,
    #                                               wizard_id.company_id).id
    #             else:
    #                 tax_id = self.tax_from_fiscal(tax, price_unit, discount, order_quantity,
    #                                               self.company_id).id
    #             hsn_record = {
    #                 'hsnsac_code': hsn_code,
    #                 'type': 's',
    #                 'taxes_id': tax_id,
    #                 'is_active': True
    #             }
    #             hsn_exist = self.env['hsn.code'].create(hsn_record)
    #     else:
    #         hsn_exist = False
    #     return hsn_exist

    ''' Function to create product if does not exist. '''
    def product_create(self, product_uom, tax, order_quantity, product, product_internal_reference, price_unit, amazon_file, sales_channel):
        if not product_uom:
            search_uom = self.env["uom.uom"].search([('name', '=', 'Units')])
        else:
            search_uom = self.env["uom.uom"].search([('name', '=', product_uom)])
        tax_amount = float(tax) / float(order_quantity)
        product_vals = {
            'is_exception': True,
            'name': product,
            'default_code': product_internal_reference,
            'uom_id': search_uom.id,
            'list_price': float(price_unit) - tax_amount if not amazon_file else float(
                price_unit) - tax_amount,
            'detailed_type': 'product' if not sales_channel.is_consumable_product else 'consu',
        }
        search_product = self.env["product.product"].create(product_vals)
        return search_product

    ''' Function to generate logs for success '''
    def generate_success_logs(self,class_id, start_date, end_date, count, operation_performed):
        class_id.shop_import_logs_ids = [(0, 0, {'start_date': start_date,
                                             'end_date': end_date,
                                             'no_of_records': count,
                                             'operation_performed': operation_performed,
                                             'status': 'success',
                                             })]
        return class_id.shop_import_logs_ids

    ''' Function to generate logs for exceptions '''
    def generate_exception_logs(self,class_id, start_date, count, end_date, order_number, operation_performed, exception):
        class_id.shop_import_logs_ids = [(0, 0, {'start_date': start_date,
                                             'no_of_records': count,
                                             'end_date': end_date,
                                             'operation_performed': operation_performed,
                                             'status': 'exception',
                                             'log_exception': order_number + ': ' + str(exception),
                                             })]

    ''' This is the Base function for vinculum and file imports for sales orders and 
        for file imports based on the condition in sales channel (Confirm Orders, Confirm Delivery Orders, 
        Confirm Invoices) it will create and confirm the order, delivery and invoice.
    '''
    def import_order(self):
        operation_performed = 'Sale Order Create(Vinculum)'
        amazon_file = self.env.context.get('amazon_file', False)
        start_date = datetime.datetime.now()

        if self.last_import_date and not amazon_file:
            from_date = self.last_import_date - datetime.timedelta(days=7)
        else:
            current_date = datetime.date.today()
            from_date = (current_date - relativedelta(days=7))

        if self.last_import_date:
            to_date = self.last_import_date
        else:
            current_date = datetime.date.today()
            to_date = current_date

        count = 0
        order_number_id = ''
        try:
            ''' Condition to check whether if it is amazon file if true then else part be executed. '''
            imported_order_list = []
            if not amazon_file:
                action_name = f"action_{self.instance_type.shortdesc.lower()}"
                data = getattr(self, action_name)(from_date, to_date)
            else:
                data = amazon_file
                wizard_id = data[0]['wizard_id']

            ''' To get the each records from list of dictionary data  '''
            for sale_order in data:
                exceptions_list = []
                order_number_id = sale_order['orderId']
                order_date = sale_order['orderDate']
                if order_date is None or order_date == "":
                    exceptions_list.append(f"Order Number: {order_number_id} ==> Order Date is not provided in data.\n")

                ''' Condition to check whether it is a amazon file, if not then else part will be executed. '''
                if amazon_file:
                    date_order = datetime.datetime.strptime(str(order_date), "%Y-%m-%d %H:%M:%S")
                    orderLocation = sale_order['orderLocation']
                    location = self.env['stock.location'].search([('name', '=', orderLocation)])
                    sales_channel = wizard_id.sales_channel_id
                    status = sale_order['status']
                else:
                    date_order = datetime.datetime.strptime(str(order_date), "%d/%m/%Y %H:%M:%S")
                    status = sale_order['status']
                    orderSource = sale_order['orderSource']
                    fulfillmentLocCode = sale_order['fulfillmentLocCode']  # this will be seller_id

                    if orderSource is None or orderSource == "":
                        exceptions_list.append(
                            f"Order Number: {order_number_id} ==> Order source is not provided in the data.\n")
                    if fulfillmentLocCode is None or fulfillmentLocCode == "":
                        exceptions_list.append(
                            f"Order Number: {order_number_id} ==> Fullfillment Loc Code is not provided in the data.\n")

                    fullfillment_code = self.env['seller.merchant'].search([('name', '=', fulfillmentLocCode)])

                    orderLocation = sale_order['orderLocation']  # this will be location code
                    order_loc = self.env['locations.code'].search([('location_code', '=', orderSource)])

                    ''' Condition to check whether order loc is true or not if yes then it will search with all four 
                        condition seller_id, location_code_id, shop_instance_id and company_id.
                        if condition is false then it will only search with seller_id, shop_instance_id and company_id.
                    '''
                    if not order_loc:
                        sales_channel = self.env['shop.sales.channel'].sudo().search([('seller_id', '=', fullfillment_code.id),
                                                                               ('shop_instance_id', '=', self.id),
                                                                               ],
                                                                              limit=1)
                    else:
                        sales_channel = self.env['shop.sales.channel'].sudo().search([('seller_id', '=', fullfillment_code.id),
                                                                               ('location_code_id', '=', order_loc.id),
                                                                               ('shop_instance_id', '=', self.id),
                                                                               ])
                if not sales_channel:
                    is_channel_exception = True
                    sales_channel = self.env['shop.sales.channel'].sudo().search([('seller_id', '=', 'NO'),
                                                                                  ('location_code_id', '=', 'NO'),
                                                                                  ('shop_instance_id', '=', self.id),
                         ])
                else:
                    is_channel_exception = False

                default_journal = self.env['account.journal'].search([('name', '=', 'Tax Invoices'),
                                                                      ('company_id', '=', sales_channel.company_id.id)])

                ''' To fetch all the values from dictionary '''
                customer = sale_order['customerName']

                # To get the shipping address details
                ship_street = sale_order['shipAddress1']
                ship_street2 = sale_order['shipAddress2']
                ship_city = sale_order['shipCity']
                ship_state = sale_order['shipState']
                ship_country = sale_order['shipCountry']
                ship_zip = sale_order['shipPincode']
                ship_phone = sale_order['shipPhone1']
                ship_email = sale_order['shipEmail1']

                # To get the billing address details
                bill_street = sale_order['billAddress1']
                bill_street2 = sale_order['billAddress2']
                bill_city = sale_order['billCity']
                bill_state = sale_order['billState']
                bill_country = sale_order['billCountry']
                bill_zip = sale_order['billPincode']
                bill_phone = sale_order['billPhone1']
                bill_email = sale_order['billEmail1']

                customer_gstin = sale_order['customerGSTIN']

                if customer is None or customer == "":
                    exceptions_list.append(
                        f"Order Number: {order_number_id} ==> Customer Name is not provided in the data.\n")
                if ship_state is None or ship_state == "":
                    exceptions_list.append(
                        f"Order Number: {order_number_id} ==> Shipping state is not provided in the data.\n")
                if bill_state is None or bill_state == "":
                    exceptions_list.append(
                        f"Order Number: {order_number_id} ==> Billing state is not provided in the data.\n")

                # B2B and B2C
                # if B2B customer is required, if billing address != shipping address then create 2 partners, billing == partner
                # in B2B if billing address == shipping address then create 1 partner
                # if B2C all three addresses will be same partner, shipping, billing

                check_customer_gstin_obj = self.env["shop.instance"].check_customer_gstin(customer_gstin)
                if check_customer_gstin_obj[0] == "company":
                    if customer:
                        contact_obj = self.env["shop.instance"].for_b2b_contact(customer, check_customer_gstin_obj[0],
                                    check_customer_gstin_obj[1], check_customer_gstin_obj[2], bill_street, bill_street2, bill_city,
                                    bill_state, bill_country, bill_zip, bill_phone, bill_email, ship_street,
                                    ship_street2, ship_city, ship_state, ship_country, ship_zip, ship_phone, ship_email)
                if check_customer_gstin_obj[0] == "person":
                    if not amazon_file and customer == '':
                        customer = self.instance_name + ' - ' + ship_state.upper() + ' - ' + ship_zip
                    else:
                        if customer == '':
                            customer = wizard_id.shop_instance_id.instance_name + ' - ' + ship_state.upper() + ' - ' + str(
                                ship_zip)
                    contact_obj = self.env["shop.instance"].for_b2c_contact(customer, check_customer_gstin_obj[0],
                                check_customer_gstin_obj[1], check_customer_gstin_obj[2], ship_street, ship_street2, ship_city,
                                ship_state, ship_country, ship_zip, ship_phone, ship_email)

                # To create sale order
                lst = []
                tax_dict = {}  # list of dictionary
                i = 0
                for order_line in sale_order['items']:
                    ''' To fetch all the values from the vinculum and amazon dictionary for line level. '''
                    product = order_line['skuName']
                    product_internal_reference = order_line['sku']
                    product_uom = order_line['uom']
                    order_quantity = order_line['orderQty']
                    price_unit = order_line['unitPrice']
                    tax = order_line['taxAmount']
                    discount = order_line['discountAmt']

                    if product == "" or product is None:
                        exceptions_list.append(
                            f"Order Number: {order_number_id} ==> Product is not provided in the data.\n")
                        # when None type object comes as a product
                        product = "Unknown Product"
                    if product_uom is None or product_uom == "":
                        exceptions_list.append(
                            f"Order Number: {order_number_id} ==> Product uom is not provided in the data.\n")

                    # To search a product
                    search_product = self.env["product.product"].search([('name', '=', product),
                                                                         ('default_code', '=',
                                                                          product_internal_reference)])

                    # hsn_exist = self.env["shop.instance"].hsn_create(amazon_file, order_line, tax, price_unit, discount, order_quantity,
                    #                               self if not amazon_file else wizard_id)

                    # Check is that product exists or not
                    if not search_product:
                        is_exception = True
                        search_product = self.env["shop.instance"].product_create(product_uom, tax, order_quantity,
                                                                                  product, product_internal_reference, price_unit, amazon_file, sales_channel)
                    else:
                        is_exception = False

                    # Check is that product uom exist or not
                    if not product_uom:
                        search_uom = self.env["uom.uom"].search([('name', '=', 'Units')])
                    else:
                        search_uom = self.env["uom.uom"].search([('name', '=', product_uom)])

                    if product:
                        if float(order_quantity) > 0:
                            tax_amount = float(tax) / float(order_quantity)
                            discount_per_unit = float(discount) / float(order_quantity)
                        else:
                            tax_amount = 0
                            discount_per_unit = 0
                        unit_price = float(price_unit) - tax_amount

                        if unit_price > 0:
                            discount_in_percentage = discount_per_unit / unit_price * 100
                        else:
                            discount_in_percentage = 0

                        sale_order_line_dict = {
                            'is_exception': is_exception,
                            'product_id': search_product.id,
                            'name': search_product.description[3:-4] if search_product.description else product,
                            'product_uom': search_uom.id,
                            'product_uom_qty': order_quantity,
                            'price_unit': float(price_unit) - tax_amount if not amazon_file else float(
                                price_unit) - tax_amount,
                            'discount': discount_in_percentage,
                            # 'hsn_id': hsn_exist.id if hsn_exist else False,
                        }
                        if not amazon_file:
                            ''' To fetch all the values from the amazon dictionary for line level. '''
                            line_no = order_line['lineno']
                            sale_order_line_dict['cust_line_id'] = line_no
                            sale_order_line_dict['vinculum_status'] = order_line['status']

                            ''' To store line level data of vinculum api '''
                            sale_order_line_dict.update(sale_order['extra_lines_data'][i])

                            # Condition to check for tax, price_unit and order_quantity for tax calculation
                            # if float(tax) and float(price_unit) and float(order_quantity) > 0:
                            #     search_tax = self.tax_from_fiscal(tax, price_unit, discount, order_quantity,
                            #                                       sales_channel.company_id)
                            #     if not search_product.taxes_id:
                            #         if search_tax:
                            #             search_product.write({'taxes_id': [(4, search_tax.id)]})
                            #     tax_dict[line_no] = search_tax
                        else:
                            sale_order_line_dict['amazon_status'] = order_line['status']
                            sale_order_line_dict['item_id'] = order_line['item_id']
                            sale_order_line_dict['stock_loc_id'] = self.env['stock.location'].search(
                                [('name', '=', order_line['location_id'])], limit=1).id
                            # if float(tax) and float(price_unit) and float(order_quantity) > 0:
                            #     search_tax = self.tax_from_fiscal(tax, price_unit, discount, order_quantity,
                            #                                       sales_channel.company_id)

                        # sale order line values
                        sale_order_line_vals = (0, 0, sale_order_line_dict)
                        lst.append(sale_order_line_vals)

                    # sale order values
                    sale_order_vals = {
                        'name': order_number_id,
                        'is_channel_exception': is_channel_exception,
                        'is_exception': True if not sales_channel else False,
                        'sales_channel_id': sales_channel.id,
                        'location_id': sales_channel.stock_location_id.id if not amazon_file else self.env['stock.location'].search(
                                [('name', '=', order_line['location_id'])], limit=1).id,
                        'date_order': date_order,
                        'partner_id': contact_obj[0].id,
                        'company_id': sales_channel.company_id.id,
                        'partner_shipping_id': contact_obj[1].id,
                        'partner_invoice_id': contact_obj[2].id,
                        'shop_instance_id': self.id if not amazon_file else wizard_id.shop_instance_id.id,
                        'order_line': lst
                    }
                    if not amazon_file:
                        sale_order_vals['vinculum_status'] = status
                        sale_order_vals['vinculum_order_source'] = orderSource
                        sale_order_vals['vinculum_fullfillment_code'] = fulfillmentLocCode
                    i += 1
                # To search a sale order
                search_sale_order = self.env["sale.order"].search([('name', '=', order_number_id)])

                # Check is that sale order exist or not
                if not search_sale_order:
                    if not amazon_file:
                        if orderSource is not None or len(orderSource) != 0:
                            sale_order_id = self.env["sale.order"].create(sale_order_vals)
                            imported_order_list.append(sale_order_id)
                            count += 1
                            sale_order_id.write({'l10n_in_journal_id': sales_channel.sales_journal_id.id
                            if sales_channel and sales_channel.sales_journal_id else default_journal.id,
                                                 })
                            # Function call for fiscal position update according to states
                            # sale_order_id.set_order_line()

                            ''' To store header level data of vinculum api '''
                            sale_order_id.write(sale_order['extra_data'])

                            print("tax_dict: ", tax_dict)

                            ''' For loop on order line to apply tax based on the fiscal position
                                searched a tax in fiscal position tax_ids line in Tax on Product to get Tax to Apply.
                            '''
                            for so_line in sale_order_id.order_line:
                                # so_line._compute_tax_id()
                                for fiscal_tax_line in sale_order_id.fiscal_position_id.tax_ids:
                                    if tax_dict:
                                        if so_line.cust_line_id in tax_dict:
                                            if fiscal_tax_line.tax_src_id.id == (tax_dict[so_line.cust_line_id]).id:
                                                so_line.write({'tax_id': [(6,0,
                                                                           [fiscal_tax_line.tax_dest_id.id])] if fiscal_tax_line else False})

                            self.remove_nill_taxes(sale_order_id)
                            self.write_exceptions(sale_order_id, exceptions_list)
                    else:
                        sale_order_id = self.env["sale.order"].create(sale_order_vals)
                        imported_order_list.append(sale_order_id)
                        count += 1
                        sale_order_id.write({
                            'l10n_in_journal_id': sales_channel.sales_journal_id.id if sales_channel and sales_channel.sales_journal_id else default_journal.id})

                        # sale_order_id.set_order_line()

                        print("tax_dict: ", tax_dict)

                        ''' For loop on order line to apply tax based on the fiscal position
                            searched a tax in fiscal position tax_ids line in Tax on Product to get Tax to Apply.
                        '''
                        for so_line in sale_order_id.order_line:
                            so_line._compute_tax_id()
                            for fiscal_tax_line in sale_order_id.fiscal_position_id.tax_ids:
                                if search_tax:
                                    if fiscal_tax_line.tax_src_id.id == search_tax.id:
                                        so_line.write({'tax_id': [(6, 0,
                                                                   [
                                                                       fiscal_tax_line.tax_dest_id.id])] if fiscal_tax_line else False})

                        self.remove_nill_taxes(sale_order_id)
                        self.write_exceptions(sale_order_id, exceptions_list)
                        self.sale_order_confirm(sale_order_id)
                else:
                    if not amazon_file:
                        search_sale_order.write({'vinculum_status': status})
                        for line_item in sale_order["extra_lines_data"]:
                            search_so_line = self.env["sale.order.line"].search([('cust_line_id', '=', line_item["vinculum_line_line_no"]),
                                                                                 ('order_id', '=', search_sale_order.id)])
                            search_so_line.write({'vinculum_status': line_item["vinculum_line_status"]})
                    else:
                        search_sale_order.write({'amazon_status': status})
                        for line_item in search_sale_order.order_line:
                            search_so_line = self.env["sale.order.line"].search([('item_id', '=', line_item["item_id"]),
                                                                                 ('order_id', '=', search_sale_order.id)])
                            search_so_line.write({'amazon_status': status})

            end_date = datetime.datetime.now()
            if not amazon_file:
                if not self.left_batches:
                    self.last_import_date = end_date
                # To create new record in vinculum import logs
                # company = sales_channel.company_id
                class_id = self
                log_id = self.generate_success_logs(class_id, start_date, end_date, count, operation_performed)[-1]
                for orders in imported_order_list:
                    orders.write({'log_id': log_id.id})
            else:
                operation_performed = 'Sale Order Create & Update(Amazon)'
                wizard_id.shop_instance_id.last_import_date = end_date
                # To create new record in vinculum import logs for amazon files
                # company = wizard_id.shop_instance_id.company_id
                class_id = wizard_id.shop_instance_id
                log_id = self.generate_success_logs(class_id, start_date, end_date, count, operation_performed)[-1]
                for orders in imported_order_list:
                    orders.write({'log_id': log_id.id})
        except Exception as e:
            end_date = datetime.datetime.now()
            if not amazon_file:
                self.last_import_date = end_date
                # To create new record in vinculum import logs
                # company = sales_channel.company_id
                class_id = self
                self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id,operation_performed,e)
            else:
                operation_performed = 'Sale Order Create & Update(Amazon)'
                wizard_id.shop_instance_id.last_import_date = end_date
                # To create new record in vinculum import logs for amazon files
                # company = wizard_id.shop_instance_id.company_id
                class_id = wizard_id.shop_instance_id
                self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id,operation_performed,e)

    ''' Crone for creating sales order by calling import_order() function. '''
    def import_order_crone(self):
        records = self.env['shop.instance'].search([('is_active', '=', True)])
        for rec in records:
            rec.import_order()

    ''' This function will be used for creating orders using ordr number entered in wizard. '''
    def import_order_for_order_number(self, wizard_id):
        opertaion_performed = 'Sale Order Create(Viniculam)'
        print("import_order_for_order_number is working")
        order_pull = self.env.context.get('order_pull', False)
        start_date = datetime.datetime.now()
        company = self.env.company.id

        count = 0
        order_number_id = ''
        try:
            data = order_pull
            for sale_order in data:
                exceptions_list = []
                print("sale_order: ", sale_order)

                ''' To fetch all the values from the vinculum dictionary '''
                order_number_id = sale_order['orderId']
                customer = sale_order['customerName']
                status = sale_order['status']

                ''' To get the shipping address '''
                ship_street = sale_order['shipAddress1']
                ship_street2 = sale_order['shipAddress2']
                ship_city = sale_order['shipCity']
                ship_state = sale_order['shipState']
                ship_country = sale_order['shipCountry']
                ship_zip = sale_order['shipPincode']
                ship_phone = sale_order['shipPhone1']
                ship_email = sale_order['shipEmail1']

                ''' To get the billing address '''
                bill_street = sale_order['billAddress1']
                bill_street2 = sale_order['billAddress2']
                bill_city = sale_order['billCity']
                bill_state = sale_order['billState']
                bill_country = sale_order['billCountry']
                bill_zip = sale_order['billPincode']
                bill_phone = sale_order['billPhone1']
                bill_email = sale_order['billEmail1']
                orderSource = sale_order['orderSource']
                fulfillmentLocCode = sale_order['fulfillmentLocCode']  # this will be seller_id

                customer_gstin = sale_order['customerGSTIN']
                order_date = sale_order['orderDate']

                if customer is None:
                    exceptions_list.append(f"Order NUmber: {order_number_id} ==> Customer is not provided in data.\n")
                if ship_state is None:
                    exceptions_list.append(f"Order NUmber: {order_number_id} ==> Ship state is not provided in data.\n")
                if bill_state is None:
                    exceptions_list.append(f"Order NUmber: {order_number_id} ==> Bill state is not provided in data.\n")
                if orderSource is None:
                    exceptions_list.append(f"Order NUmber: {order_number_id} ==> Order Source is not provided  in "
                                           f"data.\n")
                if fulfillmentLocCode is None:
                    exceptions_list.append(
                        f"Order NUmber: {order_number_id} ==> Fulfillment Loc Code is not define in data.\n")
                if customer_gstin is None:
                    exceptions_list.append(
                        f"Order NUmber: {order_number_id} ==> Customer Gstin is not define in data.\n")

                default_journal = self.env['account.journal'].search([('name', '=', 'Tax Invoices')])
                date_order = datetime.datetime.strptime(str(order_date), "%d/%m/%Y %H:%M:%S")

                fullfillment_code = self.env['seller.merchant'].search([('name', '=', fulfillmentLocCode)])

                orderLocation = sale_order['orderLocation']  # this will be location code
                order_loc = self.env['locations.code'].search([('location_code', '=', orderSource)])

                ''' Condition to check whether order loc is true or not if yes then it will search with all four 
                    condition seller_id, location_code_id, shop_instance_id and company_id.
                    if condition is false then it will only search with seller_id, shop_instance_id and company_id.
                '''
                if not order_loc:
                    sales_channel = self.env['shop.sales.channel'].search([('seller_id', '=', fullfillment_code.id),
                                                                           ('shop_instance_id', '=',
                                                                            wizard_id.shop_instance_id.id if wizard_id else
                                                                            sale_order['for_payment_reconciliation'][
                                                                                'shop_instance_id'].id),
                                                                           ('company_id', '=',
                                                                            wizard_id.company_id.id if wizard_id else company)],
                                                                          limit=1)
                else:
                    sales_channel = self.env['shop.sales.channel'].search([('seller_id', '=', fullfillment_code.id),
                                                                           ('location_code_id', '=', order_loc.id),
                                                                           ('shop_instance_id', '=',
                                                                            wizard_id.shop_instance_id.id if wizard_id else
                                                                            sale_order['for_payment_reconciliation'][
                                                                                'shop_instance_id'].id),
                                                                           ('company_id', '=',
                                                                            wizard_id.company_id.id if wizard_id else company)])

                check_customer_gstin_obj = self.env["shop.instance"].check_customer_gstin(customer_gstin)
                if check_customer_gstin_obj[0] == "company":
                    if customer:
                        contact_obj = self.env["shop.instance"].for_b2b_contact(customer, check_customer_gstin_obj[0],
                                    check_customer_gstin_obj[1], check_customer_gstin_obj[2], bill_street, bill_street2, bill_city,
                                    bill_state, bill_country, bill_zip, bill_phone, bill_email, ship_street,
                                    ship_street2, ship_city, ship_state, ship_country, ship_zip, ship_phone, ship_email)
                if check_customer_gstin_obj[0] == "person":
                    if order_pull and customer == '':
                        customer = wizard_id.shop_instance_id.name if wizard_id else \
                            sale_order['for_payment_reconciliation'][
                                'shop_instance_id'].instance_name + ' - ' + ship_state.upper() + ' - ' + ship_zip
                    contact_obj = self.env["shop.instance"].for_b2c_contact(customer, check_customer_gstin_obj[0],
                                check_customer_gstin_obj[1], check_customer_gstin_obj[2], ship_street, ship_street2, ship_city,
                                ship_state, ship_country, ship_zip, ship_phone, ship_email)

                    ''' To create sale order '''
                    lst = []
                    tax_dict = {}  # list of dictionary
                    i = 0
                    for order_line in sale_order['items']:
                        ''' To fetch all the values from the vinculum dictionary for line level. '''
                        product = order_line['skuName']
                        product_internal_reference = order_line['sku']
                        product_uom = order_line['uom']
                        order_quantity = order_line['orderQty']
                        price_unit = order_line['unitPrice']
                        tax = order_line['taxAmount']
                        discount = order_line['discountAmt']
                        line_no = order_line['lineno']
                        line_status = order_line['status']

                        ''' To search a product '''
                        search_product = self.env["product.product"].search([('name', '=', product),
                                                                             ('default_code', '=',
                                                                              product_internal_reference)])

                        ''' Check is that product exist or not '''
                        if not search_product:
                            is_exception = True
                            if not product_uom:
                                search_uom = self.env["uom.uom"].search([('name', '=', 'Units')])
                            else:
                                search_uom = self.env["uom.uom"].search([('name', '=', product_uom)])
                            product_vals = {
                                'is_exception': True,
                                'name': product,
                                'default_code': product_internal_reference,
                                'uom_id': search_uom.id,
                                'list_price': price_unit,
                                'detailed_type': 'product' if not sales_channel.is_consumable_product else 'consu',
                            }
                            search_product = self.env["product.product"].create(product_vals)
                        else:
                            is_exception = False

                        ''' Check is that product uom exist or not '''
                        if not product_uom:
                            search_uom = self.env["uom.uom"].search([('name', '=', 'Units')])
                        else:
                            search_uom = self.env["uom.uom"].search([('name', '=', product_uom)])

                        if product:
                            if float(order_quantity) > 0:
                                tax_amount = float(tax) / float(order_quantity)
                                discount_per_unit = float(discount) / float(order_quantity)
                            else:
                                tax_amount = 0
                                discount_per_unit = 0
                            unit_price = float(price_unit) - tax_amount

                            if unit_price > 0:
                                discount_in_percentage = discount_per_unit / unit_price * 100
                            else:
                                discount_in_percentage = 0

                            sale_order_line_dict = {
                                'is_exception': is_exception,
                                'product_id': search_product.id,
                                'name': search_product.description[3:-4] if search_product.description else product,
                                'product_uom': search_uom.id,
                                'product_uom_qty': order_quantity,
                                'price_unit': float(price_unit) - tax_amount,
                                'discount': discount_in_percentage,
                                'cust_line_id': line_no,
                                'vinculum_status': line_status,
                            }

                            ''' To store line level data of vinculum api '''
                            sale_order_line_dict.update(sale_order['extra_lines_data'][i])

                            # Condition to check for tax, price_unit and order_quantity for tax calculation
                            # if float(tax) and float(price_unit) and float(order_quantity) > 0:
                            #     search_tax = self.env['shop.instance'].tax_from_fiscal(tax, price_unit, discount,
                            #                                                            order_quantity,
                            #                                                            sales_channel.company_id)
                            #     if not search_product.taxes_id:
                            #         if search_tax:
                            #             search_product.write({'taxes_id': [(4, search_tax.id)]})
                            #     tax_dict[line_no] = search_tax

                            # sale order line values
                            sale_order_line_vals = (0, 0, sale_order_line_dict)
                            lst.append(sale_order_line_vals)

                        # sale order values
                        sale_order_vals = {
                            'name': order_number_id,
                            'is_exception': True if not sales_channel else False,
                            'sales_channel_id': sales_channel.id,
                            'location_id': sales_channel.stock_location_id.id,
                            'date_order': date_order,
                            'partner_id': contact_obj[0].id,
                            'company_id': wizard_id.company_id.id if wizard_id else company,
                            'partner_shipping_id': contact_obj[1].id,
                            'partner_invoice_id': contact_obj[2].id,
                            'shop_instance_id': wizard_id.shop_instance_id.id if wizard_id else
                            sale_order['for_payment_reconciliation']['shop_instance_id'].id,
                            'vinculum_status': status,
                            'vinculum_order_source': orderSource,
                            'vinculum_fullfillment_code': fulfillmentLocCode,
                            'order_line': lst
                        }
                        i += 1

                    ''' To search a sale order '''
                    search_sale_order = self.env["sale.order"].search([('name', '=', order_number_id)])

                    ''' Check is that sale order exist or not '''
                    if not search_sale_order:
                        if orderSource is not None or len(orderSource) != 0:
                            sale_order_id = self.env["sale.order"].create(sale_order_vals)
                            count += 1
                            sale_order_id.write({'l10n_in_journal_id': sales_channel.sales_journal_id.id
                            if sales_channel and sales_channel.sales_journal_id else default_journal.id,
                                                 })
                            # Function call for fiscal position update according to states
                            # sale_order_id.set_order_line()

                            ''' To store header level data of vinculum api '''
                            sale_order_id.write(sale_order['extra_data'])

                            print("tax_dict: ", tax_dict)

                            ''' For loop on order line to apply tax based on the fiscal position
                                searched a tax in fiscal position tax_ids line in Tax on Product to get Tax to Apply.
                            '''

                            for so_line in sale_order_id.order_line:
                                # so_line._compute_tax_id()
                                for fiscal_tax_line in sale_order_id.fiscal_position_id.tax_ids:
                                    if tax_dict:
                                        if fiscal_tax_line.tax_src_id.id == (tax_dict[so_line.cust_line_id]).id:
                                            so_line.write({'tax_id': [(6, 0,
                                                                       [fiscal_tax_line.tax_dest_id.id])] if fiscal_tax_line else False})

                            ''' For loop on order line to get the order lines for this particular order, search tax 
                                which have the amount=0 and remove that id tax from order line
                            '''
                            self.remove_nill_taxes(sale_order_id)
                            self.write_exceptions(sale_order_id, exceptions_list)
                    else:
                        search_sale_order.write({'vinculum_status': status})
                        for line_item in sale_order["extra_lines_data"]:
                            search_so_line = self.env["sale.order.line"].search([('cust_line_id', '=', line_item["vinculum_line_line_no"])])
                            search_so_line.write({'vinculum_status': line_item["vinculum_line_status"]})

            end_date = datetime.datetime.now()
            if not wizard_id:
                sale_order['for_payment_reconciliation']['shop_instance_id'].last_import_date = end_date
                # To create new record in vinculum import logs
                # company = self.company_id
                class_id = self
                self.generate_success_logs(class_id, start_date, end_date, count,opertaion_performed)
            else:
                wizard_id.shop_instance_id.last_import_date = end_date
                # To create new record in vinculum import logs for amazon files
                class_id = wizard_id.shop_instance_id
                self.generate_success_logs(class_id, start_date, end_date, count, opertaion_performed)
        except Exception as e:
            end_date = datetime.datetime.now()
            print("e: ", e)
            if not wizard_id:
                sale_order['for_payment_reconciliation']['shop_instance_id'].last_import_date = end_date
                # To create new record in vinculum import logs
                # company = self.company_id
                class_id = self
                self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id, opertaion_performed, e)
            else:
                wizard_id.shop_instance_id.last_import_date = end_date
                # To create new record in vinculum import logs for amazon files
                # company = wizard_id.shop_instance_id.company_id
                class_id = wizard_id.shop_instance_id
                self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id, opertaion_performed, e)
