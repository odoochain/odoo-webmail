# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Webmail",
    "summary": "Odoo as a Webmail",
    "version": "16.0.1.0.0",
    "category": "R&D",
    "author": "Odoo as a Free Software (OaaFS)",
    "developpement_status": "Alpha",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/oaafs/odoo-webmail",
    "license": "AGPL-3",
    "depends": [
        "base",
        # OCA
        "queue_job",
        "web_notify",
    ],
    "external_dependencies": {"python": ["imapclient"]},
    "data": [
        "security/ir_module_category.xml",
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/view_webmail_host.xml",
        "views/view_webmail_account.xml",
        "views/view_webmail_address.xml",
        "views/view_webmail_folder.xml",
        "views/view_webmail_mail.xml",
        "views/view_webmail_conversation.xml",
    ],
    "demo": [
        "demo/webmail_host.xml",
    ],
}
