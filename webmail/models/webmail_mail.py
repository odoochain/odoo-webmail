# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import imaplib
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

from .imap_tools import _get_string

_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"
    _order = "date_mail desc"

    date_mail = fields.Datetime(required=True, readonly=True)

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        required=True,
        readonly=True,
    )

    identifier = fields.Char(required=True, readonly=True)

    origin_mail_id = fields.Many2one(comodel_name="webmail.mail", readonly=True)

    conversation_id = fields.Many2one(
        comodel_name="webmail.conversation", readonly=True, ondelete="cascade"
    )

    reply_identifier = fields.Char(readonly=True)

    subject = fields.Char(readonly=True)

    sender_address_id = fields.Many2one(
        comodel_name="webmail.address",
        required=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    envelope_data = fields.Text(
        string="Technical field containing envelope", readonly=True
    )

    flags_data = fields.Text(string="Technical field containing flags", readonly=True)

    def _fetch_mails(self, webmail_folder):
        client = webmail_folder.account_id._get_client_connected()
        try:
            client.select_folder(webmail_folder.technical_name)
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

        # TODO ADD : [u'SINCE', date(2005, 4, 3)]
        message_ids = client.search(["NOT", "DELETED"])
        mail_datas = client.fetch(message_ids, ["FLAGS", "ENVELOPE"])

        for _message_id, mail_data in mail_datas.items():
            self._get_or_create(webmail_folder, mail_data)

        client.logout()

    def _get_or_create(self, webmail_folder, mail_data):
        envelope = mail_data[b"ENVELOPE"]
        identifier = envelope.message_id.decode()
        reply_identifier = (
            envelope.in_reply_to and envelope.in_reply_to.decode() or False
        )
        vals = {
            "folder_id": webmail_folder.id,
        }

        # Check if mail exists in Odoo
        existing_mail = self.search(
            [
                ("identifier", "=", identifier),
            ]
        )
        if existing_mail:
            if existing_mail.folder_id != webmail_folder:
                existing_mail.write(vals)
            return existing_mail

        origin_mail = self.search(
            [
                ("identifier", "=", reply_identifier),
            ]
        )

        other_mails = self.search(
            [
                ("reply_identifier", "=", identifier),
            ]
        )

        # Get conversation(s) and merge if required or create a new one
        conversations = (
            other_mails.mapped("conversation_id") | origin_mail.conversation_id
        )
        if not conversations:
            conversation = self.env["webmail.conversation"].create(
                {
                    "account_id": webmail_folder.account_id.id,
                }
            )
        elif len(conversations) == 1:
            conversation = conversations[0]
        else:
            conversation = conversations.merge()

        vals.update(
            {
                "identifier": identifier,
                "conversation_id": conversation.id,
                "date_mail": envelope.date,
                "reply_identifier": reply_identifier,
                "origin_mail_id": origin_mail and origin_mail.id,
                "subject": _get_string(envelope.subject),
                "sender_address_id": self.env["webmail.address"]
                ._get_from_address(webmail_folder.user_id, envelope.sender[0])
                .id,
                "envelope_data": str(envelope),
                "flags_data": str(mail_data[b"FLAGS"]),
            }
        )

        _logger.info(
            "fetch from the upstream mail server."
            " Account %s. Creation of mail %s"
            % (webmail_folder.account_id.name, identifier)
        )
        new_mail = self.create(vals)

        if other_mails:
            other_mails.write(
                {
                    "origin_mail_id": new_mail.id,
                }
            )
        return new_mail

    def unlink(self):
        conversations = self.mapped("conversation_id")
        res = super().unlink()
        conversations.filtered(lambda x: x.mail_qty == 0).unlink()
        return res
