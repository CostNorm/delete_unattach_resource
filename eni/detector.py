import json

def detect_enis(ec2_client):
    unused_enis = []
    enis = ec2_client.describe_network_interfaces(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )['NetworkInterfaces']
        
    for eni in enis:
        eni_id = eni['NetworkInterfaceId']
        unused_enis.append(eni_id)
    
    return unused_enis



