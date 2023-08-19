# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import socket
from imaplib import IMAP4

from odoo import _, models
from odoo.exceptions import UserError


class ImapProxy(models.AbstractModel):
    _name = "imap.proxy"
    _description = "IMAP Proxy"

    def test_connexion(self, webmail_account):
        webmail_account.ensure_one()
        client = self._get_client_connected(webmail_account)
        client.logout()

    def _get_client_connected(self, webmail_account):
        webmail_account.ensure_one()
        try:
            client = IMAP4(host=webmail_account.url, timeout=5)
        except socket.gaierror as e:
            raise UserError(
                _(
                    "server '%s' has not been reached. Possible Reasons: \n"
                    "- the server doesn't exist"
                    "- your odoo instance faces to network issue"
                )
                % (webmail_account.url)
            ) from e

        try:
            client.login(webmail_account.login, webmail_account.password)
        except IMAP4.error as e:
            raise UserError(
                _(
                    "Authentication failed. Possible Reasons: \n"
                    "- your credentials are incorrect (%s // **********)"
                )
                % (webmail_account.login)
            ) from e

        return client

    def get_folders_data(self, webmail_account):
        webmail_account.ensure_one()
        client = self._get_client_connected(webmail_account)
        result = client.list()
        client.logout()
        return result
