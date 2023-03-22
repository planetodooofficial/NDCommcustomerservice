from odoo import api, fields, models, _
import pandas as pd
import base64
from io import BytesIO
from datetime import datetime
from collections import Counter


class BulkRtoWizard(models.TransientModel):
    _name = "bulk.rto.wizard"
    _description = "Bulk Rto"

    upload_file = fields.Binary("Upload File")
    company_id = fields.Many2one("res.company", "Company", readonly=True, default=lambda self: self.env.company.id)
    rto_mail_ids = fields.One2many('rtorder.mail', 'orders', string='RTO Mail')

    def action_bulk_rto(self):
        filename = BytesIO(base64.b64decode(self.upload_file))
        data = pd.read_excel(filename).fillna(False).to_dict('index').values()
        print(data)

        order_name = []
        lst = []
        count = 0
        #
        cr = list(map(lambda a: a['carrier'], data))
        ord = list(map(lambda a: a['name'], data))

        carriers = list(set(cr))
        print('Print Carriers : ', carriers)

        cr_dic = {}

        # To get order numbers carrier wise
        for order in data:
            if order['carrier'] not in cr_dic:
                cr_dic[order['carrier']] = set([order['name']])
            else:
                cr_dic[order['carrier']].add(order['name'])

        # print('Cr Dic :', cr_dic)

        for keys, values in cr_dic.items():
            print(keys, values)
            delivery_carrier_id = self.env['delivery.carrier'].search([('name', '=', keys)])
            data_vals = {
                'carrier': delivery_carrier_id.id,
                'count': len(values),
                'orders1': ",".join(values),
                'spoc': delivery_carrier_id.spoc
            }
            print(values)
            for i in values:
                order_name.append(i)

                for j in order_name:
                    sale_order_search = self.env['sale.order'].search([('name', '=', j)])
                    if sale_order_search:
                        sale_order_search.write({'custom_state': "rto_requested"})


            # update email by carrier id

            vals = (0, 0, data_vals)
            lst.append(vals)
        _id = self.env['bulk.rto.wizard'].create({'upload_file': self.upload_file,
                                                  'rto_mail_ids': lst})
        print(order_name)

        return {
            'name': _("Rto Mail"),
            'view_mode': 'form',
            'res_model': 'bulk.rto.wizard',
            'res_id': _id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    #for sending mail to receipents for RTO
    def call_mail(self):
        template = self.env.ref('customer_service.email_template')
        body_content = u"Here is details of RTO orders <br/> Placing RTO request for Order No "
        count = 0
        for rec in self.rto_mail_ids:

            items = rec.orders1.split(",")
            print('ITEMS',items)
            # lst_items = ["\n <li>{}</li>".format(s) for s in items]
            # print(lst_items)
            body_content2 = f""" """
            for i in items:
                count += 1
                body_content2 += f"""  <tr><td style="width: 10%">{count}</td>
                <td>{i}</td>
                </tr>"""

            print(body_content2)

            # data = pd.DataFrame({'SR No': [count],
            #                      'ORDERS': [rec.orders1],
            #                      })
            # s = data.style.set_properties(
            #     **{'border': '1px black solid black !important', 'font-size': '9pt'}).set_table_attributes(
            #     'style="border-collapse:collapse"').set_table_styles([{
            #     'selector': '.col_heading',
            #     'props': 'background-color: white; font-size:9pt; color: black; border-collapse: collapse; border: 1px black solid !important;'
            # }])
            #
            # output = s.hide(axis='index').to_html()

            email_values = {'subject': "Details of Rto orders",
                            'email_from': self.env.company.email,
                            'email_to': rec.spoc,
                            'body_html': body_content +

                             f"""
                                
                                <html><body>
                                <div style="display:table;">
                                    <div style="display:table-header-group;">
                                        <div style="display:table-row;">
                                            <div style="display:table-cell;">SR NO</div>
                                            <div style="display:table-cell;">ORDERS</div>
                                        </div>
                                    </div>
                                               
                                    <table>
                                            {body_content2}
                                    
                                    </table>
                                </div>
                                
                              
                                </body></html>
                                """
                            }


            template.send_mail(rec.id, force_send=True, email_values=email_values)


class RtoOrdermail(models.Model):
    _name = "rtorder.mail"
    _description = "Rto Email"

    carrier = fields.Many2one('delivery.carrier', 'Carrier')
    count = fields.Integer('Count')
    spoc = fields.Char('Email')
    orders = fields.Char('Order name')
    orders1 = fields.Char('Order name')
    is_active = fields.Boolean('')
