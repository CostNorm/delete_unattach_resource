import json
import boto3

ec2 = boto3.client('ec2')

def find_unused_resources():
    unused_eips = []
    unused_enis = []

    addresses = ec2.describe_addresses()['Addresses']
    for address in addresses:
        if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
            unused_eips.append(address['AllocationId'])

    enis = ec2.describe_network_interfaces(Filters=[{'Name': 'status', 'Values': ['available']}])['NetworkInterfaces']
    for eni in enis:
        unused_enis.append(eni['NetworkInterfaceId'])

    return unused_eips, unused_enis

def build_slack_blocks(eips, enis):
    blocks = []

    if not eips and not enis:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*There are no unused resources at the moment.*"}
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Unused resources have been found.*"}
        })
        if eips:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*EIPs:* {', '.join(eips)}"}
            })
        if enis:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*ENIs:* {', '.join(enis)}"}
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Delete"},
                    "style": "danger",
                    "value": json.dumps({"eips": eips, "enis": enis}),
                    "action_id": "delete_unused"
                }
            ]
        })

    return blocks

def lambda_handler(event, context):
    eips, enis = find_unused_resources()
    blocks = build_slack_blocks(eips, enis)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "https://slack.com",
                    "Access-Control-Allow-Credentials": "true"},
        "body": json.dumps({
            "response_type": "ephemeral",
            "blocks": blocks
        })
    }
