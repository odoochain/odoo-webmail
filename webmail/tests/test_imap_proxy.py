# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class Tests(TransactionCase):
    def setUp(self):
        super().setUp()
        self.proxy = self.env["imap.proxy"]
        self.demo_account_bad_url = self.env.ref("webmail.demo_account_bad_url")
        self.demo_account_gandi_bad_login = self.env.ref(
            "webmail.demo_account_gandi_bad_login"
        )

    # Test Section
    def test_test_connexion(self):
        # TODO, improve check content of error
        with self.assertRaises(TimeoutError):
            self.proxy.test_connexion(self.demo_account_bad_url)

        with self.assertRaises(UserError):
            self.proxy.test_connexion(self.demo_account_gandi_bad_login)
