from odoo import api, fields, models


class StateConfigWizard(models.TransientModel):
    _name = "state.config.wizard"
    _description = "State Config Wizard"

    old_state_id = fields.Many2one("res.country.state", "Old State")
    new_state_id = fields.Many2one("res.country.state", "New State")

    def old_state_replace(self):
        search_partner = self.env["res.partner"].search([('state_id', '=', self.new_state_id.id)])
        for partner in search_partner:
            partner.write({'state_id': self.old_state_id.id})

