import json
import boto3
import urllib.parse
import base64

def lambda_handler(event, context):
    # Initialize AWS Lambda client
    lambda_client = boto3.client('lambda')
    
    # Extract response_url from the API Gateway request
    response_url = None
    
    try:
        # Body may be URL-encoded when coming from API Gateway HTTP integration
        if 'body' in event and event['body']:
            # Check and decode base64 encoding
            body_str = event['body']
            if event.get('isBase64Encoded', False):
                body_str = base64.b64decode(body_str).decode('utf-8')
                print(f"Decoded body: {body_str}")
            
            # Parse URL-encoded string
            parsed_body = urllib.parse.parse_qs(body_str)
            print(f"Parsed body: {json.dumps(parsed_body)}")
            
            # Extract response_url parameter from Slack
            if 'response_url' in parsed_body:
                response_url = parsed_body['response_url'][0]
                print(f"Found response_url: {response_url}")
    except Exception as e:
        print(f"Error parsing request body: {str(e)}")
    
    try:
        # Invoke detectUnattachResource Lambda function asynchronously
        # Pass response_url in the payload
        payload = {'response_url': response_url} if response_url else {}
        print(f"Sending payload to detectUnattachResource: {json.dumps(payload)}")
        
        response = lambda_client.invoke(
            FunctionName='detectUnattachResource',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        print(f"Lambda invoke response: {response}")
        
        # Success message
        message = "Resource detection process has started."
    except Exception as e:
        # Error message
        message = f"An error occurred while executing resource detection: {str(e)}"
        print(f"Error invoking Lambda: {str(e)}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "https://slack.com",
                    "Access-Control-Allow-Credentials": "true"},
        "body": json.dumps({
            "response_type": "ephemeral",
            "text": message
        })
    }