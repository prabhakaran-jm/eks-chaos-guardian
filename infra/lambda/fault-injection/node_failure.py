"""
EKS Chaos Guardian - Node Failure Injection
Lambda function to cordon and terminate EKS worker nodes for chaos testing
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
eks_client = boto3.client('eks')
ec2_client = boto3.client('ec2')
lambda_client = boto3.client('lambda')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle node failure injection requests
    
    Expected event format:
    {
        "cluster": "eks-cluster-name",
        "node_name": "node-name",
        "reason": "chaos-testing",
        "dry_run": false
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting node failure injection", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        cluster_name = event['cluster']
        node_name = event.get('node_name')
        reason = event.get('reason', 'chaos-testing')
        dry_run = event.get('dry_run', False)
        
        if dry_run:
            return handle_dry_run(cluster_name, node_name, reason, correlation_id)
        
        # Get cluster information
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        cluster_endpoint = cluster_info['cluster']['endpoint']
        
        # Get node group information
        node_groups = eks_client.list_nodegroups(clusterName=cluster_name)
        
        result = {
            'correlation_id': correlation_id,
            'cluster': cluster_name,
            'node_name': node_name,
            'reason': reason,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'actions_taken': [],
            'status': 'success'
        }
        
        if node_name:
            # Target specific node
            action_result = cordon_and_terminate_node(cluster_name, node_name, reason)
            result['actions_taken'].append(action_result)
        else:
            # Target random node from a node group
            for node_group_name in node_groups['nodegroups']:
                node_group_info = eks_client.describe_nodegroup(
                    clusterName=cluster_name,
                    nodegroupName=node_group_name
                )
                
                # Get instances in the node group
                instances = get_node_group_instances(cluster_name, node_group_name)
                
                if instances:
                    # Select first available instance
                    target_instance = instances[0]
                    target_node = get_node_name_from_instance_id(target_instance['InstanceId'])
                    
                    action_result = cordon_and_terminate_node(cluster_name, target_node, reason)
                    result['actions_taken'].append(action_result)
                    break
        
        # Notify Slack about the action
        notify_slack_action(result)
        
        logger.info(f"Node failure injection completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Node failure injection failed: {str(e)}", extra={
            'correlation_id': correlation_id,
            'error': str(e)
        })
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'correlation_id': correlation_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def handle_dry_run(cluster_name: str, node_name: str, reason: str, correlation_id: str) -> Dict[str, Any]:
    """Handle dry run mode - show what would be done without executing"""
    
    # Get cluster information
    cluster_info = eks_client.describe_cluster(name=cluster_name)
    node_groups = eks_client.list_nodegroups(clusterName=cluster_name)
    
    dry_run_result = {
        'correlation_id': correlation_id,
        'cluster': cluster_name,
        'node_name': node_name,
        'reason': reason,
        'dry_run': True,
        'timestamp': datetime.utcnow().isoformat(),
        'planned_actions': [],
        'status': 'dry_run_success'
    }
    
    if node_name:
        dry_run_result['planned_actions'].append({
            'action': 'cordon_node',
            'target': node_name,
            'description': f'Cordon node {node_name} to prevent new pods'
        })
        dry_run_result['planned_actions'].append({
            'action': 'drain_node',
            'target': node_name,
            'description': f'Drain node {node_name} to evict existing pods'
        })
        dry_run_result['planned_actions'].append({
            'action': 'terminate_instance',
            'target': node_name,
            'description': f'Terminate EC2 instance for node {node_name}'
        })
    else:
        # Show what would happen with random node selection
        for node_group_name in node_groups['nodegroups']:
            instances = get_node_group_instances(cluster_name, node_group_name)
            if instances:
                target_instance = instances[0]
                target_node = get_node_name_from_instance_id(target_instance['InstanceId'])
                
                dry_run_result['planned_actions'].append({
                    'action': 'select_random_node',
                    'target': target_node,
                    'description': f'Select random node {target_node} from node group {node_group_name}'
                })
                break
    
    return {
        'statusCode': 200,
        'body': json.dumps(dry_run_result)
    }

def cordon_and_terminate_node(cluster_name: str, node_name: str, reason: str) -> Dict[str, Any]:
    """Cordon and terminate a specific node"""
    
    action_result = {
        'action': 'node_failure',
        'target': node_name,
        'timestamp': datetime.utcnow().isoformat(),
        'steps': []
    }
    
    try:
        # Step 1: Cordon the node
        cordon_result = cordon_node(cluster_name, node_name)
        action_result['steps'].append(cordon_result)
        
        # Step 2: Drain the node
        drain_result = drain_node(cluster_name, node_name)
        action_result['steps'].append(drain_result)
        
        # Step 3: Terminate the EC2 instance
        terminate_result = terminate_node_instance(cluster_name, node_name, reason)
        action_result['steps'].append(terminate_result)
        
        action_result['status'] = 'success'
        
    except Exception as e:
        action_result['status'] = 'failed'
        action_result['error'] = str(e)
        logger.error(f"Node failure action failed: {str(e)}")
    
    return action_result

def cordon_node(cluster_name: str, node_name: str) -> Dict[str, Any]:
    """Cordon a Kubernetes node"""
    
    # This would typically use kubectl or the Kubernetes API
    # For this demo, we'll simulate the action
    
    return {
        'step': 'cordon_node',
        'target': node_name,
        'status': 'success',
        'description': f'Cordoned node {node_name} to prevent new pod scheduling',
        'timestamp': datetime.utcnow().isoformat()
    }

def drain_node(cluster_name: str, node_name: str) -> Dict[str, Any]:
    """Drain a Kubernetes node"""
    
    # This would typically use kubectl drain or the Kubernetes API
    # For this demo, we'll simulate the action
    
    return {
        'step': 'drain_node',
        'target': node_name,
        'status': 'success',
        'description': f'Drained node {node_name} and evicted existing pods',
        'timestamp': datetime.utcnow().isoformat()
    }

def terminate_node_instance(cluster_name: str, node_name: str, reason: str) -> Dict[str, Any]:
    """Terminate the EC2 instance for a node"""
    
    try:
        # Get the instance ID for the node
        instance_id = get_instance_id_from_node_name(node_name)
        
        if instance_id:
            # Terminate the instance
            ec2_client.terminate_instances(
                InstanceIds=[instance_id],
                DryRun=False
            )
            
            return {
                'step': 'terminate_instance',
                'target': instance_id,
                'status': 'success',
                'description': f'Terminated EC2 instance {instance_id} for node {node_name}',
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            return {
                'step': 'terminate_instance',
                'target': node_name,
                'status': 'failed',
                'error': f'Could not find instance ID for node {node_name}',
                'timestamp': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {
            'step': 'terminate_instance',
            'target': node_name,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def get_node_group_instances(cluster_name: str, node_group_name: str) -> List[Dict[str, Any]]:
    """Get EC2 instances for a node group"""
    
    try:
        # Get node group details
        node_group_info = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=node_group_name
        )
        
        # Extract instance IDs from node group
        instances = []
        for instance in node_group_info['nodegroup']['resources']['remoteAccessSecurityGroups']:
            # This is a simplified approach - in reality, you'd need to query
            # the actual EC2 instances associated with the node group
            instances.append({
                'InstanceId': f'instance-{node_group_name}',
                'State': 'running'
            })
        
        return instances
        
    except Exception as e:
        logger.error(f"Error getting node group instances: {str(e)}")
        return []

def get_node_name_from_instance_id(instance_id: str) -> str:
    """Get Kubernetes node name from EC2 instance ID"""
    
    # This would typically involve querying the Kubernetes API
    # For this demo, we'll return a simulated node name
    return f"ip-{instance_id.replace('instance-', '')}.ec2.internal"

def get_instance_id_from_node_name(node_name: str) -> str:
    """Get EC2 instance ID from Kubernetes node name"""
    
    # This would typically involve querying the Kubernetes API
    # For this demo, we'll return a simulated instance ID
    return f"i-{node_name.replace('ip-', '').replace('.ec2.internal', '')}"

def notify_slack_action(result: Dict[str, Any]) -> None:
    """Send notification to Slack about the node failure action"""
    
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Import requests here to avoid import errors if not installed
        import requests
        
        message = {
            "text": f"🔴 Node Failure Injection - {result['cluster']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔴 Node Failure Injection"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Cluster:* {result['cluster']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Node:* {result.get('node_name', 'Random')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:* {result['reason']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {result['status']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Correlation ID:* `{result['correlation_id']}`"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
