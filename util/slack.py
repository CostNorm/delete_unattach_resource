import json
import os
import urllib.request
from typing import Dict, Any, Optional, List, Union

def send_slack_block_response(response_url: str, blocks: Optional[List[Dict[str, Any]]] = None) -> bool:
    
    if not response_url:
        print("❌ No response_url provided")
        return False
    
    # 메시지 데이터 구성
    slack_message = {
        "response_type": "ephemeral",
        "blocks": blocks
    }
    
    req = urllib.request.Request(
        response_url,
        data=json.dumps(slack_message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            res.read()
            print("✅ Successfully sent message to Slack")
    except Exception as e:
        print("❌ Failed to send Slack message:", e)


def send_slack_text_response(response_url: str, message: str, ephemeral: bool = True) -> bool:
    if not response_url:
        print("❌ No response_url provided")
        return False
    
    # 메시지 데이터 구성
    slack_message = {
        "response_type": "ephemeral",
        "text": message
    }
    
    req = urllib.request.Request(
        response_url,
        data=json.dumps(slack_message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            res.read()
            print("✅ Successfully sent message to Slack")
    except Exception as e:
        print("❌ Failed to send Slack message:", e)


def return_slack_response(message: str, ephemeral: bool = True) -> None:
   
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://slack.com",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps({
            "response_type": "ephemeral" if ephemeral else "in_channel",
            "text": message
        })
    }

