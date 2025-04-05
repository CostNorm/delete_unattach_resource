import boto3
import concurrent.futures
import time


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
        unused_eips = []
        addresses = ec2.describe_addresses()['Addresses']
        for address in addresses:
            if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                eip_id = address['AllocationId']
                unused_eips.append(eip_id)
        
        if unused_eips:
            print(f"Found {len(unused_eips)} unused EIPs in region {region}")
        
        # Search for unattached ENIs
        unused_enis = []
        enis = ec2.describe_network_interfaces(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )['NetworkInterfaces']
        
        for eni in enis:
            eni_id = eni['NetworkInterfaceId']
            unused_enis.append(eni_id)
        
        if unused_enis:
            print(f"Found {len(unused_enis)} unused ENIs in region {region}")
            
        # Return region and results
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

def find_unused_resources():
    """Asynchronously finds unused resources across all regions."""
    all_regions = get_all_regions()
    print(f"Regions to search: {all_regions}")
    
    start_time = time.time()
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
                print(f"Exception occurred while processing region {region}: {str(e)}")
                all_results.append({
                    'region': region,
                    'eips': [],
                    'enis': [],
                    'error': str(e)
                })
    
    # Process results
    all_unused_eips = {}
    all_unused_enis = {}
    
    for result in all_results:
        region = result['region']
        if 'error' not in result:
            if result['eips']:
                all_unused_eips[region] = result['eips']
            if result['enis']:
                all_unused_enis[region] = result['enis']
    
    end_time = time.time()
    print(f"Total search time: {end_time - start_time:.2f} seconds")
    
    return all_unused_eips, all_unused_enis