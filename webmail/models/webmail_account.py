# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re

from odoo import api, fields, models


class WebmailAccount(models.Model):
    _name = "webmail.account"
    _description = "Webmail Accounts"
    _rec_name = "login"

    url = fields.Char(required=True)

    login = fields.Char(required=True)

    password = fields.Char(required=True)

    user_id = fields.Many2one(comodel_name="res.users", required=True)

    folder_ids = fields.One2many(
        comodel_name="webmail.folder",
        inverse_name="account_id",
        readonly=True,
    )

    folder_qty = fields.Integer(
        string="Folders", compute="_compute_folder_qty", store=True
    )

    mail_qty = fields.Integer(string="Mails", compute="_compute_mail_qty", store=True)

    # Compute Section
    @api.depends("folder_ids")
    def _compute_folder_qty(self):
        for account in self:
            account.folder_qty = len(account.folder_ids)

    @api.depends("folder_ids.mail_qty")
    def _compute_mail_qty(self):
        for account in self:
            account.mail_qty = sum(account.mapped("folder_ids.mail_qty"))

    # Action Section
    def button_test_connexion(self):
        self.env["imap.proxy"].test_connexion(self)

    def button_fetch_folders(self):
        self._fetch_folders()

    def button_fetch_mails(self):
        for folder in self.mapped("folder_ids"):
            folder.button_fetch_mails()

    # Private Section
    @api.model
    def _fetch_folders(self):
        WebmailFolder = self.env["webmail.folder"]
        _status, folder_datas = self.env["imap.proxy"].get_folders_data(self)

        for folder_data in folder_datas:
            reg = r"(?P<tags>\(.*\)) \"((?P<separator>.))\" (?P<technical_name>.*)"
            result = re.search(reg, folder_data.decode()).groupdict()
            separator = result["separator"]
            technical_name = result["technical_name"]
            if technical_name[0] == '"' and technical_name[-1] == '"':
                technical_name = technical_name[1:-1]

            WebmailFolder._get_or_create(self, separator, technical_name)
