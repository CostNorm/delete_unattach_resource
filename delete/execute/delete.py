import boto3

def delete_eips(region, eip_ids):
    """지정된 리전에서 EIP 리소스 삭제"""
    if not eip_ids:
        return [], []
    
    ec2 = boto3.client('ec2', region_name=region)
    success_ids = []
    failed_ids = []
    
    for eip_id in eip_ids:
        try:
            ec2.release_address(AllocationId=eip_id)
            success_ids.append(eip_id)
            print(f"✅ EIP {eip_id} 삭제 성공 (리전: {region})")
        except Exception as e:
            print(f"❌ EIP {eip_id} 삭제 실패 (리전: {region}): {str(e)}")
            failed_ids.append(eip_id)
    
    return success_ids, failed_ids

def delete_enis(region, eni_ids):
    """지정된 리전에서 ENI 리소스 삭제"""
    if not eni_ids:
        return [], []
    
    ec2 = boto3.client('ec2', region_name=region)
    success_ids = []
    failed_ids = []
    
    for eni_id in eni_ids:
        try:
            ec2.delete_network_interface(NetworkInterfaceId=eni_id)
            success_ids.append(eni_id)
            print(f"✅ ENI {eni_id} 삭제 성공 (리전: {region})")
        except Exception as e:
            print(f"❌ ENI {eni_id} 삭제 실패 (리전: {region}): {str(e)}")
            failed_ids.append(eni_id)
    
    return success_ids, failed_ids