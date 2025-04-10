import json
import base64
import urllib.parse
from typing import Dict, Any, Optional, Union

def parse_body(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    API Gateway 이벤트에서 body 부분만 파싱합니다.
    base64로 인코딩된 경우 디코딩하고, 
    application/json 또는 application/x-www-form-urlencoded 형식을 처리합니다.
    
    Args:
        event: API Gateway에서 전달된 Lambda 이벤트
        
    Returns:
        파싱된 body 딕셔너리 또는 None
    """
    # 1. body 추출
    body = event.get('body', '')
    if not body:
        # 이미 JSON 객체인지 확인 (Lambda URL로 직접 호출되는 경우 등)
        if event.get('type') == 'block_actions' and event.get('actions'):
            print("이벤트 객체 자체가 페이로드인 것으로 간주합니다.")
            return event
        return None
    
    # 2. base64 디코딩 (필요한 경우)
    if event.get('isBase64Encoded', False):
        try:
            body = base64.b64decode(body).decode('utf-8')
            print("Base64 디코딩 완료.")
        except Exception as e:
            print(f"Base64 디코딩 실패: {str(e)}")
            return None
    
    # 3. 컨텐츠 타입 확인
    headers = event.get('headers', {}) or {}
    content_type = headers.get('content-type', '') or headers.get('Content-Type', '')
    print(f"Content-Type: {content_type}")
    
    # 4. 형식에 맞게 파싱
    try:
        if 'application/json' in content_type:
            # JSON 형식인 경우
            parsed = json.loads(body)
            print(f"JSON 파싱 결과: {json.dumps(parsed)[:200]}...") # 로그 길이 제한
            return parsed
        elif 'application/x-www-form-urlencoded' in content_type:
            # URL 인코딩된 폼 데이터인 경우
            parsed = dict(urllib.parse.parse_qsl(body))
            print(f"URL 인코딩 파싱 결과: {json.dumps(parsed)[:200]}...") # 로그 길이 제한
            return parsed
        else:
            # 직접 JSON 파싱 시도 (content-type이 명확하지 않거나 없는 경우)
            try:
                parsed = json.loads(body)
                print(f"직접 JSON 파싱 결과: {json.dumps(parsed)[:200]}...") # 로그 길이 제한
                return parsed
            except json.JSONDecodeError:
                print(f"JSON으로 파싱할 수 없는 body입니다. Raw로 처리합니다.")
                return {"raw": body}
            except Exception as e:
                print(f"직접 JSON 파싱 중 오류: {str(e)}")
                return {"raw": body}
    except Exception as e:
        print(f"Body 파싱 실패: {str(e)}")
        return {"raw": body}

def get_slack_command_payload(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    API Gateway 이벤트에서 Slack 슬래시 커맨드 페이로드를 추출합니다.
    
    Args:
        event: API Gateway에서 전달된 Lambda 이벤트
        
    Returns:
        Slack 슬래시 커맨드 페이로드 또는 None
    """
    body_data = parse_body(event)
    if not body_data:
        return None
    
    # Slack 슬래시 커맨드인지 확인
    if 'command' in body_data and isinstance(body_data.get('command'), str) and body_data['command'].startswith('/'):
        return body_data
    
    return None

def get_slack_interactive_payload(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    API Gateway 이벤트에서 Slack 인터랙티브 페이로드(버튼 클릭 등)를 추출합니다.
    
    Args:
        event: API Gateway에서 전달된 Lambda 이벤트
        
    Returns:
        Slack 인터랙티브 페이로드 또는 None
    """
    # 직접 Lambda URL로 호출된 경우 또는 body가 이미 파싱된 경우
    if event.get('type') == 'block_actions' and event.get('actions'):
        print("직접 인터랙티브 페이로드 감지됨 (event 객체)")
        return event
    
    body_data = parse_body(event)
    if not body_data:
        return None
    
    # Slack 인터랙티브 메시지인지 확인 (URL 인코딩된 'payload' 키)
    if 'payload' in body_data:
        try:
            payload_str = body_data['payload']
            # payload_str이 실제 문자열인지 확인
            if isinstance(payload_str, str):
                payload = json.loads(payload_str)
                print(f"Payload 디코딩 결과: {json.dumps(payload)[:200]}...") # 로그 길이 제한
                # 타입이 block_actions인지 추가 확인
                if payload.get('type') == 'block_actions':
                    return payload
                else:
                    print(f"'payload' 내부의 타입이 'block_actions'가 아님: {payload.get('type')}")
            else:
                print("'payload' 키의 값이 문자열이 아닙니다.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Payload 디코딩 실패: {str(e)}")
    # body 자체가 인터랙티브 페이로드인 경우 (content-type: application/json)
    elif body_data.get('type') == 'block_actions' and body_data.get('actions'):
        print("Body 자체가 인터랙티브 페이로드인 것 감지됨 (파싱된 body)")
        return body_data
    
    return None

def get_action_id(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    파싱된 Slack 인터랙티브 페이로드에서 첫 번째 action_id를 추출합니다.
    오류 발생 시 None을 반환합니다.
    
    Args:
        payload: API Gateway 이벤트의 파싱된 body 또는 event 객체
        
    Returns:
        첫 번째 action_id 문자열 또는 None
    """
    try:
        if not payload:
            print("Action ID 추출 실패: 입력 페이로드가 없습니다.")
            return None

        # 'payload' 키가 있는지 확인 (URL 인코딩된 경우)
        if 'payload' in payload and isinstance(payload['payload'], str):
            print("'payload' 키에서 JSON 파싱 시도...")
            payload_dict = json.loads(payload['payload'])
        # body 자체가 페이로드인 경우 (application/json 또는 직접 호출)
        elif payload.get('type') == 'block_actions' and 'actions' in payload:
            print("입력 페이로드 자체가 block_actions 타입입니다.")
            payload_dict = payload
        else:
            print("Action ID 추출 실패: 유효한 인터랙티브 페이로드 형식이 아닙니다.")
            return None

        # action_id 추출
        actions = payload_dict.get('actions', [])
        if actions and isinstance(actions, list) and len(actions) > 0:
            first_action = actions[0]
            if isinstance(first_action, dict):
                action_id = first_action.get('action_id')
                if action_id and isinstance(action_id, str):
                    print(f"Action ID 추출 성공: {action_id}")
                    return action_id
        
        print("Action ID 추출 실패: actions 구조에서 action_id를 찾을 수 없습니다.")
        return None

    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        print(f"Action ID 추출 중 오류 발생: {type(e).__name__} - {str(e)}")
        return None
    except Exception as e:
        # 예상치 못한 다른 오류 처리
        print(f"Action ID 추출 중 예상치 못한 오류 발생: {type(e).__name__} - {str(e)}")
        return None

def create_slack_response(text: str, ephemeral: bool = True) -> Dict[str, Any]:
    """
    Slack API에 반환할 간단한 응답을 생성합니다.
    
    Args:
        text: 메시지 텍스트
        ephemeral: 메시지를 본인에게만 표시할지 여부
        
    Returns:
        API Gateway 응답 형식의 딕셔너리
    """
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "response_type": "ephemeral" if ephemeral else "in_channel",
            "text": text
        })
    }

