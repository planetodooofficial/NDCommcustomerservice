from odoo import models, fields, api, _

class AccountAssetInherit(models.Model):
    _inherit = 'account.asset'

    name = fields.Char(string='Asset Name', compute='_compute_name', store=True,readonly=True,tracking=True)
    asset_tags = fields.Many2many('asset.tag','asset_tag_rel',string="Tags")
    asset_types = fields.Many2one('asset.type',"Type")
    equipment_id = fields.Many2one('maintenance.equipment',"Equipment")
    employee_id = fields.Many2one('hr.employee',"Employee")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('account.asset.po')
        return super(AccountAssetInherit, self).create(vals_list)