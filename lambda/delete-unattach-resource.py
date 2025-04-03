import json
import boto3
import urllib.parse
import urllib.request
import base64

sqs = boto3.client("sqs")

SQS_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/354918406440/delete-unattach-queue"

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

    eips = value.get('eips', [])
    enis = value.get('enis', [])
    response_url = payload.get('response_url')

    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({
                "eips": eips,
                "enis": enis,
                "response_url": response_url
            })
        )

        post_to_slack(response_url, {
            "response_type": "ephemeral",
            "text": f"✅ Your deletion request has been received successfully.\nUnused EIPs: {', '.join(eips) or 'None'}\nUnused ENIs: {', '.join(enis) or 'None'}"
        })
    except Exception as e:
        print("❌ Failed to send message to SQS:", e)
        post_to_slack(response_url, {
            "response_type": "ephemeral",
            "text": f"✅  Your deletion request has been received fail. \nEIP: {', '.join(eips) or 'None'}\nENI: {', '.join(enis) or 'None'}"
        })
    

    # 5. Return empty response immediately (Slack needs 200 fast)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": ""
    }
