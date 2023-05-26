from email.header import decode_header


def _get_subject(imap_subject):
    if not imap_subject:
        return ""
    dh = decode_header(imap_subject.decode())
    return "".join(
        [isinstance(t[0], bytes) and t[0].decode(t[1] or "utf-8") or t[0] for t in dh]
    )
