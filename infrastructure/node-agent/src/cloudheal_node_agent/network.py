import subprocess


def get_local_ip() -> str:
    """Return this node's Tailscale IPv4 address."""
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        address = result.stdout.strip()

        if address:
            return address

    except (subprocess.SubprocessError, OSError):
        pass

    raise RuntimeError(
        "Could not determine the node's Tailscale IP address"
    )