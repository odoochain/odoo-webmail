# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from ..models import imap_tools


class Tests(TransactionCase):
    def setUp(self):
        super().setUp()

    # Test Section
    def test_01_get_subject(self):
        values = [
            (  # No Subject
                False,
                "",
            ),
            (  # No encoding specified
                b"Re: Kick off meeting for Open Upgrade Documentation",
                "Re: Kick off meeting for Open Upgrade Documentation",
            ),
            (  # utf-8 / q
                b"=?utf-8?q?Re=3A?= How to move forward =?utf-8?q?=3F?=",
                "Re: How to move forward ?",
            ),
            (  # UTF-8 / Q
                b"=?UTF-8?Q?Re=3A_Mise_=C3=A0_jour_repo_odoo-migrate?=",
                "Re: Mise à jour repo odoo-migrate",
            ),
            (
                b"=?iso-8859-1?Q?Votre d=E9claration accessible en ligne?=",
                "Votre déclaration accessible en ligne",
            ),
        ]
        for (imap_subject, subject) in values:
            self.assertEqual(
                imap_tools._get_subject(imap_subject),
                subject,
            )
