def detect_eips(ec2_client):
    unused_eips = []
    addresses = ec2_client.describe_addresses()['Addresses']
    for address in addresses:
            if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                eip_id = address['AllocationId']
                unused_eips.append(eip_id)
    return unused_eips