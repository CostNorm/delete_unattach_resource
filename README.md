# AWS 미사용 리소스 정리 Lambda (Slack 연동)

AWS 환경에서 사용되지 않는 특정 리소스(현재 Elastic IP, ENI)를 탐지하고, Slack을 통해 사용자에게 알린 후 인터랙션을 통해 해당 리소스를 삭제할 수 있도록 지원하는 서버리스 애플리케이션입니다.

## 주요 기능

*   **미사용 리소스 탐지**: 지정된 AWS 리전에서 연결되지 않은 EIP와 ENI를 탐색합니다.
*   **Slack 알림**: 탐지된 미사용 리소스 목록을 Slack 메시지로 전송합니다.
*   **인터랙티브 삭제**: Slack 메시지에 포함된 버튼을 통해 사용자가 직접 리소스 삭제를 요청할 수 있습니다.
*   **삭제 결과 보고**: 삭제 작업의 성공/실패 결과를 Slack으로 다시 알려줍니다.
*   **서버리스 아키텍처**: AWS Lambda와 API Gateway를 사용하여 별도의 서버 관리 없이 운영됩니다.

## 아키텍처

이 솔루션은 단일 AWS Lambda 함수와 API Gateway를 중심으로 구성됩니다.

1.  **API Gateway**: Slack으로부터 오는 슬래시 커맨드(` /cleanup-unattach`) 및 버튼 클릭 인터랙션 요청을 수신하여 Lambda 함수를 트리거합니다.
2.  **AWS Lambda (`lambda_function.py`)**:
    *   **요청 라우팅**: 수신된 이벤트 유형(슬래시 커맨드, 버튼 클릭, 내부 호출)에 따라 적절한 핸들러 모듈로 요청을 전달합니다.
    *   **비동기 자체 호출**: 리소스 탐지 및 삭제와 같이 시간이 소요될 수 있는 작업은 Lambda 함수 자체를 비동기적으로 호출(`InvocationType='Event'`)하여 백그라운드에서 처리합니다. 이를 통해 Slack의 3초 응답 제한을 준수하고 사용자 경험을 개선합니다.
    *   **상태 관리**: 비동기 호출 시 필요한 정보(Slack 응답 URL, 삭제할 리소스 목록 등)를 이벤트 페이로드에 담아 전달합니다.

## 워크플로우

1.  **탐지 시작**: 사용자가 Slack 채널에서 `/cleanup-unattach` 명령어를 실행합니다.
2.  **커맨드 처리**: API Gateway를 통해 Lambda 함수가 호출되고, `command_handler`가 실행됩니다.
3.  **비동기 탐지 호출**: `command_handler`는 즉시 Slack에 "탐색 시작" 메시지를 보내고, `action: detect` 와 응답 URL을 포함하여 Lambda 함수를 비동기적으로 호출합니다.
4.  **리소스 탐지**: 비동기 호출된 Lambda 함수는 `detect_handler`를 실행합니다.
5.  **탐지 결과 전송**: `detect_handler`는 모든 리전에서 미사용 EIP/ENI를 찾고, 결과와 함께 "삭제" 버튼이 포함된 Slack 메시지를 응답 URL로 전송합니다.
6.  **삭제 요청**: 사용자가 Slack 메시지의 "삭제" 버튼을 클릭합니다.
7.  **인터랙션 처리**: API Gateway를 통해 Lambda 함수가 호출되고, `handle_delete_interaction` (delete_handler.py 내) 함수가 실행됩니다.
8.  **비동기 삭제 호출**: `handle_delete_interaction`은 즉시 Slack에 "삭제 요청 접수" 메시지를 보내고, `action: delete`, 삭제할 리소스 정보, 응답 URL을 포함하여 Lambda 함수를 비동기적으로 호출합니다.
9.  **리소스 삭제**: 비동기 호출된 Lambda 함수는 `delete_handler`를 실행합니다.
10. **삭제 결과 전송**: `delete_handler`는 요청된 리소스를 삭제하고, 성공/실패 결과를 요약하여 Slack 메시지를 응답 URL로 전송합니다.

