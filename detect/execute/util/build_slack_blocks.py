import json


def build_slack_blocks(regional_eips, regional_enis):
    blocks = []
    
    total_eips = sum(len(eips) for eips in regional_eips.values())
    total_enis = sum(len(enis) for enis in regional_enis.values())
    
    if not regional_eips and not regional_enis:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*No unused resources found in any region.*"}
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Unused resources have been found across all regions.*\nTotal EIPs: {total_eips}, Total ENIs: {total_enis}"}
        })
        
        # Add regional EIP information
        if regional_eips:
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": "Unused EIPs"}
            })
            
            for region, eips in regional_eips.items():
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{region}* ({len(eips)}): {', '.join(eips)}"}
                })
        
        # Add regional ENI information
        if regional_enis:
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": "Unused ENIs"}
            })
            
            for region, enis in regional_enis.items():
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{region}* ({len(enis)}): {', '.join(enis)}"}
                })
        
        # Add delete button
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Delete"},
                    "style": "danger",
                    "value": json.dumps({"eips": regional_eips, "enis": regional_enis}),
                    "action_id": "delete_unused"
                }
            ]
        })
    
    return blocks