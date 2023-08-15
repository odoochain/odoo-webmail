# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


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
        self.env["imap.proxy"].test_connexion()

    def button_fetch_folders(self):
        self.env["webmail.folder"].with_delay()._fetch_folders(self)

    def button_fetch_mails(self):
        for folder in self.mapped("folder_ids"):
            folder.button_fetch_mails()
