"""
EKS Chaos Guardian - Kubernetes Operations
Lambda function to execute Kubernetes operations for remediation
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
eks_client = boto3.client('eks')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle Kubernetes operations for remediation
    
    Expected event format:
    {
        "operation": "patch_deployment",
        "cluster": "eks-cluster-name",
        "namespace": "default",
        "resource_name": "my-deployment",
        "patch": {"spec": {"replicas": 3}},
        "dry_run": false
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting Kubernetes operation", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        operation = event.get('operation')
        cluster_name = event.get('cluster')
        namespace = event.get('namespace', 'default')
        resource_name = event.get('resource_name')
        patch = event.get('patch', {})
        dry_run = event.get('dry_run', False)
        
        result = {
            'correlation_id': correlation_id,
            'operation': operation,
            'cluster': cluster_name,
            'namespace': namespace,
            'resource_name': resource_name,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        if dry_run:
            result['planned_changes'] = get_planned_changes(operation, namespace, resource_name, patch)
            result['status'] = 'dry_run_success'
        else:
            # Execute the operation
            operation_result = execute_k8s_operation(
                operation, cluster_name, namespace, resource_name, patch, correlation_id
            )
            result['operation_result'] = operation_result
            
            if operation_result.get('status') == 'success':
                result['status'] = 'success'
            else:
                result['status'] = 'failed'
                result['error'] = operation_result.get('error')
        
        # Notify Slack about the operation
        notify_slack_operation(result)
        
        logger.info(f"Kubernetes operation completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Kubernetes operation failed: {str(e)}", extra={
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

def get_planned_changes(operation: str, namespace: str, resource_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Get planned changes for dry run mode"""
    
    planned_changes = {
        'operation': operation,
        'namespace': namespace,
        'resource_name': resource_name,
        'changes': [],
        'risk_level': 'low'
    }
    
    if operation == 'patch_deployment':
        planned_changes['changes'].append({
            'type': 'patch',
            'target': f'deployment/{resource_name}',
            'patch': patch,
            'description': f'Apply patch to deployment {resource_name}'
        })
        
        # Assess risk level based on patch content
        if 'spec' in patch:
            spec = patch['spec']
            if 'replicas' in spec and spec['replicas'] > 10:
                planned_changes['risk_level'] = 'high'
            elif 'resources' in spec:
                planned_changes['risk_level'] = 'medium'
    
    elif operation == 'rollout_restart':
        planned_changes['changes'].append({
            'type': 'restart',
            'target': f'deployment/{resource_name}',
            'description': f'Restart deployment {resource_name}'
        })
        planned_changes['risk_level'] = 'low'
    
    elif operation == 'scale_deployment':
        planned_changes['changes'].append({
            'type': 'scale',
            'target': f'deployment/{resource_name}',
            'replicas': patch.get('replicas', 1),
            'description': f'Scale deployment {resource_name} to {patch.get("replicas", 1)} replicas'
        })
        
        replicas = patch.get('replicas', 1)
        if replicas > 10:
            planned_changes['risk_level'] = 'high'
        elif replicas > 5:
            planned_changes['risk_level'] = 'medium'
    
    elif operation == 'cordon_node':
        planned_changes['changes'].append({
            'type': 'cordon',
            'target': f'node/{resource_name}',
            'description': f'Cordon node {resource_name} to prevent new pods'
        })
        planned_changes['risk_level'] = 'medium'
    
    elif operation == 'drain_node':
        planned_changes['changes'].append({
            'type': 'drain',
            'target': f'node/{resource_name}',
            'description': f'Drain node {resource_name} and evict existing pods'
        })
        planned_changes['risk_level'] = 'high'
    
    return planned_changes

