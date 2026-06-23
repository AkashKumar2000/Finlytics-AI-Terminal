"""Zerodha Kite Connect — daily access token generator.

Run this script once each morning to refresh your access token:
    python scripts/kite_auth.py

Steps:
  1. Script prints the Kite login URL
  2. Open it in your browser and log in with your Zerodha credentials
  3. After login, Zerodha redirects to your redirect URL — copy the `request_token` from the URL
  4. Paste it here — script exchanges it for an access_token and saves it to .env
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")


def update_env(key: str, value: str):
    """Update or insert a key=value line in .env."""
    with open(ENV_PATH, "r") as f:
        content = f.read()

    pattern = rf"^{key}=.*$"
    new_line = f"{key}={value}"

    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
    else:
        content += f"\n{new_line}\n"

    with open(ENV_PATH, "w") as f:
        f.write(content)

    print(f"✅ Saved {key} to .env")


def main():
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)

    api_key = os.getenv("KITE_API_KEY", "").strip()
    api_secret = os.getenv("KITE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("❌ KITE_API_KEY or KITE_API_SECRET missing in .env")
        sys.exit(1)

    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=api_key)

    login_url = kite.login_url()
    print("\n" + "─" * 60)
    print("STEP 1 — Open this URL in your browser and log in:")
    print(f"\n  {login_url}\n")
    print("─" * 60)
    print("STEP 2 — After login, Zerodha redirects to your redirect URL.")
    print("         Copy the 'request_token' value from the URL.")
    print("         It looks like: ?request_token=xxxxxxxx&action=login&status=success")
    print("─" * 60)

    request_token = input("\nPaste the request_token here: ").strip()

    if not request_token:
        print("❌ No request_token provided.")
        sys.exit(1)

    try:
        session = kite.generate_session(request_token, api_secret=api_secret)
        access_token = session["access_token"]
        print(f"\n✅ Access token generated: {access_token[:10]}...")
        update_env("KITE_ACCESS_TOKEN", access_token)
        print("\n🎉 Done! Restart the backend container to apply:")
        print("   docker restart investment-research-dashboard-backend-1")
    except Exception as e:
        print(f"\n❌ Failed to generate session: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
