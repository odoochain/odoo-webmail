# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import email
import imaplib
import logging
from xmlrpc import client as xmlrpclib

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebmailFolder(models.Model):
    _name = "webmail.folder"
    _description = "Webmail Folders"
    _order = "technical_name"
    _rec_name = "technical_name"

    name = fields.Char(required=True, readonly=True)

    parent_id = fields.Many2one(
        comodel_name="webmail.folder",
        readonly=True,
    )

    child_ids = fields.One2many(
        comodel_name="webmail.folder",
        inverse_name="parent_id",
    )

    account_id = fields.Many2one(
        comodel_name="webmail.account",
        required=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="account_id.user_id",
        store=True,
        readonly=True,
    )

    mail_ids = fields.One2many(
        comodel_name="webmail.mail",
        inverse_name="folder_id",
    )

    folder_qty = fields.Integer(
        string="Folders", compute="_compute_folder_qty", store=True
    )

    mail_qty = fields.Integer(string="Mails", compute="_compute_mail_qty", store=True)

    technical_name = fields.Char(required=True, readonly=True)

    # Compute Section
    @api.depends("child_ids.parent_id")
    def _compute_folder_qty(self):
        for folder in self:
            folder.folder_qty = len(folder.child_ids)

    @api.depends("mail_ids.folder_id")
    def _compute_mail_qty(self):
        for folder in self:
            folder.mail_qty = len(folder.mail_ids)

    # Action Section
    def button_fetch_mails(self):
        for folder in self:
            folder._fetch_mails()

    # Custom Section
    def _get_or_create(self, webmail_account, separator, technical_name):
        # Check if folder exist in Odoo
        existing_folder = self.search(
            [
                ("account_id", "=", webmail_account.id),
                ("technical_name", "=", technical_name),
            ]
        )
        if existing_folder:
            return existing_folder

        name_parts = technical_name.split(separator)
        vals = {
            "account_id": webmail_account.id,
            "technical_name": technical_name,
            "name": name_parts[-1],
        }
        if separator in technical_name:
            vals.update(
                {
                    "parent_id": self._get_or_create(
                        webmail_account, separator, "/".join(name_parts[:-1])
                    ).id
                }
            )

        _logger.info(
            "fetch from the upstream mail server."
            " Account %s. Creation of folder %s" % (webmail_account.login, vals["name"])
        )
        return self.create(vals)

    def _fetch_mails(self, webmail_folder):
        client = webmail_folder.account_id._get_client_connected()
        try:
            folder_name = webmail_folder.technical_name
            if " " in folder_name:
                folder_name = '"' + folder_name + '"'
            client.select(folder_name)
        except imaplib.IMAP4.error as e:
            message = _(
                "Folder %(folder_name)s doesn't exists for account %(account_login)s."
            ) % (
                {
                    "folder_name": webmail_folder.technical_name,
                    "account_login": webmail_folder.account_id.login,
                }
            )
            client.logout()
            raise UserError(message) from e

        message_numbers = client.search(None, "(ALL)")[1][0].split()

        for message_number in message_numbers:
            message_data = client.fetch(message_number, "(RFC822)")[1][0][1]
            if isinstance(message_data, xmlrpclib.Binary):
                message_data = bytes(message_data.data)
            if isinstance(message_data, str):
                message_data = message_data.encode("utf-8")
            message = email.message_from_bytes(message_data, policy=email.policy.SMTP)
            self._get_or_create(webmail_folder, message)

        client.logout()
