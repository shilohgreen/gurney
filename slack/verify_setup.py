#!/usr/bin/env python3
"""
Verify Slack bot setup - checks tokens and permissions.

Run from project root: python3 slack/verify_setup.py
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from slack_sdk import WebClient

# Load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")


def verify_setup():
    """Check if tokens are valid and bot has required permissions."""
    
    print("🔍 Verifying Slack bot setup...\n")
    
    # Check tokens exist
    if not SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN is missing from .env")
        return False
    
    if not SLACK_APP_TOKEN:
        print("❌ SLACK_APP_TOKEN is missing from .env")
        return False
    
    print(f"✅ SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN[:10]}...")
    print(f"✅ SLACK_APP_TOKEN: {SLACK_APP_TOKEN[:10]}...\n")
    
    # Check bot token format
    if not SLACK_BOT_TOKEN.startswith("xoxb-"):
        print("⚠️  SLACK_BOT_TOKEN should start with 'xoxb-'")
    
    if not SLACK_APP_TOKEN.startswith("xapp-"):
        print("⚠️  SLACK_APP_TOKEN should start with 'xapp-'")
        return False
    
    print("📋 Checking SLACK_APP_TOKEN:")
    print("   ⚠️  App-level tokens can't be verified via API")
    print("   ✅ If bot connects (you see 'A new session has been established'), token is valid")
    print("   ✅ Make sure it has 'connections:write' scope in App-Level Tokens\n")
    
    # Test bot token with API call
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        auth_test = client.auth_test()
        
        print(f"✅ Bot token is valid")
        print(f"   Bot User ID: {auth_test.get('user_id')}")
        print(f"   Team: {auth_test.get('team')}")
        print(f"   Bot ID: {auth_test.get('bot_id')}\n")
        
        # Check scopes
        scopes = auth_test.get("scopes", [])
        required_scopes = ["app_mentions:read", "chat:write", "commands"]
        
        print("📋 Checking OAuth scopes:")
        for scope in required_scopes:
            if scope in scopes:
                print(f"   ✅ {scope}")
            else:
                print(f"   ❌ {scope} - MISSING! Add this in OAuth & Permissions")
        
        missing = [s for s in required_scopes if s not in scopes]
        if missing:
            print(f"\n⚠️  Missing scopes: {', '.join(missing)}")
            print("   Go to: https://api.slack.com/apps → Your App → OAuth & Permissions")
            print("   Add the missing scopes, then reinstall the app to your workspace")
            return False
        
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False
    
    print("\n✅ Setup looks good! Try @gurney in a channel where the bot is added.")
    return True


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)

