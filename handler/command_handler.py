import json
import os
from util.slack import return_slack_response

def command_handler(command_payload, lambda_client):
    """
    Slack 슬래시 커맨드 '/cleanup-unattach'를 처리합니다.
    """
    print("슬래시 커맨드 '/cleanup-unattach' 감지됨")
    # 응답 URL 저장
    response_url = command_payload.get('response_url', '')
    print(f"response_url: {response_url}")
    # 현재 Lambda 함수 이름 가져오기
    function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    
    if function_name:
        # 자기 자신을 비동기적으로 호출 (detect 작업 실행)
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # 비동기 호출
            Payload=json.dumps({
                'source': 'lambda',
                'action': 'detect',
                'response_url': response_url
            })
        )
        
        print(f"Lambda 함수 '{function_name}' 비동기 호출 성공 (detect)")
        return return_slack_response("리소스 탐색을 시작합니다...")
    else:
        print("Lambda 함수 이름을 가져올 수 없습니다.")
        return return_slack_response("Lambda 함수 이름을 가져올 수 없습니다.") 