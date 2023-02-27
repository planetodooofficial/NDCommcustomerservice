
{
  "name"                 :  "GSTR Reconciliation",
  "summary"              :  """Odoo GST - Returns and Invoices Reconciliation""",
  "category"             :  "Accounting",
  "version"              :  "3.0.0",
  "sequence"             :  1,
  "author"               :  "Planet Odoo",
  "website"              :  "https://planet-odoo.com/",
  "description"          :  """GSTR Invoices Reconciliation

Goods and Services Tax Reconciliation in Odoo""",
  "depends"              :  ['base','account','gst_invoice_v16'],
  "data"                 :  [
    'security/ir.model.access.csv',
    'wizard/upload_reco_file.xml',
    'views/gstr_reco_view.xml',
  ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,

}
