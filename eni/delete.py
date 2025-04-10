import boto3

def delete_eni(ec2_client, eni_id):
    """
    ENI(Elastic Network Interface)를 삭제합니다.
    
    Args:
        ec2_client: boto3 EC2 클라이언트
        eni_id: 삭제할 ENI의 ID (예: 'eni-12345')
        
    Raises:
        Exception: ENI 삭제 중 오류가 발생한 경우
    """
    try:
        # ENI 삭제
        ec2_client.delete_network_interface(NetworkInterfaceId=eni_id)
        print(f"✅ ENI {eni_id} 삭제 성공")
        return True
    except Exception as e:
        print(f"❌ ENI {eni_id} 삭제 실패: {str(e)}")
        # 예외를 다시 발생시켜 상위 함수에서 처리하도록 함
        raise