def execute_k8s_operation(operation: str, cluster_name: str, namespace: str, 
                         resource_name: str, patch: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Execute a Kubernetes operation"""
    
    try:
        # Get cluster information for authentication
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        cluster_endpoint = cluster_info['cluster']['endpoint']
        cluster_ca = cluster_info['cluster']['certificateAuthority']['data']
        
        operation_result = {
            'operation': operation,
            'cluster': cluster_name,
            'namespace': namespace,
            'resource_name': resource_name,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {}
        }
        
        if operation == 'patch_deployment':
            result = patch_deployment(cluster_name, namespace, resource_name, patch)
            operation_result['details'] = result
            
        elif operation == 'rollout_restart':
            result = rollout_restart_deployment(cluster_name, namespace, resource_name)
            operation_result['details'] = result
            
        elif operation == 'scale_deployment':
            result = scale_deployment(cluster_name, namespace, resource_name, patch.get('replicas', 1))
            operation_result['details'] = result
            
        elif operation == 'cordon_node':
            result = cordon_node(cluster_name, resource_name)
            operation_result['details'] = result
            
        elif operation == 'drain_node':
            result = drain_node(cluster_name, resource_name)
            operation_result['details'] = result
            
        elif operation == 'patch_hpa':
            result = patch_hpa(cluster_name, namespace, resource_name, patch)
            operation_result['details'] = result
            
        elif operation == 'patch_pdb':
            result = patch_pdb(cluster_name, namespace, resource_name, patch)
            operation_result['details'] = result
            
        else:
            operation_result['status'] = 'failed'
            operation_result['error'] = f'Unknown operation: {operation}'
        
        return operation_result
        
    except Exception as e:
        logger.error(f"Error executing operation {operation}: {str(e)}")
        return {
            'operation': operation,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def patch_deployment(cluster_name: str, namespace: str, deployment_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Patch a Kubernetes deployment"""
    
    try:
        # This would typically use kubectl or the Kubernetes API
        # For this demo, we'll simulate the patch operation
        
        logger.info(f"Patching deployment {deployment_name} in namespace {namespace}")
        
        # Simulate patch application
        result = {
            'action': 'patch_deployment',
            'deployment': deployment_name,
            'namespace': namespace,
            'patch_applied': patch,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'before': {
                    'replicas': 1,
                    'image': 'nginx:1.20'
                },
                'after': {
                    **patch.get('spec', {}),
                    'image': 'nginx:1.20'
                }
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to patch deployment {deployment_name}: {str(e)}")
        return {
            'action': 'patch_deployment',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def rollout_restart_deployment(cluster_name: str, namespace: str, deployment_name: str) -> Dict[str, Any]:
    """Restart a Kubernetes deployment"""
    
    try:
        logger.info(f"Restarting deployment {deployment_name} in namespace {namespace}")
        
        # Simulate rollout restart
        result = {
            'action': 'rollout_restart',
            'deployment': deployment_name,
            'namespace': namespace,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'restart_triggered': True,
                'rolling_update': True,
                'max_unavailable': '25%',
                'max_surge': '25%'
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to restart deployment {deployment_name}: {str(e)}")
        return {
            'action': 'rollout_restart',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def scale_deployment(cluster_name: str, namespace: str, deployment_name: str, replicas: int) -> Dict[str, Any]:
    """Scale a Kubernetes deployment"""
    
    try:
        logger.info(f"Scaling deployment {deployment_name} to {replicas} replicas")
        
        # Simulate scaling operation
        result = {
            'action': 'scale_deployment',
            'deployment': deployment_name,
            'namespace': namespace,
            'replicas': replicas,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'current_replicas': 1,
                'desired_replicas': replicas,
                'scaling_triggered': True
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to scale deployment {deployment_name}: {str(e)}")
        return {
            'action': 'scale_deployment',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def cordon_node(cluster_name: str, node_name: str) -> Dict[str, Any]:
    """Cordon a Kubernetes node"""
    
    try:
        logger.info(f"Cordoning node {node_name}")
        
        # Simulate cordon operation
        result = {
            'action': 'cordon_node',
            'node': node_name,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'cordoned': True,
                'new_pods_prevented': True,
                'existing_pods_unchanged': True
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to cordon node {node_name}: {str(e)}")
        return {
            'action': 'cordon_node',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def drain_node(cluster_name: str, node_name: str) -> Dict[str, Any]:
    """Drain a Kubernetes node"""
    
    try:
        logger.info(f"Draining node {node_name}")
        
        # Simulate drain operation
        result = {
            'action': 'drain_node',
            'node': node_name,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'drained': True,
                'pods_evicted': 3,
                'eviction_strategy': 'graceful',
                'grace_period': '30s'
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to drain node {node_name}: {str(e)}")
        return {
            'action': 'drain_node',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def patch_hpa(cluster_name: str, namespace: str, hpa_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Patch a Horizontal Pod Autoscaler"""
    
    try:
        logger.info(f"Patching HPA {hpa_name} in namespace {namespace}")
        
        # Simulate HPA patch
        result = {
            'action': 'patch_hpa',
            'hpa': hpa_name,
            'namespace': namespace,
            'patch_applied': patch,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'min_replicas': patch.get('spec', {}).get('minReplicas', 1),
                'max_replicas': patch.get('spec', {}).get('maxReplicas', 10),
                'target_cpu': patch.get('spec', {}).get('targetCPUUtilizationPercentage', 70)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to patch HPA {hpa_name}: {str(e)}")
        return {
            'action': 'patch_hpa',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def patch_pdb(cluster_name: str, namespace: str, pdb_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Patch a Pod Disruption Budget"""
    
    try:
        logger.info(f"Patching PDB {pdb_name} in namespace {namespace}")
        
        # Simulate PDB patch
        result = {
            'action': 'patch_pdb',
            'pdb': pdb_name,
            'namespace': namespace,
            'patch_applied': patch,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'min_available': patch.get('spec', {}).get('minAvailable'),
                'max_unavailable': patch.get('spec', {}).get('maxUnavailable'),
                'selector': patch.get('spec', {}).get('selector', {})
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to patch PDB {pdb_name}: {str(e)}")
        return {
            'action': 'patch_pdb',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def notify_slack_operation(result: Dict[str, Any]) -> None:
    """Send notification to Slack about the Kubernetes operation"""
    
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Import requests here to avoid import errors if not installed
        import requests
        
        operation = result.get('operation', 'unknown')
        status = result.get('status', 'unknown')
        
        # Choose emoji based on status
        emoji = "✅" if status == 'success' else "❌" if status == 'failed' else "🔍"
        
        message = {
            "text": f"{emoji} Kubernetes Operation - {operation}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Kubernetes Operation"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Operation:* {operation}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Cluster:* {result.get('cluster', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Namespace:* {result.get('namespace', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Resource:* {result.get('resource_name', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {status}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Dry Run:* {result.get('dry_run', False)}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Correlation ID:* `{result.get('correlation_id', 'N/A')}`"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
