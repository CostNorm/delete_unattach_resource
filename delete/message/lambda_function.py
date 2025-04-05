import json
import boto3
import urllib.parse
import urllib.request
import base64

lambda_client = boto3.client("lambda")

def post_to_slack(response_url, message):
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

def lambda_handler(event, context):
    # 1. Decode body from base64 if needed
    body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        body = base64.b64decode(body).decode("utf-8")

    # 2. Parse body as form-urlencoded
    parsed = urllib.parse.parse_qs(body)
    payload_raw = parsed.get("payload", [None])[0]
    if not payload_raw:
        return {"statusCode": 400, "body": "No payload found"}

    payload = json.loads(payload_raw)

    # 3. Extract values
    action = payload['actions'][0]
    value = json.loads(action['value'])

    regional_eips = value.get('eips', {})
    regional_enis = value.get('enis', {})
    response_url = payload.get('response_url')

    # 4. Notify user that deletion is in progress
    total_eips = sum(len(eips) for eips in regional_eips.values()) if regional_eips else 0
    total_enis = sum(len(enis) for enis in regional_enis.values()) if regional_enis else 0
    
    post_to_slack(response_url, {
        "response_type": "ephemeral",
        "text": f"🔄 Resource deletion process has started. Please wait...\nTotal EIPs: {total_eips}, Total ENIs: {total_enis}"
    })

    try:
        # 5. Invoke resource deletion Lambda function asynchronously
        lambda_client.invoke(
            FunctionName='executeDeleteUnattach',
            InvocationType='Event',
            Payload=json.dumps({
                "regional_eips": regional_eips,
                "regional_enis": regional_enis,
                "response_url": response_url
            })
        )
        
        print(f"✅ Successfully invoked resource deletion Lambda function")
    except Exception as e:
        print(f"❌ Failed to invoke resource deletion Lambda function: {str(e)}")
        post_to_slack(response_url, {
            "response_type": "ephemeral",
            "text": f"❌ An error occurred while processing your deletion request: {str(e)}"
        })

    # 6. Return empty response immediately (Slack needs 200 fast)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": ""
    }