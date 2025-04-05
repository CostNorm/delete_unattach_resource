# AWS 미사용 리소스 감지 및 삭제

AWS 환경에서 사용되지 않는 리소스(미연결 EIP, ENI)를 감지하고 Slack을 통해 알림 및 삭제할 수 있는 AWS Lambda 기반 서버리스 솔루션입니다.

## 구성 요소

이 프로젝트는 모듈식 구조로 구성된 네 개의 AWS Lambda 함수로 이루어져 있습니다:

### 감지 플로우
1. **메시지 트리거 (detect/message/lambda_function.py)**:
   - API Gateway를 통한 Slack 명령어 요청 처리
   - 리소스 감지 Lambda 함수를 비동기적으로 호출

2. **리소스 감지 (detect/execute/lambda_function.py 및 detect/execute/find_unused_resources.py)**:
   - 모든 AWS 리전에서 동시에 연결되지 않은 EIP와 ENI를 스캔
   - 리소스 세부 정보와 대화형 삭제 버튼이 포함된 Slack 메시지 생성
   - 원래 응답 URL을 사용하여 결과를 Slack으로 전송

### 삭제 플로우
1. **삭제 요청 처리기 (delete/message/lambda_function.py)**:
   - API Gateway를 통한 Slack 버튼 클릭 이벤트 처리
   - 삭제가 시작되었다는 즉각적인 확인 메시지를 사용자에게 전송
   - 리소스 삭제 함수를 비동기적으로 호출

2. **리소스 삭제 실행기 (delete/execute/lambda_function.py 및 delete/execute/delete.py)**:
   - 모든 리전에서 지정된 리소스 삭제
   - 성공 및 실패한 삭제 작업 추적
   - 상세한 결과를 Slack으로 전송

## 작동 방식

1. 사용자가 Slack에서 명령어를 입력하면 감지 플로우가 시작됩니다.
2. 시스템은 모든 AWS 리전에서 동시에 미사용 리소스를 스캔합니다.
3. 미사용 리소스가 발견되면 세부 정보와 삭제 버튼이 포함된 메시지가 Slack으로 전송됩니다.
4. 사용자가 삭제 버튼을 클릭하면 삭제 플로우가 시작됩니다.
5. 시스템은 각 리소스를 삭제하고 결과 요약을 생성합니다.
6. 최종 보고서가 Slack으로 전송되어 성공적으로 삭제된 리소스와 실패한 리소스를 보여줍니다.

## 아키텍처 개선 사항

- **동시 처리**: 모든 AWS 리전의 리소스가 병렬로 처리되어 더 빠른 실행이 가능합니다.
- **비동기 작업**: 모든 함수는 비동기적으로 작동하여 빠른 응답을 제공합니다.
- **모듈식 구조**: 코드가 관심사를 분리하는 모듈식 방식으로 구성되어 있습니다:
  - `detect/message`: 초기 요청 처리
  - `detect/execute`: 리소스 스캔 로직
  - `delete/message`: 삭제 요청 처리
  - `delete/execute`: 실제 리소스 삭제 로직

## 설정 방법

1. Lambda 함수를 AWS에 배포합니다:
   ```bash
   # Windows의 경우
   Compress-Archive -Path .\detect\* -DestinationPath .\detect.zip -Force
   aws lambda update-function-code --function-name detectUnattachResource --zip-file fileb://detect.zip

   # 삭제 함수의 경우
   Compress-Archive -Path .\delete\* -DestinationPath .\delete.zip -Force
   aws lambda update-function-code --function-name executeDeleteUnattach --zip-file fileb://delete.zip
   ```

2. API Gateway 구성:
   - 두 개의 HTTP API 엔드포인트 생성:
     - `/sendDetectionMessage`: 감지 메시지 함수에 연결
     - `/deleteUnattachedResources`: 삭제 메시지 함수에 연결

3. Slack 구성:
   - 슬래시 명령어 기능이 있는 Slack 앱 생성
   - 슬래시 명령어가 감지 API 엔드포인트를 가리키도록 설정
   - 대화형 구성 요소가 삭제 API 엔드포인트를 사용하도록 구성

4. IAM 권한 설정:
   - Lambda 함수에는 모든 리전에 걸친 EC2 읽기/수정 권한 필요
   - Lambda 간 호출을 위한 교차 호출 권한 필요

## 보안 고려사항

- Lambda 함수에는 EC2 리소스 조회 및 삭제 권한이 필요합니다.
- API Gateway 엔드포인트는 적절한 인증을 구현해야 합니다.
- Slack 요청에 대한 서명 확인 구현을 고려하세요.
- 민감한 구성에는 환경 변수를 사용하세요.

## 개발

코드는 쉬운 유지관리와 확장을 위해 구조화되어 있습니다:

```
.
├── detect/
│   ├── message/            # 초기 Slack 명령어 핸들러
│   └── execute/            # 리소스 감지 로직
│       ├── util/           # 공유 유틸리티
│       └── find_unused_resources.py
├── delete/
│   ├── message/            # 삭제 요청 핸들러
│   └── execute/            # 리소스 삭제 로직
│       ├── util/           # 공유 유틸리티
│       └── delete.py       # 삭제 구현
```