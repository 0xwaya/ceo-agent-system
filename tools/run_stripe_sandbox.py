"""Run Flask with sandbox Stripe webhook forwarding without printing credentials."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import environment_service  # noqa: E402,F401
from services.billing_service import BillingService  # noqa: E402


def redact(line):
    return re.sub(
        r"(?:whsec|sk_test|sk_live|rk_test|rk_live|pk_test|pk_live)_[A-Za-z0-9]+",
        "<redacted>",
        line,
    )


def main():
    service = BillingService()
    settings = service.settings()
    if settings["live"]:
        raise RuntimeError("Sandbox runner refuses live Stripe credentials")
    executable = shutil.which("stripe")
    if not executable:
        local_cli = Path.home() / ".local/bin/stripe"
        if local_cli.is_file():
            executable = str(local_cli)
    if not executable:
        raise RuntimeError("Install the official Stripe CLI before running this command")
    port = int(os.getenv("FLASK_PORT", "5001"))
    if os.getenv("FLASK_HOST", "127.0.0.1") != "127.0.0.1":
        raise RuntimeError("Sandbox runner requires FLASK_HOST=127.0.0.1")
    env = dict(os.environ, STRIPE_API_KEY=settings["key"], BILLING_ENABLED="true")
    events = ",".join(
        [
            "checkout.session.completed",
            "invoice.paid",
            "invoice.payment_failed",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "charge.refunded",
            "charge.dispute.created",
        ]
    )
    ready = threading.Event()
    signing_secret = []
    listener = subprocess.Popen(
        [
            executable,
            "listen",
            "--forward-to",
            f"http://localhost:{port}/api/billing/webhook",
            "--events",
            events,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    app = None

    def output():
        for line in listener.stdout:
            match = re.search(r"whsec_[A-Za-z0-9]+", line)
            if match:
                signing_secret.append(match.group())
                ready.set()
            print(redact(line), end="", flush=True)

    thread = threading.Thread(target=output, daemon=True)
    thread.start()
    try:
        if not ready.wait(30):
            raise RuntimeError(
                "Stripe listener did not return a signing secret; check connectivity"
            )
        env["STRIPE_WEBHOOK_SECRET"] = signing_secret[0]
        root = Path(__file__).resolve().parents[1]
        app = subprocess.Popen([sys.executable, str(root / "app.py")], cwd=root, env=env)
        print(
            "Sandbox listener and Flask started; signing secret stays in process memory.",
            flush=True,
        )
        while listener.poll() is None and app.poll() is None:
            time.sleep(1)
        raise RuntimeError("Sandbox listener or Flask exited unexpectedly")
    finally:
        for process in (app, listener):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        thread.join(timeout=2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
