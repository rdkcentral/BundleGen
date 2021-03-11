def get_default_caps():
    """
    Returns a default set of capabilities that are applied by default. This
    is a very minimal set designed to allow most applications to work out of the
    box

    It is recommended that you override this list with a platform specific set
    of capabilities

    References:
    * https://www.redhat.com/en/blog/secure-your-containers-one-weird-trick
    * https://github.com/moby/moby/blob/46cdcd206c56172b95ba5c77b827a722dab426c5/oci/caps/defaults.go (Docker default set)
    """
    return [
        "CAP_CHOWN",
        "CAP_FSETID",
        "CAP_NET_RAW",
        "CAP_SETGID",
        "CAP_SETUID",
        "CAP_SETPCAP",
        "CAP_NET_BIND_SERVICE",
        "CAP_KILL",
        "CAP_AUDIT_WRITE"
    ]