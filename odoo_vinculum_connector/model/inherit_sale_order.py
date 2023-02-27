from odoo import api, fields, models


class SalesOrderInheritVIN(models.Model):
    _inherit = "sale.order"

    vinculum_status = fields.Selection([('Confirmed', 'Confirmed'),
                                        ('Allocated', 'Allocated'),
                                        ('Cancelled', 'Cancelled'),
                                        ('Closed', 'Closed'),
                                        ('Delivered', 'Delivered'),
                                        ('Delivery created', 'Delivery Created'),
                                        ('Packed', 'Packed'),
                                        ('Part Allocated', 'Part Allocated'),
                                        ('Part Picked', 'Part Picked'),
                                        ('Partially Shipped', 'Partially Shipped'),
                                        ('Pending', 'Pending'),
                                        ('Pick complete', 'Pick Complete'),
                                        ('Shipped & Returned', 'Shipped & Returned'),
                                        ('Shipped complete', 'Shipped Complete'),
                                        ('In process', 'In process'),
                                        ], readonly=True)
    vinculum_order_source = fields.Char("Order Source", readonly=True)
    vinculum_fullfillment_code = fields.Char("Fullfillment Code", readonly=True)
    vinculum_order_location = fields.Char("Order Location", readonly=True)
    vinculum_order_id = fields.Char("Order ID", readonly=True)
    vinculum_order_no = fields.Char("Order No", readonly=True)
    vinculum_external_order_no = fields.Char("External Order No", readonly=True)
    vinculum_payment_method = fields.Char("Payment Method", readonly=True)
    vinculum_order_date = fields.Char("Order Date", readonly=True)
    vinculum_order_amount = fields.Char("Order Amount", readonly=True)
    vinculum_order_currency = fields.Char("Order Currency", readonly=True)
    vinculum_conversion_rate = fields.Char("Conversion Rate", readonly=True)
    vinculum_customer_name = fields.Char("Customer Name", readonly=True)
    vinculum_ship_address1 = fields.Char("Ship Address1", readonly=True)
    vinculum_ship_address2 = fields.Char("Ship Address2", readonly=True)
    vinculum_ship_address3 = fields.Char("Ship Address3", readonly=True)
    vinculum_landmark = fields.Char("Landmark", readonly=True)
    vinculum_latitude = fields.Char("Latitude", readonly=True)
    vinculum_longitude = fields.Char("Longitude", readonly=True)
    vinculum_ship_city = fields.Char("Ship City", readonly=True)
    vinculum_ship_state = fields.Char("Ship State", readonly=True)
    vinculum_ship_country = fields.Char("Ship Country", readonly=True)
    vinculum_ship_pincode = fields.Char("Ship Pincode", readonly=True)
    vinculum_ship_phone1 = fields.Char("Ship Phone1", readonly=True)
    vinculum_ship_phone2 = fields.Char("Ship Phone2", readonly=True)
    vinculum_ship_email1 = fields.Char("Ship Email1", readonly=True)
    vinculum_ship_email2 = fields.Char("Ship Email2", readonly=True)
    vinculum_bill_name = fields.Char("Bill Name", readonly=True)
    vinculum_bill_address1 = fields.Char("Bill Address1", readonly=True)
    vinculum_bill_address2 = fields.Char("Bill Address2", readonly=True)
    vinculum_bill_address3 = fields.Char("Bill Address3", readonly=True)
    vinculum_bill_city = fields.Char("Bill City", readonly=True)
    vinculum_bill_state = fields.Char("Bill State", readonly=True)
    vinculum_ill_country = fields.Char("Bill Country", readonly=True)
    vinculum_bill_pincode = fields.Char("Bill Pincode", readonly=True)
    vinculum_bill_phone1 = fields.Char("Bill Phone1", readonly=True)
    vinculum_bill_phone2 = fields.Char("Bill Phone2", readonly=True)
    vinculum_bill_email1 = fields.Char("Bill Email1", readonly=True)
    vinculum_bill_email2 = fields.Char("Bill Email2", readonly=True)
    vinculum_order_remarks = fields.Char("Order Remarks", readonly=True)
    vinculum_shipping_charges = fields.Char("Shipping Charges", readonly=True)
    vinculum_handling_charge2 = fields.Char("Handling Charge2", readonly=True)
    vinculum_store_credit = fields.Char("Store Credit", readonly=True)
    vinculum_is_verified_order = fields.Char("Is Verified Order", readonly=True)
    vinculum_is_on_hold = fields.Char("Is On Hold", readonly=True)
    vinculum_gift_voucher = fields.Char("Gift Voucher", readonly=True)
    vinculum_other_discount = fields.Char("Other Discount", readonly=True)
    vinculum_discount_code = fields.Char("Discount Code", readonly=True)
    vinculum_promo_code = fields.Char("Promo Code", readonly=True)
    vinculum_promo_name = fields.Char("Promo Name", readonly=True)
    vinculum_cancel_remark = fields.Char("Cancel Remark", readonly=True)
    vinculum_is_gift_wrap = fields.Char("Is Gift Wrap", readonly=True)
    vinculum_gift_wrap_msg = fields.Char("Gift Wrap Msg", readonly=True)
    vinculum_delivery_slot = fields.Char("Delivery Slot", readonly=True)
    vinculum_custom_data_field1 = fields.Char("Custom Data Feld1", readonly=True)
    vinculum_custom_data_field2 = fields.Char("Custom Data Feld2", readonly=True)
    vinculum_custom_data_field3 = fields.Char("Custom Data Feld3", readonly=True)
    vinculum_custom_data_field4 = fields.Char("Custom Data Feld4", readonly=True)
    vinculum_custom_data_field5 = fields.Char("Custom Data Feld5", readonly=True)
    vinculum_custom_data_field6 = fields.Char("Custom Data Feld6", readonly=True)
    vinculum_custom_data_field7 = fields.Char("Custom Data Feld7", readonly=True)
    vinculum_custom_data_field8 = fields.Char("Custom Data Feld8", readonly=True)
    vinculum_custom_data_field9 = fields.Char("Custom Data Feld9", readonly=True)
    vinculum_custom_data_field10 = fields.Char("Custom Data Feld10", readonly=True)
    vinculum_discount_amount = fields.Char("Discount Amount", readonly=True)
    vinculum_tax_amount = fields.Char("Tax Amount", readonly=True)
    vinculum_updated_date = fields.Char("Updated Date", readonly=True)
    vinculum_mode = fields.Char("Mode", readonly=True)
    vinculum_is_replacement_order = fields.Char("Is Replacement Order", readonly=True)
    vinculum_original_order_no = fields.Char("Original Order No", readonly=True)
    vinculum_customer_code = fields.Char("Customer Code", readonly=True)
    vinculum_ext_customer_code = fields.Char("Ext Customer Code", readonly=True)
    vinculum_client_id = fields.Char("Client Id", readonly=True)
    vinculum_ext_fulfillment_loc_code = fields.Char("Ext Fulfillment Loc Code", readonly=True)
    vinculum_order_source_name = fields.Char("Order Source Name", readonly=True)
    vinculum_collective_amount = fields.Char("Collectible Amount", readonly=True)
    vinculum_total_order_line = fields.Char("Total Order Line", readonly=True)
    vinculum_del_fulfillment_mode = fields.Char("Del Fulfillment Mode", readonly=True)
    vinculum_geo_type = fields.Char("Geo Type", readonly=True)
    vinculum_geo_address = fields.Char("Geo Address", readonly=True)
    vinculum_geo_latitude = fields.Char("Geo Latitude", readonly=True)
    vinculum_geo_longitude = fields.Char("Geo Longitude", readonly=True)
    vinculum_order_type = fields.Char("Order Type", readonly=True)
    vinculum_ship_by_date = fields.Char("Ship By Date", readonly=True)
    vinculum_process_after_date = fields.Char("Process After Date", readonly=True)
    vinculum_master_order_no = fields.Char("Master Order No", readonly=True)
    vinculum_priority = fields.Char("Priority", readonly=True)
    vinculum_pickup_location = fields.Char("Pickup Location", readonly=True)
    vinculum_fullfillment_loc_name = fields.Char("Fulfillment Loc Name", readonly=True)

    cust_invoice_number = fields.Char(string="Invoice Number", readonly=True)


class InheritResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        # with_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.is_vat)
        return super(InheritResPartner)


class SalesOrderLineInheritVIN(models.Model):
    _inherit = "sale.order.line"

    vinculum_status = fields.Selection([('Confirmed', 'Confirmed'),
                                        ('Allocated', 'Allocated'),
                                        ('Cancelled', 'Cancelled'),
                                        ('Closed', 'Closed'),
                                        ('Delivered', 'Delivered'),
                                        ('Delivery created', 'Delivery Created'),
                                        ('Packed', 'Packed'),
                                        ('Part Allocated', 'Part Allocated'),
                                        ('Part Picked', 'Part Picked'),
                                        ('Partially Shipped', 'Partially Shipped'),
                                        ('Pending', 'Pending'),
                                        ('Pick complete', 'Pick Complete'),
                                        ('Shipped & Returned', 'Shipped & Returned'),
                                        ('Shipped complete', 'Shipped Complete'),
                                        ('In process', 'In process'),
                                        ], readonly=True)
    tracking_number = fields.Char("Tracking Number", readonly=True)
    cust_line_id = fields.Char("Line ID", readonly=True)
    show_vinculum_line_data = fields.Boolean(string="Show Vinculum Line Data")
    cust_journal_id = fields.Many2one("account.journal", "Journal")
    shop_instance_id = fields.Many2one("shop.instance", "Shop Instance", related="order_id.shop_instance_id")

    vinculum_line_line_no = fields.Char("Line No", readonly=True)
    vinculum_line_ext_line_no = fields.Char("Ext Line No", readonly=True)
    vinculum_line_internal_line_no = fields.Char("Internal Line No", readonly=True)
    vinculum_line_sku = fields.Char("Sku", readonly=True)
    vinculum_line_primary_upc = fields.Char("Primary UPC", readonly=True)
    vinculum_line_sku_name = fields.Char("Sku Name", readonly=True)
    vinculum_line_status = fields.Char("Status", readonly=True)
    vinculum_line_image_url = fields.Char("Image Url", readonly=True)
    vinculum_line_uom = fields.Char("Uom", readonly=True)
    vinculum_line_uom_qty = fields.Char("Uom Qty", readonly=True)
    vinculum_line_conversion = fields.Char("Conversion", readonly=True)
    vinculum_line_order_qty = fields.Char("Order Qty", readonly=True)
    vinculum_line_commited_qty = fields.Char("Commited Qty", readonly=True)
    vinculum_line_cancelled_qty = fields.Char("Cancelled Qty", readonly=True)
    vinculum_line_shipped_qty = fields.Char("Shipped Qty", readonly=True)
    vinculum_line_return_qty = fields.Char("Return Qty", readonly=True)
    vinculum_line_unit_price = fields.Char("Unit Price", readonly=True)
    vinculum_line_discount_amt = fields.Char("Discount Amt", readonly=True)
    vinculum_line_promo_code = fields.Char("Promo Code", readonly=True)
    vinculum_line_promo_name = fields.Char("Promo Name", readonly=True)
    vinculum_line_tax_amount = fields.Char("Tax Amount", readonly=True)
    vinculum_line_open_qty = fields.Char("Open Qty", readonly=True)
    vinculum_line_udf1 = fields.Char("Udf1", readonly=True)
    vinculum_line_udf2 = fields.Char("Udf2", readonly=True)
    vinculum_line_udf3 = fields.Char("Udf3", readonly=True)
    vinculum_line_udf4 = fields.Char("Udf4", readonly=True)
    vinculum_line_udf5 = fields.Char("Udf5", readonly=True)
    vinculum_line_udf6 = fields.Char("Udf6", readonly=True)
    vinculum_line_udf7 = fields.Char("Udf7", readonly=True)
    vinculum_line_udf8 = fields.Char("Udf8", readonly=True)
    vinculum_line_udf9 = fields.Char("Udf9", readonly=True)
    vinculum_line_udf10 = fields.Char("Udf10", readonly=True)
    vinculum_line_bundle_sku_code = fields.Char("Bundle Sku Code", readonly=True)
    vinculum_line_ship_by_date = fields.Char("Ship By Date", readonly=True)
    vinculum_line_fulfillment_loc_code = fields.Char("Fulfillment Loc Code", readonly=True)
    vinculum_line_fulfillment_loc_name = fields.Char("Fulfillment Loc Name", readonly=True)