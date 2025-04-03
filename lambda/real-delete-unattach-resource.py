import json
import boto3
import urllib.request

ec2 = boto3.client("ec2")

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
        print("❌ Failed to post to Slack:", e)

def lambda_handler(event, context):
  
    for record in event["Records"]:
        try:
            msg = json.loads(record["body"])
            eips = msg.get("eips", [])
            enis = msg.get("enis", [])
            response_url = msg.get("response_url")

            results = []

            # EIP 삭제
            for alloc_id in eips:
                try:
                    ec2.release_address(AllocationId=alloc_id)
                    results.append(f"EIP {alloc_id} delete success")
                except Exception as e:
                    results.append(f"EIP {alloc_id} delete fail: {e}")

            # ENI 삭제
            for eni_id in enis:
                try:
                    ec2.delete_network_interface(NetworkInterfaceId=eni_id)
                    results.append(f"ENI {eni_id} delete success")
                except Exception as e:
                    results.append(f"ENI {eni_id} delete fail: {e}")

            # Slack 결과 전송
            if response_url:
                post_to_slack(response_url, {
                    "response_type": "ephemeral",
                    "text": "🧹 Deletion Result:\n" + "\n".join(results)
                })

        except Exception as e:
            print("❌ Failed to post to Slack:", e)