## 코드 구조

```
.
├── lambda_function.py        # 메인 Lambda 핸들러, 요청 라우팅
├── handler/                  # 요청 타입별 처리 로직
│   ├── command_handler.py    # 슬래시 커맨드 처리
│   ├── detect_handler.py     # 미사용 리소스 탐지 로직
│   └── delete_handler.py     # 삭제 인터랙션 처리 및 실제 삭제 로직
├── util/                     # 유틸리티 함수
│   ├── simple_parser.py      # Slack 페이로드 파싱
│   ├── slack.py              # Slack API 연동 (메시지 전송)
│   └── slack_block.py        # Slack Block Kit 메시지 생성
├── eip/                      # Elastic IP 관련 로직
│   ├── detector.py           # EIP 탐지
│   └── delete.py             # EIP 삭제
├── eni/                      # ENI 관련 로직
│   ├── detector.py           # ENI 탐지
│   └── delete.py             # ENI 삭제
├── README.md                 # 프로젝트 설명 (이 파일)
└── .gitignore
```

## 설정 및 배포

1.  **IAM 역할 생성**: Lambda 함수가 사용할 IAM 역할을 생성합니다. 필요한 권한은 다음과 같습니다:
    *   `ec2:DescribeAddresses`, `ec2:DescribeNetworkInterfaces` (리소스 탐지)
    *   `ec2:ReleaseAddress`, `ec2:DeleteNetworkInterface` (리소스 삭제)
    *   `lambda:InvokeFunction` (자체 비동기 호출)
    *   CloudWatch Logs 관련 권한 (로깅)

2.  **Lambda 함수 생성**:
    *   Python 런타임을 사용하여 Lambda 함수를 생성합니다.
    *   생성된 IAM 역할을 연결합니다.
    *   환경 변수를 설정합니다 (필요한 경우).
    *   코드(.py 파일 및 필요한 라이브러리)를 zip으로 압축하여 업로드합니다. 또는 소스 코드 리포지토리와 직접 연동할 수 있습니다.

3.  **API Gateway 설정**:
    *   HTTP API 또는 REST API를 생성합니다.
    *   Slack 요청을 처리할 라우트(예: `/slack/events`)를 생성하고 Lambda 함수 통합을 설정합니다.

4.  **Slack 앱 설정**:
    *   Slack 앱을 생성합니다.
    *   **Slash Commands**: `/cleanup-unattach` 명령어를 생성하고 API Gateway 엔드포인트 URL을 Request URL로 설정합니다.
    *   **Interactivity & Shortcuts**: Interactivity를 활성화하고 API Gateway 엔드포인트 URL을 Request URL로 설정합니다.
    *   필요한 OAuth 권한(예: `commands`, `chat:write`)을 앱에 부여하고 워크스페이스에 설치합니다.

5.  **배포**: 코드를 Lambda 함수에 배포합니다. (예: zip 파일 업로드, Serverless Framework, AWS SAM 등 사용)

## 보안 고려 사항

*   **IAM 최소 권한 원칙**: Lambda 함수에는 필요한 최소한의 권한만 부여합니다.
*   **API Gateway Authorizer**: 필요하다면 API Gateway에 Authorizer(예: Lambda Authorizer)를 설정하여 요청을 검증합니다.
*   **Slack 요청 검증**: Slack 요청의 서명(Signing Secret)을 검증하여 요청이 실제로 Slack에서 온 것인지 확인하는 로직을 Lambda 함수에 추가하는 것이 좋습니다. (`simple_parser.py` 등에 구현 가능)
*   **환경 변수**: Slack Bot Token 등 민감한 정보는 코드에 하드코딩하지 않고 환경 변수 또는 AWS Secrets Manager를 사용합니다.

## 향후 개선 사항

*   더 많은 리소스 타입 지원 (예: 미연결 EBS 볼륨, 미사용 로드 밸런서 등)
*   비용 절감 예상액 계산 및 알림
*   Slack 외 다른 알림 채널 지원 (이메일 등)
*   Terraform 또는 AWS CDK를 사용한 인프라 코드화(IaC)