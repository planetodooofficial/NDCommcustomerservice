import concurrent
import datetime
import json
from queue import Queue
from odoo import api, fields, models
import requests
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from itertools import islice


class InheritShopInstance(models.Model):
    _inherit = "shop.instance"

    last_import_date_invoice = fields.Datetime(string="Last Import Date Invoice")
    left_batches = fields.Text("Left Batches", readonly=1)
    cust_from_date = fields.Datetime("From Date", readonly=1)
    cust_to_date = fields.Datetime("To Date", readonly=1)

    # last_page_for_so_orders = fields.Integer(string="Last Page For SO Orders", default=1)
    ''' Function to prepare list of orders. '''
    def handle_response(self, future):
        result = json.dumps(future.result())
        result = json.loads(result)
        # handle the API call response here
        list_of_order = []
        print("Orders {} - Page {}".format(len(result['orderList']),result['currentPage']))
        for order in result['orderList']:
            extra_data = {
                "vinculum_order_location": order['orderLocation'],
                "vinculum_order_id": order['orderId'],
                "vinculum_order_no": order['orderNo'],
                "vinculum_external_order_no": order['extenalOrderNo'],
                "vinculum_payment_method": order['paymentMethod'],
                "vinculum_order_date": order['orderDate'],
                "vinculum_order_amount": order['orderAmount'],
                "vinculum_order_currency": order['orderCurrency'],
                "vinculum_conversion_rate": order['conversionRate'],
                "vinculum_customer_name": order['customerName'],
                "vinculum_ship_address1": order['shipAddress1'],
                "vinculum_ship_address2": order['shipAddress2'],
                "vinculum_ship_address3": order['shipAddress3'],
                "vinculum_landmark": order['landmark'],
                "vinculum_latitude": order['latitude'],
                "vinculum_longitude": order['longitude'],
                "vinculum_ship_city": order['shipCity'],
                "vinculum_ship_state": order['shipState'],
                "vinculum_ship_country": order['shipCountry'],
                "vinculum_ship_pincode": order['shipPincode'],
                "vinculum_ship_phone1": order['shipPhone1'],
                "vinculum_ship_phone2": order['shipPhone2'],
                "vinculum_ship_email1": order['shipEmail1'],
                "vinculum_ship_email2": order['shipEmail2'],
                "vinculum_bill_name": order['billName'],
                "vinculum_bill_address1": order['billAddress1'],
                "vinculum_bill_address2": order['billAddress2'],
                "vinculum_bill_address3": order['billAddress3'],
                "vinculum_bill_city": order['billCity'],
                "vinculum_bill_state": order['billState'],
                "vinculum_ill_country": order['billCountry'],
                "vinculum_bill_pincode": order['billPincode'],
                "vinculum_bill_phone1": order['billPhone1'],
                "vinculum_bill_phone2": order['billPhone2'],
                "vinculum_bill_email1": order['billEmail1'],
                "vinculum_bill_email2": order['billEmail2'],
                "vinculum_order_remarks": order['orderRemarks'],
                "vinculum_shipping_charges": order['shippingCharges'],
                "vinculum_handling_charge2": order['handlingCharge2'],
                "vinculum_store_credit": order['storeCredit'],
                "vinculum_is_verified_order": order['isVerifiedOrder'],
                "vinculum_is_on_hold": order['isOnHold'],
                "vinculum_gift_voucher": order['giftvoucher'],
                "vinculum_other_discount": order['otherDiscount'],
                "vinculum_discount_code": order['discountCode'],
                "vinculum_promo_code": order['promoCode'],
                "vinculum_promo_name": order['promoName'],
                "vinculum_cancel_remark": order['cancelRemark'],
                "vinculum_is_gift_wrap": order['isGiftwrap'],
                "vinculum_gift_wrap_msg": order['giftwrapMsg'],
                "vinculum_delivery_slot": order['deliverySlot'],
                "vinculum_custom_data_field1": order['customDataFeld1'],
                "vinculum_custom_data_field2": order['customDataFeld2'],
                "vinculum_custom_data_field3": order['customDataFeld3'],
                "vinculum_custom_data_field4": order['customDataFeld4'],
                "vinculum_custom_data_field5": order['customDataFeld5'],
                "vinculum_custom_data_field6": order['customDataFeld6'],
                "vinculum_custom_data_field7": order['customDataFeld7'],
                "vinculum_custom_data_field8": order['customDataFeld8'],
                "vinculum_custom_data_field9": order['customDataFeld9'],
                "vinculum_custom_data_field10": order['customDataFeld10'],
                "vinculum_discount_amount": order['discountAmount'],
                "vinculum_tax_amount": order['taxAmount'],
                "vinculum_updated_date": order['updatedDate'],
                "vinculum_mode": order['mode'],
                "vinculum_is_replacement_order": order['IsReplacementOrder'],
                "vinculum_original_order_no": order['originalOrderno'],
                "vinculum_customer_code": order['customerCode'],
                "vinculum_ext_customer_code": order['extCustomerCode'],
                "vinculum_client_id": order['clientId'],
                "vinculum_fullfillment_code": order['fulfillmentLocCode'],
                "vinculum_ext_fulfillment_loc_code": order['extFulFillmentLocCode'],
                "vinculum_order_source_name": order['orderSourceName'],
                "vinculum_collective_amount": order['collectibleAmount'],
                "vinculum_total_order_line": order['totalOrderLine'],
                "vinculum_del_fulfillment_mode": order['delFulfillmentMode'],
                "vinculum_geo_type": order['geoType'],
                "vinculum_geo_address": order['geoAddress'],
                "vinculum_geo_latitude": order['geoLatitude'],
                "vinculum_geo_longitude": order['geoLongitude'],
                "vinculum_order_source": order['orderSource'],
                "vinculum_order_type": order['orderType'],
                "vinculum_ship_by_date": order['shipByDate'],
                "vinculum_process_after_date": order['processAfterDate'],
                "vinculum_master_order_no": order['masterorderNo'],
                "vinculum_priority": order['priority'],
                "vinculum_pickup_location": order['pickupLocation'],
                "vinculum_fullfillment_loc_name": order['fulfillmentLocName'],
            }
            extra_lines_data = []
            for line_data in order['items']:
                extra_line_data = {
                    "vinculum_line_line_no": line_data['lineno'],
                    "vinculum_line_ext_line_no": line_data['extLineno'],
                    "vinculum_line_internal_line_no": line_data['internalLineNo'],
                    "vinculum_line_sku": line_data['sku'],
                    "vinculum_line_primary_upc": line_data['primaryUPC'],
                    "vinculum_line_sku_name": line_data['skuName'],
                    "vinculum_line_status": line_data['status'],
                    "vinculum_line_image_url": line_data['imageUrl'],
                    "vinculum_line_uom": line_data['uom'],
                    "vinculum_line_uom_qty": line_data['uomqty'],
                    "vinculum_line_conversion": line_data['conversion'],
                    "vinculum_line_order_qty": line_data['orderQty'],
                    "vinculum_line_commited_qty": line_data['commitedQty'],
                    "vinculum_line_cancelled_qty": line_data['cancelledQty'],
                    "vinculum_line_shipped_qty": line_data['shippedQty'],
                    "vinculum_line_return_qty": line_data['returnQty'],
                    "vinculum_line_unit_price": line_data['unitPrice'],
                    "vinculum_line_discount_amt": line_data['discountAmt'],
                    "vinculum_line_promo_code": line_data['promoCode'],
                    "vinculum_line_promo_name": line_data['promoName'],
                    "vinculum_line_tax_amount": line_data['taxAmount'],
                    "vinculum_line_open_qty": line_data['openQty'],
                    "vinculum_line_udf1": line_data['udf1'],
                    "vinculum_line_udf2": line_data['udf2'],
                    "vinculum_line_udf3": line_data['udf3'],
                    "vinculum_line_udf4": line_data['udf4'],
                    "vinculum_line_udf5": line_data['udf5'],
                    "vinculum_line_udf6": line_data['udf6'],
                    "vinculum_line_udf7": line_data['udf7'],
                    "vinculum_line_udf8": line_data['udf8'],
                    "vinculum_line_udf9": line_data['udf9'],
                    "vinculum_line_udf10": line_data['udf10'],
                    "vinculum_line_bundle_sku_code": line_data['bundleSkuCode'],
                    "vinculum_line_ship_by_date": line_data['shipByDate'],
                    "vinculum_line_fulfillment_loc_code": line_data['fulfillmentLocCode'],
                    "vinculum_line_fulfillment_loc_name": line_data['fulfillmentLocName'],
                }
                extra_lines_data.append(extra_line_data)
            order['extra_data'] = extra_data
            order['extra_lines_data'] = extra_lines_data
            list_of_order.append(order)
        return list_of_order

    ''' Function to fetch pages from api. '''
    def fetch_page(self, url, api_owner, api_key, from_date, to_date):
        # print("fetch total pages")
        url = url
        api_owner = api_owner
        api_key = api_key
        headers = {
            "Content-Type": "application/x-www-form-urlencoded ",
            "Accept": "*/*",
        }
        form_data = {
            "RequestBody": json.dumps({
                "orderNo": "",
                "statuses": [],
                "fromDate": from_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
                "toDate": to_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
                "pageNumber": 1,
                "order_Location": "",
                "IsReplacementOrder": "",
                "orderSource": "",
                "paymentType": [],
                "filterBy": 1,
                "fulfillmentLocation": ""
            }),
            "ApiKey": api_key,
            "ApiOwner": api_owner
        }
        response = requests.post(url, headers=headers, data=form_data).json()
        page_numbers = response["totalPages"]
        # print('Total Orders: {}'.format(response['totalOrders']))
        return page_numbers

    ''' Function to fetch data for all the pages. '''
    def fetch_data(self, url, api_owner, api_key, data):
        # print("fetch total data")
        url = url
        api_owner = api_owner
        api_key = api_key
        headers = {
            "Content-Type": "application/x-www-form-urlencoded ",
            "Accept": "*/*",
            "ApiKey": api_key,
            "ApiOwner": api_owner,
        }
        result = requests.post(url, headers=headers, data=data).json()
        return result

    ''' Function for calling order pull api. '''
    def action_vinculum(self, from_date, to_date):
        print("vinculum action call")
        # s = time.time()
        order_list = []
        url = self.instance_url + "RestWS/api/eretail/v2/order/orderPullV2"
        api_owner = self.instance_username
        api_key = self.instance_password
        pages = self.fetch_page(url=url, api_owner=api_owner, api_key=api_key, from_date=from_date, to_date=to_date)

        def batcher(iterable, batch_size):
            iterator = iter(iterable)
            while batch := list(islice(iterator, batch_size)):
                yield batch

        def my_gen():
            yield from range(1, pages+1)

        batch_list = []
        batch_pages = None
        if not self.left_batches:
            self.cust_from_date = from_date
            self.cust_to_date = to_date
            for batch in batcher(my_gen(), 10):
                batch_list.append(batch)
            batch_pages = batch_list.pop()
            self.write({'left_batches': batch_list})
        else:
            if eval(self.left_batches):
                from_date = self.cust_from_date
                to_date = self.cust_to_date
                left_pages = eval(self.left_batches)
                batch_pages = left_pages.pop()
                # print("batch_pages: ", batch_pages)
                self.write({'left_batches': left_pages})
            else:
                self.write({'left_batches': None})
        # print("batch_list: ", batch_list)

        data_queue = Queue()
        if batch_pages is not None:
            for page in batch_pages:
                form_data = {
                    "RequestBody": json.dumps({
                        "orderNo": "",
                        "statuses": [],
                        "fromDate": from_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
                        "toDate": to_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
                        "pageNumber": page,
                        "order_Location": "",
                        "IsReplacementOrder": "",
                        "orderSource": "",
                        "paymentType": [],
                        "filterBy": 1,
                        "fulfillmentLocation": ""
                    }),
                    "ApiKey": api_key,
                    "ApiOwner": api_owner
                }
                data_queue.put(form_data)
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # use the executor to submit the fetch_page function with the URLs from the queue
                futures = [executor.submit(self.fetch_data, data=data, api_key=api_key, api_owner=api_owner,
                                           url=url) for data in data_queue.queue]
            for future in concurrent.futures.as_completed(futures):
                order_list.extend(self.handle_response(future))
        # print(len(order_list), time.time() - s)
        return order_list
        # page_number = 1
        # headers = {
        #     "Content-Type": "application/x-www-form-urlencoded",
        #     "Accept": "*/*",
        #     "ApiKey": api_key,
        #     "ApiOwner": api_owner,
        # }
        # data = {
        #     "RequestBody": json.dumps({
        #         "orderNo": "",
        #         "statuses": [],
        #         "fromDate": from_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
        #         "toDate": to_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
        #         "pageNumber": page_number,
        #         "order_Location": "",
        #         "IsReplacementOrder": "",
        #         "orderSource": "",
        #         "paymentType": [],
        #         "filterBy": 1,
        #         "fulfillmentLocation": ""
        #     }),
        #     "ApiKey": api_key,
        #     "ApiOwner": api_owner
        # }
        #
        # response = requests.post(url, headers=headers, data=data)
        # orders_count = response.json()['totalOrders']
        # print(orders_count)
        # page_numbers = response.json()["totalPages"]

        # order_list = []
        # for i in range(1, page_numbers + 1):
        #     print("i: ", i)
        #     data = {
        #         "RequestBody": json.dumps({
        #             "orderNo": "",
        #             "statuses": [],
        #             "fromDate": from_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
        #             "toDate": to_date.strftime("%d/%m/%Y").split(" ")[0] + " " + "00:00:00",
        #             "pageNumber": i,
        #             "order_Location": "",
        #             "IsReplacementOrder": "",
        #             "orderSource": "",
        #             "paymentType": [],
        #             "filterBy": 1,
        #             "fulfillmentLocation": ""
        #         }),
        #         "ApiKey": api_key,
        #         "ApiOwner": api_owner
        #     }
        #     response = requests.post(url, headers=headers, data=data).json()
        #     for order in response['orderList']:
        #         extra_data = {
        #             "vinculum_order_location": order['orderLocation'],
        #             "vinculum_order_id": order['orderId'],
        #             "vinculum_order_no": order['orderNo'],
        #             "vinculum_external_order_no": order['extenalOrderNo'],
        #             "vinculum_payment_method": order['paymentMethod'],
        #             "vinculum_order_date": order['orderDate'],
        #             "vinculum_order_amount": order['orderAmount'],
        #             "vinculum_order_currency": order['orderCurrency'],
        #             "vinculum_conversion_rate": order['conversionRate'],
        #             "vinculum_customer_name": order['customerName'],
        #             "vinculum_ship_address1": order['shipAddress1'],
        #             "vinculum_ship_address2": order['shipAddress2'],
        #             "vinculum_ship_address3": order['shipAddress3'],
        #             "vinculum_landmark": order['landmark'],
        #             "vinculum_latitude": order['latitude'],
        #             "vinculum_longitude": order['longitude'],
        #             "vinculum_ship_city": order['shipCity'],
        #             "vinculum_ship_state": order['shipState'],
        #             "vinculum_ship_country": order['shipCountry'],
        #             "vinculum_ship_pincode": order['shipPincode'],
        #             "vinculum_ship_phone1": order['shipPhone1'],
        #             "vinculum_ship_phone2": order['shipPhone2'],
        #             "vinculum_ship_email1": order['shipEmail1'],
        #             "vinculum_ship_email2": order['shipEmail2'],
        #             "vinculum_bill_name": order['billName'],
        #             "vinculum_bill_address1": order['billAddress1'],
        #             "vinculum_bill_address2": order['billAddress2'],
        #             "vinculum_bill_address3": order['billAddress3'],
        #             "vinculum_bill_city": order['billCity'],
        #             "vinculum_bill_state": order['billState'],
        #             "vinculum_ill_country": order['billCountry'],
        #             "vinculum_bill_pincode": order['billPincode'],
        #             "vinculum_bill_phone1": order['billPhone1'],
        #             "vinculum_bill_phone2": order['billPhone2'],
        #             "vinculum_bill_email1": order['billEmail1'],
        #             "vinculum_bill_email2": order['billEmail2'],
        #             "vinculum_order_remarks": order['orderRemarks'],
        #             "vinculum_shipping_charges": order['shippingCharges'],
        #             "vinculum_handling_charge2": order['handlingCharge2'],
        #             "vinculum_store_credit": order['storeCredit'],
        #             "vinculum_is_verified_order": order['isVerifiedOrder'],
        #             "vinculum_is_on_hold": order['isOnHold'],
        #             "vinculum_gift_voucher": order['giftvoucher'],
        #             "vinculum_other_discount": order['otherDiscount'],
        #             "vinculum_discount_code": order['discountCode'],
        #             "vinculum_promo_code": order['promoCode'],
        #             "vinculum_promo_name": order['promoName'],
        #             "vinculum_cancel_remark": order['cancelRemark'],
        #             "vinculum_is_gift_wrap": order['isGiftwrap'],
        #             "vinculum_gift_wrap_msg": order['giftwrapMsg'],
        #             "vinculum_delivery_slot": order['deliverySlot'],
        #             "vinculum_custom_data_field1": order['customDataFeld1'],
        #             "vinculum_custom_data_field2": order['customDataFeld2'],
        #             "vinculum_custom_data_field3": order['customDataFeld3'],
        #             "vinculum_custom_data_field4": order['customDataFeld4'],
        #             "vinculum_custom_data_field5": order['customDataFeld5'],
        #             "vinculum_custom_data_field6": order['customDataFeld6'],
        #             "vinculum_custom_data_field7": order['customDataFeld7'],
        #             "vinculum_custom_data_field8": order['customDataFeld8'],
        #             "vinculum_custom_data_field9": order['customDataFeld9'],
        #             "vinculum_custom_data_field10": order['customDataFeld10'],
        #             "vinculum_discount_amount": order['discountAmount'],
        #             "vinculum_tax_amount": order['taxAmount'],
        #             "vinculum_updated_date": order['updatedDate'],
        #             "vinculum_mode": order['mode'],
        #             "vinculum_is_replacement_order": order['IsReplacementOrder'],
        #             "vinculum_original_order_no": order['originalOrderno'],
        #             "vinculum_customer_code": order['customerCode'],
        #             "vinculum_ext_customer_code": order['extCustomerCode'],
        #             "vinculum_client_id": order['clientId'],
        #             "vinculum_fullfillment_code": order['fulfillmentLocCode'],
        #             "vinculum_ext_fulfillment_loc_code": order['extFulFillmentLocCode'],
        #             "vinculum_order_source_name": order['orderSourceName'],
        #             "vinculum_collective_amount": order['collectibleAmount'],
        #             "vinculum_total_order_line": order['totalOrderLine'],
        #             "vinculum_del_fulfillment_mode": order['delFulfillmentMode'],
        #             "vinculum_geo_type": order['geoType'],
        #             "vinculum_geo_address": order['geoAddress'],
        #             "vinculum_geo_latitude": order['geoLatitude'],
        #             "vinculum_geo_longitude": order['geoLongitude'],
        #             "vinculum_order_source": order['orderSource'],
        #             "vinculum_order_type": order['orderType'],
        #             "vinculum_ship_by_date": order['shipByDate'],
        #             "vinculum_process_after_date": order['processAfterDate'],
        #             "vinculum_master_order_no": order['masterorderNo'],
        #             "vinculum_priority": order['priority'],
        #             "vinculum_pickup_location": order['pickupLocation'],
        #             "vinculum_fullfillment_loc_name": order['fulfillmentLocName'],
        #         }
        #         order['extra_data'] = extra_data
        #         extra_lines_data = []
        #         for line_data in order['items']:
        #             extra_line_data = {
        #                 "vinculum_line_line_no": line_data['lineno'],
        #                 "vinculum_line_ext_line_no": line_data['extLineno'],
        #                 "vinculum_line_internal_line_no": line_data['internalLineNo'],
        #                 "vinculum_line_sku": line_data['sku'],
        #                 "vinculum_line_primary_upc": line_data['primaryUPC'],
        #                 "vinculum_line_sku_name": line_data['skuName'],
        #                 "vinculum_line_status": line_data['status'],
        #                 "vinculum_line_image_url": line_data['imageUrl'],
        #                 "vinculum_line_uom": line_data['uom'],
        #                 "vinculum_line_uom_qty": line_data['uomqty'],
        #                 "vinculum_line_conversion": line_data['conversion'],
        #                 "vinculum_line_order_qty": line_data['orderQty'],
        #                 "vinculum_line_commited_qty": line_data['commitedQty'],
        #                 "vinculum_line_cancelled_qty": line_data['cancelledQty'],
        #                 "vinculum_line_shipped_qty": line_data['shippedQty'],
        #                 "vinculum_line_return_qty": line_data['returnQty'],
        #                 "vinculum_line_unit_price": line_data['unitPrice'],
        #                 "vinculum_line_discount_amt": line_data['discountAmt'],
        #                 "vinculum_line_promo_code": line_data['promoCode'],
        #                 "vinculum_line_promo_name": line_data['promoName'],
        #                 "vinculum_line_tax_amount": line_data['taxAmount'],
        #                 "vinculum_line_open_qty": line_data['openQty'],
        #                 "vinculum_line_udf1": line_data['udf1'],
        #                 "vinculum_line_udf2": line_data['udf2'],
        #                 "vinculum_line_udf3": line_data['udf3'],
        #                 "vinculum_line_udf4": line_data['udf4'],
        #                 "vinculum_line_udf5": line_data['udf5'],
        #                 "vinculum_line_udf6": line_data['udf6'],
        #                 "vinculum_line_udf7": line_data['udf7'],
        #                 "vinculum_line_udf8": line_data['udf8'],
        #                 "vinculum_line_udf9": line_data['udf9'],
        #                 "vinculum_line_udf10": line_data['udf10'],
        #                 "vinculum_line_bundle_sku_code": line_data['bundleSkuCode'],
        #                 "vinculum_line_ship_by_date": line_data['shipByDate'],
        #                 "vinculum_line_fulfillment_loc_code": line_data['fulfillmentLocCode'],
        #                 "vinculum_line_fulfillment_loc_name": line_data['fulfillmentLocName'],
        #             }
        #             extra_lines_data.append(extra_line_data)
        #         order['extra_lines_data'] = extra_lines_data
        #         order_list.append(order)
        # return order_list

    ''' Function for calling invoice api. '''

    def action_update_invoice(self, sale_order):
        print("action_update_invoice")
        url = self.instance_url + "RestWS/api/eretail/v1/order/orderinvoicepdf"
        api_owner = self.instance_username
        api_key = self.instance_password

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "ApiKey": api_key,
            "ApiOwner": api_owner,
        }
        data = {
            "RequestBody": json.dumps({
                "WebOrderNo": [sale_order.vinculum_order_no],
                "invoiceno": "",
                "AWB_No": ""
            }),
            "ApiKey": api_key,
            "ApiOwner": api_owner
        }
        try:
            response = requests.post(url, headers=headers, data=data)

            invoice_order_list = []
            if response.json() and 'OrderInvoiceDetails' in response.json():
                for invoice_order in response.json()['OrderInvoiceDetails']:
                    # print("invoice_order: ", invoice_order)
                    invoice_order_list.append(invoice_order)
            return invoice_order_list
        except Exception as e:
            pass

    ''' Function for calling invoice api based on order no,
        updating the invoice number in sale order's custom invoice number field and in invoice's payment reference field
        and attach pdf's in invoices
    '''

    def update_invoice(self):
        start_date = datetime.datetime.now()
        operation_performed = 'Invoice Update(Vinculum)'
        if self.last_import_date_invoice:
            from_date = self.last_import_date_invoice - datetime.timedelta(days=7)
        else:
            current_date = datetime.date.today()
            from_date = ((current_date - relativedelta(days=7)))

        if self.last_import_date_invoice:
            to_date = self.last_import_date_invoice.strftime("%d/%m/%Y")[:10]
        else:
            to_date = datetime.date.today().strftime("%d/%m/%Y")

        count = 0
        order_number_id = ''
        try:
            imported_order_list = []
            for instance in self:
                # print("instance", instance)
                search_sale_order = self.env["sale.order"].search([("shop_instance_id", '=', instance.id),
                                                                   ('vinculum_status', 'in',
                                                                    ["Shipped & Returned", "Closed", "Delivered",
                                                                     "Shipped Complete"]
                                                                    )])
                if len(search_sale_order) > 0:
                    for sale_order in search_sale_order[:100]:
                        # print("sale_order", sale_order)
                        update_invoice_data = getattr(self, "action_update_invoice")(sale_order)
                        for invoice in update_invoice_data:
                            # print("invoice: ", invoice)
                            order_no = invoice['WebOrderNo']
                            invoice_no = invoice['InvoiceNo']
                            invoice_stream = invoice['InvoiceStream']

                            search_order = self.env["sale.order"].search([('vinculum_order_no', '=', order_no)])
                            order_number_id = search_order.name
                            search_invoice = self.env["account.move"].search(
                                [('invoice_origin', '=', search_order.name)])
                            # print("invoice_stream: ", invoice_stream)

                            if search_invoice:
                                imported_order_list.append(sale_order)
                                count += 1
                                search_order.write({'cust_invoice_number': invoice_no})
                                for inv in search_invoice:
                                    inv.write({'payment_reference': invoice_no})
                                    ir_attachment_obj = self.env['ir.attachment']
                                    search_ir_attachment = ir_attachment_obj.search([('name', '=', invoice_no)])
                                    if not search_ir_attachment:
                                        attachment_id = ir_attachment_obj.create({
                                            'name': f'{invoice_no}',
                                            'type': 'binary',
                                            'datas': invoice_stream.encode('ascii'),
                                            'res_model': 'account.move',
                                            'res_id': inv.id,
                                            'mimetype': 'application/x-pdf'
                                        })

            end_date = datetime.datetime.now()
            self.last_import_date_invoice = end_date
            # To create new record in vinculum import logs
            class_id = self
            self.generate_success_logs(class_id, start_date, end_date, count, operation_performed)
            print(count)
            print(len(imported_order_list))
            for orders in imported_order_list:
                orders.write({'invoice_log_id':  self.shop_import_logs_ids[-1].id})
        except Exception as e:
            end_date = datetime.datetime.now()
            self.last_import_date_invoice = end_date
            # To create new record in vinculum import logs
            class_id = self
            self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id, operation_performed, e)

    ''' This crone will be used for calling update_invoice() function to update the invoice number. '''

    def update_invoice_crone(self):
        records = self.env['shop.instance'].search([('is_active', '=', True)])
        for rec in records:
            rec.update_invoice()

    ''' This crone will be used to update the sale order and based on the vinculum status it will confirm,
        create delivery, create invoice, create return for delivery, create credit note.
    '''

    def update_sale_order_crone(self):
        print("Update Sale Orders")
        shop_instance_records = self.env['shop.instance'].search([('is_active', '=', True)])
        operation_performed = 'Sale Order Update(Vinculum)'
        order_number_id = ''
        start_date = datetime.datetime.now()

        ''' For loop on all the active shop instances '''

        for instance in shop_instance_records:
            updated_sale_orders = []
            ''' search sale orders where state is draft, shop instance is active shop instance and vinculum status '''
            sale_order_records = self.env['sale.order'].search([('state', '=', 'draft'),
                                                                ('shop_instance_id', '=', instance.id),
                                                                ('vinculum_status', 'in',
                                                                 ["Shipped & Returned", "Closed", "Delivered",
                                                                  "Shipped complete"])])
            # print(f"sale_order_records for {instance.instance_name}: ", sale_order_records)
            count = 0
            try:
                if len(sale_order_records) > 0:
                    for sale_order in sale_order_records[:100]:
                        order_number_id = sale_order.name
                        print(order_number_id)
                        ''' To check the number of orderlines present in particular order, if the orderline status is 
                        shipped & returned then it will seperate it in other list, if the total orderlines is equal to 
                        shipped & retruned orderlines and so vin status is same then it will create credit note for whole
                        order else it will create credit note for that particular order line only. '''
                        total_order_line = len(sale_order.order_line)
                        order_line_sr_list = []
                        # line_item_to_confirm = []
                        for line_item in sale_order.order_line:
                            if line_item.vinculum_status == "Shipped & Returned":
                                order_line_sr_list.append(line_item)
                            # if line_item.vinculum_status == sale_order.vinculum_status:
                            #     line_item_to_confirm.append(line_item.id)

                        # sale_order.write({'order_line': [(6,0,line_item_to_confirm)]})

                        self.env["shop.instance"].sale_order_confirm(sale_order)
                        updated_sale_orders.append(sale_order)
                        count += 1
                        if total_order_line == order_line_sr_list and sale_order.vinculum_status == "Shipped & Returned":
                            self.env["shop.instance"].order_credit_note(sale_order)
                        else:
                            if total_order_line != len(order_line_sr_list) and len(order_line_sr_list) > 0:
                                stock_move_list = []
                                for line in order_line_sr_list:
                                    # print("line.sale_line_id: ", line.sale_line_id)
                                    search_stock_move = self.env["stock.move"].search([('sale_line_id', '=', line.id)])
                                    stock_move_list.append(search_stock_move)

                                # print("stock_move_list: ", stock_move_list)
                                search_delivery = self.env["stock.picking"].search([('origin', '=', sale_order.name)])
                                stock_return_picking_obj = self.env["stock.return.picking"]
                                lst = []
                                for delivery in search_delivery:
                                    # print("delivery: ", delivery)
                                    for move_id_package in stock_move_list:
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
                                    search_reverse_delivery = self.env["stock.picking"].search(
                                        [('origin', '=', f'Return of {delivery.name}')])
                                    search_reverse_delivery.action_set_quantities_to_reservation()
                                    search_reverse_delivery.button_validate()

                                    search_invoice = self.env["account.move"].search(
                                        [('invoice_origin', '=', sale_order.name),
                                         ('move_type', '=', 'out_invoice')])

                                    lst1 = []
                                    for line in order_line_sr_list:
                                        search_invoice_line = self.env["account.move.line"].search(
                                            [('sale_line_ids', 'in', line.id)])
                                        credit_note_line_vals = (0, 0, {
                                            'product_id': search_invoice_line.product_id.id,
                                            'name': search_invoice_line.name,
                                            'account_id': search_invoice_line.account_id.id,
                                            'quantity': search_invoice_line.quantity,
                                            'product_uom_id': search_invoice_line.product_uom_id.id,
                                            'price_unit': search_invoice_line.price_unit,
                                            'hsn_id': search_invoice_line.hsn_id.id,
                                            'tax_ids': [(4, search_invoice_line.tax_ids.id)],
                                            'sale_line_ids': [(4, line.id)],
                                        })
                                        lst1.append(credit_note_line_vals)
                                    credit_note_vals = {
                                        'move_type': 'out_refund',
                                        'partner_id': search_invoice.partner_id.id,
                                        'l10n_in_gst_treatment': search_invoice.l10n_in_gst_treatment,
                                        'invoice_date': search_invoice.invoice_date,
                                        'invoice_date_due': search_invoice.invoice_date_due,
                                        'journal_id': search_invoice.journal_id.id,
                                        'dispatch_partner_id': search_invoice.dispatch_partner_id.id,
                                        'fiscal_position_id': search_invoice.fiscal_position_id.id,
                                        'company_id': search_invoice.company_id.id,
                                        'invoice_line_ids': lst1
                                    }
                                    credit_note_id = search_invoice.create(credit_note_vals)
                                    credit_note_id.action_post()
                class_id = instance
                end_date = datetime.datetime.now()
                update_log_id = self.generate_success_logs(class_id, start_date, end_date, count, operation_performed)[-1]
                for order in updated_sale_orders:
                    order.write({'order_update_log': update_log_id.id})
            except Exception as e:
                end_date = datetime.datetime.now()
                class_id = instance
                self.generate_exception_logs(class_id, start_date, count, end_date, order_number_id,
                                             operation_performed, e)
