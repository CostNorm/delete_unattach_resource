import json
import boto3
import os
from util.simple_parser import get_slack_command_payload
from util.slack import return_slack_response
from handler.detect_handler import detect_handler
from handler.delete_handler import delete_handler, handle_delete_interaction
from util.simple_parser import parse_body
from util.simple_parser import get_action_id
from util.simple_parser import get_slack_interactive_payload
from handler.command_handler import command_handler
# AWS Lambda 클라이언트 초기화
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """
    메인 Lambda 핸들러 함수
    """
    print(f"Lambda 함수 호출됨. 이벤트: {json.dumps(event)}")

    # Slack 슬래시 커맨드 처리
    command_payload = get_slack_command_payload(event)
    if command_payload and command_payload.get('command') == '/cleanup-unattach':
        return command_handler(command_payload, lambda_client)

    # Slack 인터랙티브 메시지(버튼 클릭) 처리
    interactive_payload = get_slack_interactive_payload(event)
    if interactive_payload:
        return handle_delete_interaction(interactive_payload)

    # 내부 Lambda 호출 처리 (비동기 실행된 작업)
    if event.get('source') == 'lambda':
        action = event.get('action')
        print(f"내부 Lambda 호출 감지됨. action: {action}")
        # 비동기 호출 시 전달된 event 로그 출력
        print(f"내부 호출 이벤트: {json.dumps(event)}") 
        
        if action == 'detect':
            response_url = event.get('response_url', '')
            if response_url:
                return detect_handler(response_url)
            else:
                print("Detect 실행에 response_url이 없습니다.")
                return {"statusCode": 400, "body": "Missing response_url for detect action"}
        elif action == 'delete':
            response_url = event.get('response_url', '')
            resources = event.get('resources', {})
            if response_url and resources:
                print("delete_handler 호출")
                # delete_handler 호출 시 event 형식에 맞게 전달
                return delete_handler({
                    'response_url': response_url,
                    'resources': resources
                })
            else:
                print("삭제 실행에 필요한 정보(response_url 또는 resources)가 없습니다.")
                return {"statusCode": 400, "body": "Missing parameters for delete action"}
    
    # 어떤 조건에도 해당하지 않는 경우
    print("지원되지 않는 요청 타입입니다.")
    return return_slack_response("지원되지 않는 요청입니다. '/cleanup-unattach' 명령어를 사용하거나 메시지의 버튼을 클릭해주세요.")
    
    

