from odoo import models, fields, api, _

class AssetTags(models.Model):
    _name = 'asset.tag'

    name = fields.Char("Name")


class AssetType(models.Model):
    _name = 'asset.type'

    name = fields.Char("Name")
