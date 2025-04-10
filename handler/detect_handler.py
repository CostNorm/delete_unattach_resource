import boto3
import concurrent.futures
import time
from eip.detector import detect_eips
from eni.detector import detect_enis
from util.slack import send_slack_block_response
from util.slack_block import create_resource_detect_blocks
from typing import Dict, Any, List

def get_all_regions():
    """Returns a list of all AWS regions."""
    ec2_client = boto3.client('ec2', region_name='us-east-1')  # Call from default region
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def search_region_resources(region):
    """Finds unused resources in a specific region."""
    try:
        print(f"Searching region {region}...")
        ec2 = boto3.client('ec2', region_name=region)
        
        # Search for unattached EIPs
        unused_eips = detect_eips(ec2)
        
        # Search for unattached ENIs
        unused_enis = detect_enis(ec2)
        
    
        result = {
            'region': region,
            'eips': unused_eips,
            'enis': unused_enis
        }
        return result
            
    except Exception as e:
        print(f"Error occurred while searching region {region}: {str(e)}")
        return {
            'region': region,
            'eips': [],
            'enis': [],
            'error': str(e)
        }

def find_unused_resources() -> Dict[str, Dict[str, List[str]] ]:
    """Asynchronously finds unused resources across all regions."""
    all_regions = get_all_regions()
    
    all_results = []
    
    # Use ThreadPoolExecutor for parallel region search
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks for each region
        future_to_region = {executor.submit(search_region_resources, region): region for region in all_regions}
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_region):
            region = future_to_region[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                all_results.append({
                    'region': region,
                    'eips': [],
                    'enis': [],
                    'error': str(e)
                })

    # Process results into the new format: {"eips": {"region": [...]}...}
    all_unused_resources = {}
    
    for result in all_results:
        region = result['region']
        if 'error' not in result:
            if result['eips']:
                if "eips" not in all_unused_resources:
                    all_unused_resources["eips"] = {}
                all_unused_resources["eips"][region] = result['eips']
            if result['enis']:
                if "enis" not in all_unused_resources:
                    all_unused_resources["enis"] = {}
                all_unused_resources["enis"][region] = result['enis']
    
    return all_unused_resources


def detect_handler(response_url: str):
    unused_resources = find_unused_resources()
    blocks = create_resource_detect_blocks(unused_resources, response_url=response_url)
    send_slack_block_response(response_url, blocks)
    
