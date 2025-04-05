import json
import boto3

from util.post_to_slack import post_to_slack
from delete import delete_eips, delete_enis



def lambda_handler(event, context):
    # Extract data from event
    regional_eips = event.get('regional_eips', {})
    regional_enis = event.get('regional_enis', {})
    response_url = event.get('response_url')
    
    if not response_url:
        print("❌ No response_url provided")
        return {
            "statusCode": 400,
            "body": "Missing response_url"
        }
    
    # Track results
    results = {
        'eips': {'success': [], 'failed': []},
        'enis': {'success': [], 'failed': []}
    }
    
    # 1. Delete EIPs for each region
    for region, eip_ids in regional_eips.items():
        success, failed = delete_eips(region, eip_ids)
        for eip in success:
            results['eips']['success'].append(f"{region}:{eip}")
        for eip in failed:
            results['eips']['failed'].append(f"{region}:{eip}")
    
    # 2. Delete ENIs for each region
    for region, eni_ids in regional_enis.items():
        success, failed = delete_enis(region, eni_ids)
        for eni in success:
            results['enis']['success'].append(f"{region}:{eni}")
        for eni in failed:
            results['enis']['failed'].append(f"{region}:{eni}")
    
    # 3. Summarize results
    total_success_eips = len(results['eips']['success'])
    total_failed_eips = len(results['eips']['failed'])
    total_success_enis = len(results['enis']['success'])
    total_failed_enis = len(results['enis']['failed'])
    
    # 4. Send results to Slack
    message = {
        "response_type": "ephemeral",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧹 Resource Deletion Results"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Successfully Deleted*\nEIPs: {total_success_eips}, ENIs: {total_success_enis}\n\n*Failed to Delete*\nEIPs: {total_failed_eips}, ENIs: {total_failed_enis}"
                }
            }
        ]
    }
    
    # Provide additional information if there are failed resources
    if total_failed_eips > 0 or total_failed_enis > 0:
        failed_details = []
        
        if total_failed_eips > 0:
            failed_details.append(f"*Failed EIPs*: {', '.join(results['eips']['failed'])}")
        
        if total_failed_enis > 0:
            failed_details.append(f"*Failed ENIs*: {', '.join(results['enis']['failed'])}")
        
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(failed_details)
            }
        })
    
    post_to_slack(response_url, message)
    
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }