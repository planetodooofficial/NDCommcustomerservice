import base64
import json
from tempfile import TemporaryFile
import openpyxl
import requests

from odoo import api, fields, models


class ImportOrderVinculumFilesWizard(models.TransientModel):
    _name = "import.order.vinculum.files.wizard"
    _description = "Import Order Vinculum Files Wizard"

    shop_instance_id = fields.Many2one("shop.instance", string="Shop Instance")
    sales_channel_id = fields.Many2one("shop.sales.channel", string="Shop Sales Channel")
    order_number = fields.Text("Enter Order Number(s)")
    company_id = fields.Many2one("res.company", "Company", readonly=True, default=lambda self: self.env.company.id)

    @api.onchange('shop_instance_id')
    def onchange_shop_instance_id(self):
        # print("onchange_shop_instance_id", self.shop_instance_id)
        return {'domain': {'sales_channel_id': [('shop_instance_id', '=', self.shop_instance_id.id)]}}

    ''' This function is used to call vinculum api for order numbers entered in wizard (sale order action) to 
        create orders in system.
    '''
    def action_import_order_vinculum(self):
        print("action_import_order_vinculum is working")
        print("self.order_number.split(" "): ", self.order_number.split('\n'))
        url = self.shop_instance_id.instance_url + "RestWS/api/eretail/v2/order/orderPullV2"
        api_owner = self.shop_instance_id.instance_username
        api_key = self.shop_instance_id.instance_password

        order_list = []
        for order_number in self.order_number.split('\n'):
            print("order_number: ", order_number)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
                "ApiKey": api_key,
                "ApiOwner": api_owner,
            }
            data = {
                "RequestBody": json.dumps({
                    "orderNo": f"{order_number}",
                    "statuses": [],
                    "fromDate": "",
                    "toDate": "",
                    "pageNumber": 1,
                    "order_Location": "",
                    "IsReplacementOrder": "",
                    "orderSource": f"{self.sales_channel_id.location_code_id.location_code}",
                    "paymentType": [],
                    "filterBy": 1,
                    "fulfillmentLocation": ""
                }),
                "ApiKey": api_key,
                "ApiOwner": api_owner
            }
            response = requests.post(url, headers=headers, data=data)
            for order in response.json()['orderList']:
                print(order)
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
                order_list.append(order)
        self.env['shop.instance'].with_context(order_pull=order_list).import_order_for_order_number(wizard_id=self)
        return True