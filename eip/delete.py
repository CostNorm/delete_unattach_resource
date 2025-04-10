import boto3

def delete_eip(ec2_client, eip_id):
    """
    EIP(Elastic IP)를 해제합니다.
    
    Args:
        ec2_client: boto3 EC2 클라이언트
        eip_id: 해제할 EIP의 AllocationId (예: 'eip-12345')
        
    Raises:
        Exception: EIP 해제 중 오류가 발생한 경우
    """
    try:
        # EIP 해제
        ec2_client.release_address(AllocationId=eip_id)
        print(f"✅ EIP {eip_id} 해제 성공")
        return True
    except Exception as e:
        print(f"❌ EIP {eip_id} 해제 실패: {str(e)}")
        # 예외를 다시 발생시켜 상위 함수에서 처리하도록 함
        raise