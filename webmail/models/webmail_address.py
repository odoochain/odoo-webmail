# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from imapclient.response_types import Address

from odoo import fields, models

from .imap_tools import _get_mail, _get_string

_logger = logging.getLogger(__name__)


class WebmailAddress(models.Model):
    _name = "webmail.address"
    _description = "Webmail Addresses"
    _order = "email"

    display_name = fields.Char(compute="_compute_display_name")

    name = fields.Char()

    email = fields.Char(required=True, readonly=True)

    user_id = fields.Many2one(comodel_name="res.users", required=True)

    _sql_constraints = [
        (
            "user_id_email_unique",
            "UNIQUE(user_id,email)",
            "You cannot have the same email twice.",
        )
    ]

    def _compute_display_name(self):
        for address in self:
            address.display_name = address.name or address.email

    def _get_from_address(self, user, address: Address):
        email = _get_mail(address)

        existing_address = self.search(
            [("email", "=", email), ("user_id", "=", user.id)]
        )

        # Use existing address (and update it, if required)
        if existing_address:
            if not existing_address.name and address.name:
                existing_address.name = _get_string(address.name)
            return existing_address

        # create new address
        _logger.info(
            "fetch from the upstream mail server." " Creation of address %s" % (email)
        )

        return self.create(
            {"user_id": user.id, "email": email, "name": _get_string(address.name)}
        )
