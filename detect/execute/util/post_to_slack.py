import urllib.request
import json
def post_to_slack(response_url, message):
    """Send message to Slack"""
    req = urllib.request.Request(
        response_url,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            res.read()
            print("✅ Successfully sent message to Slack")
    except Exception as e:
        print("❌ Failed to send Slack message:", e)