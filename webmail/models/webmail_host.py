# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class WebmailHost(models.Model):
    _name = "webmail.host"
    _description = "Webmail Hosts"

    name = fields.Char(required=True)

    url = fields.Char(required=True)
