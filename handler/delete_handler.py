import boto3
import json
import time
import os
import sys

# 상위 디렉토리를 경로에 추가하여 모듈을 찾을 수 있도록 합니다
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eni.delete import delete_eni
from eip.delete import delete_eip
from util.slack import send_slack_block_response
from util.slack import send_slack_text_response
from util.slack_block import create_resource_delete_blocks
from util.slack import return_slack_response

# AWS Lambda 클라이언트 초기화 (interactive handler에서 사용)
lambda_client = boto3.client('lambda')

def handle_delete_interaction(interactive_payload):
    """
    Slack 인터랙티브 메시지(삭제 버튼 클릭)를 처리하고 delete_handler를 비동기 호출합니다.
    """
    print(f"인터랙티브 페이로드 감지됨: {json.dumps(interactive_payload)}")
    
    # 액션 ID 확인 (block_actions 타입)
    if interactive_payload.get('type') == 'block_actions':
        actions = interactive_payload.get('actions', [])
        if actions and actions[0].get('action_id') == 'delete':
            print("삭제 버튼 클릭 감지됨")
            response_url = interactive_payload.get('response_url', '')
            print(f"인터랙티브 response_url: {response_url}")
            
            try:
                value_str = actions[0].get('value', '{}')
                resources_data = json.loads(value_str)
                resources = resources_data.get('resources', {})
                print(f"삭제할 리소스: {json.dumps(resources)}")
                
                function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
                
                if function_name and response_url and resources:
                    lambda_payload = {
                        'source': 'lambda',
                        'action': 'delete',
                        'response_url': response_url,
                        'resources': resources
                    }
                    print(f"비동기 호출 Payload: {json.dumps(lambda_payload)}")
                    lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType='Event',
                        Payload=json.dumps(lambda_payload)
                    )
                    print(f"Lambda 함수 '{function_name}' 비동기 호출 성공 (delete)")
                    
                    return {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"text": "삭제 요청을 받았습니다. 잠시 후 결과가 전송됩니다."})
                    }
                else:
                    error_msg = "Lambda 함수 정보, 응답 URL 또는 리소스 정보를 가져올 수 없습니다."
                    print(error_msg)
                    return return_slack_response(error_msg)
                
            except Exception as e:
                error_msg = f"인터랙티브 메시지 처리 중 오류 발생: {str(e)}"
                print(error_msg)
                return return_slack_response(error_msg)
    
    print("처리할 수 없는 인터랙션 타입입니다.")
    return return_slack_response("알 수 없는 인터랙션입니다.")

def delete_resources(resources, response_url):
    """
    각 리소스 타입별, 리전별로 리소스를 삭제합니다.
    
    Args:
        resources: 타입별 리소스 정보가 담긴 딕셔너리
                  형식: {"리소스 타입": {"리전": [리소스 ID 목록]}}
                  예: {"eips": {"ap-northeast-2": ["eipalloc-xxx"]}, "enis": {"ap-northeast-2": ["eni-xxx"]}}
        response_url: 슬랙 응답 URL
        
    Returns:
        삭제 결과를 담은 딕셔너리
    """
    # 삭제 결과 저장
    results = {
        "success": [],  # 성공한 리소스 목록
        "failed": []    # 실패한 리소스 목록
    }
    
    # 리소스 타입별로 처리 (eips, enis 등)
    for resource_type, regions in resources.items():
        print(f"리소스 타입 {resource_type} 처리 중...")
        
        # 리전별로 처리
        for region, resource_ids in regions.items():
            print(f"  리전 {region} 처리 중...")
            
            if not resource_ids:
                print(f"  리전 {region}에 처리할 {resource_type}가 없습니다.")
                continue
            
            # 리전별 EC2 클라이언트 생성
            try:
                print(f"  리전 {region}에 대한 EC2 클라이언트 생성 중...")
                ec2_client = boto3.client('ec2', region_name=region)
                
                # 리소스 타입에 따라 적절한 삭제 함수 호출
                for resource_id in resource_ids:
                    try:
                        if resource_type == "eips":
                            print(f"    EIP 삭제 중: {resource_id} (리전: {region})")
                            delete_eip(ec2_client, resource_id)
                            results["success"].append(f"{region}:{resource_type}:{resource_id}")
                            print(f"    EIP 삭제 성공: {resource_id}")
                        elif resource_type == "enis":
                            print(f"    ENI 삭제 중: {resource_id} (리전: {region})")
                            delete_eni(ec2_client, resource_id)
                            results["success"].append(f"{region}:{resource_type}:{resource_id}")
                            print(f"    ENI 삭제 성공: {resource_id}")
                        else:
                            print(f"    지원되지 않는 리소스 타입: {resource_type}")
                            results["failed"].append(f"{region}:{resource_type}:{resource_id}")
                    except Exception as e:
                        print(f"    {resource_type} 삭제 실패: {resource_id} - {str(e)}")
                        results["failed"].append(f"{region}:{resource_type}:{resource_id}")
            
            except Exception as e:
                print(f"  리전 {region}에 대한 EC2 클라이언트 생성 실패: {str(e)}")
                # 이 리전의 모든 리소스를 실패로 표시
                for resource_id in resource_ids:
                    results["failed"].append(f"{region}:{resource_type}:{resource_id}")

    return results

def send_delete_result(results, response_url):
    blocks = create_resource_delete_blocks(results, title="리소스 삭제 결과", show_delete_button=False)
    send_slack_block_response(response_url, blocks)

def delete_handler(event):
    """
    삭제 요청을 처리하는 Lambda 핸들러 함수
    
    Args:
        event: 요청 이벤트 객체
        
    Returns:
        Lambda 응답 객체
    """
    print("리소스 삭제 핸들러 시작...")
    print(f"이벤트: {json.dumps(event)}")
    
    # 응답 URL 가져오기
    response_url = event.get('response_url', '')
    if not response_url:
        print("응답 URL이 제공되지 않았습니다.")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': '응답 URL이 제공되지 않았습니다.'})
        }
    
    # 삭제할 리소스 정보 가져오기
    resources = event.get('resources', {})
    if not resources:
        print("삭제할 리소스 정보가 제공되지 않았습니다.")
        send_slack_text_response(
            response_url=response_url,
            message="삭제할 리소스 정보가 제공되지 않았습니다.",
            ephemeral=False
        )
        return {
            'statusCode': 400,
            'body': json.dumps({'message': '삭제할 리소스 정보가 제공되지 않았습니다.'})
        }
    
    try:
    
        results = delete_resources(resources, response_url)
        send_delete_result(results, response_url)
    
    except Exception as e:
        print(f"리소스 삭제 중 오류 발생: {str(e)}")
        
        # 오류 발생 시 슬랙으로 오류 메시지 전송
        send_slack_text_response(
            response_url=response_url,
            message=f"리소스 삭제 중 오류가 발생했습니다: {str(e)}",
            ephemeral=False
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# 테스트 코드
# if __name__ == "__main__":
#     print("=== delete_resources 테스트 시작 ===")
    
#     all_resources = find_unused_resources()
#     print(f"모든 리소스: {all_resources}")
#     delete_resources(all_resources, "https://hooks.slack.com/commands/T00000000/1234567890/abcdefghijklmnopqrstuvwxyz");

#     print("=== delete_resources 테스트 종료 ===")
