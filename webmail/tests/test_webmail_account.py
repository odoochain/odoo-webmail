# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.tests.common import TransactionCase

from . import data


class Tests(TransactionCase):
    def setUp(self):
        super().setUp()
        self.demo_account_gandi_bad_login = self.env.ref(
            "webmail.demo_account_gandi_bad_login"
        )
        self.WebmailFolder = self.env["webmail.folder"]

    # Test Section
    @patch(
        "odoo.addons.webmail.models.imap_proxy.ImapProxy.get_folders_data",
        return_value=data.folders_data,
    )
    def test_fetch_folders(self, _get_folders_data):
        self.demo_account_gandi_bad_login.button_fetch_folders()
        project_folder = self.WebmailFolder.search([("name", "=", "Projects")])
        self.assertEqual(len(project_folder), 1)
        child_folder = project_folder.child_ids.filtered(
            lambda x: x.name == "OCA - OpenUpgrade Documentation"
        )
        self.assertEqual(len(child_folder), 1)
