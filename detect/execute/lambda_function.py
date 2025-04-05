import json
import boto3
import urllib.request
import asyncio
import concurrent.futures
import time

from util.post_to_slack import post_to_slack
from util.build_slack_blocks import build_slack_blocks
from find_unused_resources import find_unused_resources


def lambda_handler(event, context):
    # Output the full event for debugging
    print("Received event:", json.dumps(event))
    
    # Get Slack response URL
    response_url = None
    
    # Find response_url from the event (handling various formats)
    if isinstance(event, dict):
        # Check for response_url key directly in the event
        if 'response_url' in event:
            response_url = event['response_url']
        # It might be inside a Payload
        elif 'Payload' in event:
            try:
                payload = json.loads(event['Payload'])
                if isinstance(payload, dict) and 'response_url' in payload:
                    response_url = payload['response_url']
            except:
                pass
        
    print(f"Response URL found: {response_url}")
    
    # Find unused resources (asynchronous processing)
    regional_eips, regional_enis = find_unused_resources()
    total_eips = sum(len(eips) for eips in regional_eips.values())
    total_enis = sum(len(enis) for enis in regional_enis.values())
    print(f"Found unused resources - Total EIPs: {total_eips}, Total ENIs: {total_enis}")
    blocks = build_slack_blocks(regional_eips, regional_enis)
    
    # Compose Slack message
    slack_message = {
        "response_type": "ephemeral",
        "blocks": blocks
    }
    
    # Send results to Slack if response URL is available
    if response_url:
        post_to_slack(response_url, slack_message)
    else:
        print("❌ No response_url found in the event. Cannot send message to Slack.")
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "https://slack.com",
                    "Access-Control-Allow-Credentials": "true"},
        "body": json.dumps(slack_message)
    }
