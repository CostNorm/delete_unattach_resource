# AWS 미사용 리소스 감지 및 삭제 (delete_unattach_resource)

AWS 환경에서 사용되지 않는 리소스(미연결 EIP, ENI)를 감지하고 Slack을 통해 알림 및 삭제할 수 있는 AWS Lambda 기반 솔루션입니다.

## 구성 요소

이 프로젝트는 세 개의 AWS Lambda 함수로 구성되어 있습니다:

1. **detect-unattach-resource.py**: 
   - 미사용 중인 EIP(Elastic IP)와 ENI(Elastic Network Interface) 리소스를 감지
   - Slack으로 미사용 리소스 목록과 삭제 버튼을 포함한 메시지 전송

2. **delete-unattach-resource.py**:
   - Slack의 삭제 버튼 클릭 이벤트 처리
   - 삭제 요청을 SQS 큐로 전송하고 사용자에게 확인 메시지 응답

3. **real-delete-unattach-resource.py**:
   - SQS 큐에서 삭제 요청을 수신하여 실제 리소스 삭제 작업 수행
   - 삭제 결과를 Slack으로 응답

## 작동 방식

1. slack에서 명령어를 입력하면, `detect-unattach-resource` 함수가 호출됩니다.
2. 미사용 리소스가 발견되면 Slack에 알림이 전송되고 삭제 버튼이 표시됩니다.
3. 사용자가 삭제 버튼을 클릭하면 `delete-unattach-resource` 함수가 호출됩니다.
4. 삭제 요청은 SQS 큐에 전송되고 사용자에게 요청 접수 메시지가 표시됩니다.
5. `real-delete-unattach-resource` 함수가 SQS 큐에서 메시지를 처리하고 실제 리소스를 삭제합니다.
6. 삭제 결과가 Slack으로 전송됩니다.

## 설정 방법

1. 세 개의 Lambda 함수를 AWS Lambda 콘솔에 배포합니다.
2. SQS 큐 `delete-unattach-queue`를 생성하고 `real-delete-unattach-resource` 함수의 트리거로 설정합니다.
3. Slack 앱을 설정하고 인터랙티브 컴포넌트 URL을 `delete-unattach-resource` 함수의 API Gateway URL로 지정합니다.
4. `detect-unattach-resource` 함수를 CloudWatch Events/EventBridge로 스케줄링하거나 Slack 슬래시 명령어로 호출 가능하도록 설정합니다.

## 보안 고려사항

- Lambda 함수에는 EC2 리소스 조회 및 삭제 권한이 필요합니다.
- SQS 메시지 수신 및 삭제 권한 설정이 필요합니다.
- Slack과의 통신은 보안을 위해 URL 검증 및 적절한 인증을 구현해야 합니다.