# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import email
import email.policy
import imaplib
import logging
from datetime import datetime
from xmlrpc import client as xmlrpclib

from babel.dates import format_date, format_time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"
    _order = "technical_date desc"
    _rec_name = "technical_subject"

    display_date = fields.Char(string="date", compute="_compute_display_date")

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    account_id = fields.Many2one(
        comodel_name="webmail.account",
        related="folder_id.account_id",
        store=True,
    )

    origin_mail_id = fields.Many2one(comodel_name="webmail.mail", readonly=True)

    conversation_id = fields.Many2one(
        comodel_name="webmail.conversation", readonly=True, ondelete="cascade"
    )

    technical_message_id = fields.Char(required=True, readonly=True)

    technical_in_reply_to = fields.Char(readonly=True)
    technical_date = fields.Datetime(required=True, readonly=True)

    technical_subject = fields.Char(readonly=True)
    technical_body = fields.Html(readonly=True)

    technical_to = fields.Char(readonly=True)
    technical_from = fields.Char(readonly=True)
    technical_cc = fields.Char(readonly=True)

    # sender_address_id = fields.Many2one(
    #     comodel_name="webmail.address",
    #     readonly=True,
    # )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    # Compute Section
    @api.depends("technical_date")
    def _compute_display_date(self):
        for mail in self:
            mail.display_date = self._get_display_date(mail.technical_date)

    # Overload Section
    def unlink(self):
        conversations = self.mapped("conversation_id")
        res = super().unlink()
        conversations.filtered(lambda x: x.mail_qty == 0).unlink()
        return res

    # Custom Section
    @api.model
    def _get_display_date(self, mail_date):
        date_now = datetime.now().date()
        if date_now == mail_date.date():
            return format_time(mail_date, format="short")
        elif date_now.year == mail_date.year:
            return mail_date.strftime("%-d %b")
        else:
            return format_date(mail_date, format="short")

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
        # mail_datas = client.fetch(message_ids, ["FLAGS", "ENVELOPE", "RFC822"])

        for message_number in message_numbers:
            message_data = client.fetch(message_number, "(RFC822)")[1][0][1]
            if isinstance(message_data, xmlrpclib.Binary):
                message_data = bytes(message_data.data)
            if isinstance(message_data, str):
                message_data = message_data.encode("utf-8")
            message = email.message_from_bytes(message_data, policy=email.policy.SMTP)
            self._get_or_create(webmail_folder, message)

        client.logout()

    def _get_or_create(self, webmail_folder, message):
        message_dict = (
            self.env["mail.thread"]
            .with_context(no_mail_thread=True)
            .message_parse(message)
        )

        technical_message_id = message_dict["message_id"]
        technical_in_reply_to = message_dict["in_reply_to"]
        vals = {
            "folder_id": webmail_folder.id,
        }

        # Check if mail exists in Odoo
        existing_mail = self.search(
            [("technical_message_id", "=", technical_message_id)]
        )
        if existing_mail:
            if existing_mail.folder_id != webmail_folder:
                existing_mail.write(vals)
            return existing_mail

        origin_mail = self.search(
            [("technical_message_id", "=", technical_in_reply_to)]
        )

        other_mails = self.search(
            [("technical_in_reply_to", "=", technical_message_id)]
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
                "conversation_id": conversation.id,
                "origin_mail_id": origin_mail and origin_mail.id,
                "technical_message_id": technical_message_id,
                "technical_in_reply_to": technical_in_reply_to,
                "technical_date": message_dict["date"],
                # draft mail can have no subject
                "technical_subject": message_dict.get("subject", ""),
                "technical_from": message_dict["from"],
                "technical_cc": message_dict["cc"],
                "technical_to": message_dict["to"],
                "technical_body": message_dict["body"],
                # "sender_address_id": self.env["webmail.address"]
                # ._get_from_address(webmail_folder.user_id, envelope.sender[0])
                # .id,
                # "technical_envelope": str(envelope),
                # "technical_flags": str(mail_data[b"FLAGS"]),
                # "technical_rfc822": str(mail_data[b"RFC822"]),
            }
        )

        _logger.info(
            "fetch from the upstream mail server."
            " Account %s. Creation of mail %s"
            % (webmail_folder.account_id.login, technical_message_id)
        )
        new_mail = self.create(vals)

        if other_mails:
            other_mails.write({"origin_mail_id": new_mail.id})
        return new_mail
