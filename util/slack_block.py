from typing import Dict, Any, List, Optional
import json

def create_resource_detect_blocks(resources: Dict[str, Dict[str, List[str]]], 
                                  response_url: Optional[str] = None,
                                  title: str = "리소스 목록", 
                                  show_delete_button: bool = True) -> List[Dict[str, Any]]:
    """
    리전별 리소스 목록을 받아 Slack 블록을 생성합니다.
        
    Args:
        resources: 리소스 정보를 담은 딕셔너리 (형식: {"리전": {"리소스 유형": [리소스 ID 목록]}})
                  예: {"ap-northeast-2": {"eips": ["eip-1", "eip-2"], "enis": ["eni-1"]}}
        response_url: 슬랙 응답 URL (현재 버튼 value에는 사용 안 함)
        title: 블록 상단에 표시될 타이틀
        show_delete_button: 삭제 버튼 표시 여부
        
    Returns:
        Slack Block Kit 형식의 메시지 블록 리스트
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": title,
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # 리전별로 처리
    empty = True
    for region, resource_types in resources.items():
        # 리전에 리소스가 있는지 확인
        if any(resource_list for resource_list in resource_types.values()):
            empty = False
            # 리전 이름 추가
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*리전: {region}*"
                }
            })
            
            # 리소스 유형별로 처리
            for resource_type, resource_list in resource_types.items():
                if resource_list:  # 리소스가 있는 경우만 표시
                    resource_text = f"*{resource_type}*:\n"
                    for resource_id in resource_list:
                        resource_text += f"• `{resource_id}`\n"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": resource_text
                        }
                    })
    
    # 리소스가 없는 경우
    if empty:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "표시할 리소스가 없습니다."
            }
        })
    # 삭제 버튼 추가
    elif show_delete_button:
        blocks.append({
            "type": "divider"
        })
        
        # 버튼 value에는 resources만 포함
        button_value = {"resources": resources}
            
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗑️ 삭제",
                        "emoji": True
                    },
                    "style": "danger",
                    "value": json.dumps(button_value), # resources만 포함
                    "action_id": "delete"
                }
            ]
        })
    
    return blocks

def create_resource_delete_blocks(results: Dict[str, str], 
                                  
                                title: str = "리소스 목록", 
                                show_delete_button: bool = True) -> List[Dict[str, Any]]:
    
    # 삭제 결과 메시지 생성
    total_success = len(results["success"])
    total_failed = len(results["failed"])

    # 슬랙 메시지 블록 구성
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🗑️ 리소스 삭제 결과",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*성공:* {total_success}개 리소스 삭제됨\n*실패:* {total_failed}개 리소스 삭제 실패"
            }
        }
    ]

    # 실패한 리소스가 있는 경우 상세 정보 표시
    if total_failed > 0:
        failed_text = "*실패한 리소스 목록:*\n"
        for i, resource_id in enumerate(results["failed"], 1):
            failed_text += f"{i}. `{resource_id}`\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": failed_text
            }
        })

    if total_success > 0:
        success_text = "*성공한 리소스 목록:*\n"
        for i, resource_id in enumerate(results["success"], 1):
            success_text += f"{i}. `{resource_id}`\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": success_text
            }
        })
        
        

    return blocks
