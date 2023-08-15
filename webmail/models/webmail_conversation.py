# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebmailConversation(models.Model):
    _name = "webmail.conversation"
    _description = "Webmail Conversation"
    _order = "date_last_mail desc"
    _rec_name = "technical_subject"

    date_first_mail = fields.Datetime(compute="_compute_mail_infos", store=True)

    date_last_mail = fields.Datetime(compute="_compute_mail_infos", store=True)

    display_date = fields.Char(compute="_compute_mail_infos", store=True)

    display_subject = fields.Html(
        string="Displayed Subject", compute="_compute_mail_infos", store=True
    )
    technical_subject = fields.Char(
        string="Subject", compute="_compute_mail_infos", store=True
    )

    contact_ids = fields.Many2many(
        comodel_name="webmail.address",
        compute="_compute_mail_infos",
        store=True,
    )

    mail_ids = fields.One2many(
        comodel_name="webmail.mail",
        inverse_name="conversation_id",
        readonly=True,
    )

    mail_qty = fields.Integer(string="Mails", compute="_compute_mail_qty", store=True)

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

    # Compute Section
    @api.depends(
        "mail_ids.technical_date",
        "mail_ids.display_subject",
    )
    # "mail_ids.sender_address_id",
    def _compute_mail_infos(self):
        for conversation in self:
            mails = conversation.mail_ids.sorted(key=lambda r: r.technical_date)
            if mails:
                conversation.date_first_mail = mails[0].technical_date
                conversation.date_last_mail = mails[-1].technical_date
                conversation.display_subject = mails[0].display_subject
                conversation.technical_subject = mails[0].technical_subject
                conversation.display_date = self.env["webmail.mail"]._get_display_date(
                    conversation.date_last_mail
                )
            else:
                conversation.date_first_mail = False
                conversation.date_last_mail = False
                conversation.display_subject = False
                conversation.technical_subject = False
                conversation.display_date = False
            # conversation.contact_ids = mails.mapped("sender_address_id")

    @api.depends("mail_ids")
    def _compute_mail_qty(self):
        for conversation in self:
            conversation.mail_qty = len(conversation.mail_ids)

    def merge(self):
        if len(self) < 2:
            raise UserError(_("Can not merge %d conversation") % len(self))
        else:
            main_conversation = self[0]
            other_conversations = self[-1:]
            other_conversations.mapped("mail_ids").write(
                {"conversation_id": main_conversation.id}
            )
            other_conversations.unlink()
        return main_conversation
