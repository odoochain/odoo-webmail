# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import socket
from imaplib import IMAP4
import pathlib

from imapclient.exceptions import IMAPClientError

from odoo import _, models
from odoo.addons.webmail.models import mail_client
from odoo.exceptions import UserError


class ImapProxy(models.AbstractModel):
    _name = "imap.proxy"
    _description = "IMAP Proxy"

    def filter_mail_subject_move_and_save_eml(self, mail):
        if '测试' in mail.subject:
            mail_client.MailClient.move_mail(mail.uid, 'Parent_1/Parent_2')
        with open(pathlib.Path(__file__).parent / f"{mail.subject}.eml", 'wb') as f:
            f.write(mail.eml)

    def test_connexion(self, webmail_account):
        # with mail_client.MailQiYeQQ(user_name=webmail_account.login,
        #                             password=webmail_account.password) as qq_mail_client:
        #     # UID 不是每次都一样，所以拿到邮件的 UID 时，需要交给 callback 处理。
        #     # 单次收取邮件数目不超过30个，有的邮箱拿多了会 ban。
        #     qq_mail_client.handle_mails(self.filter_mail_subject_move_and_save_eml, mails_count=30)
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
