from email.header import decode_header

from imapclient.response_types import Address


def _get_string(imap_bytes: bytes) -> str:
    if not imap_bytes:
        return ""
    dh = decode_header(imap_bytes.decode())
    return "".join(
        [isinstance(t[0], bytes) and t[0].decode(t[1] or "utf-8") or t[0] for t in dh]
    )


def _get_mail(address: Address) -> str:
    return "%s@%s" % (address.mailbox.decode(), address.host.decode())
