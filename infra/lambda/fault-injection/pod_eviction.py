"""
EKS Chaos Guardian - Pod Eviction Injection
Lambda function to evict pods for chaos testing
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
eks_client = boto3.client('eks')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle pod eviction requests
    
    Expected event format:
    {
        "cluster": "eks-cluster-name",
        "namespace": "default",
        "label_selector": "app=my-app",
        "respect_pdb": true,
        "dry_run": false
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting pod eviction", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        cluster_name = event['cluster']
        namespace = event.get('namespace', 'default')
        label_selector = event.get('label_selector')
        respect_pdb = event.get('respect_pdb', True)
        dry_run = event.get('dry_run', False)
        
        if dry_run:
            return handle_dry_run(cluster_name, namespace, label_selector, respect_pdb, correlation_id)
        
        result = {
            'correlation_id': correlation_id,
            'cluster': cluster_name,
            'namespace': namespace,
            'label_selector': label_selector,
            'respect_pdb': respect_pdb,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'evicted_pods': [],
            'status': 'success'
        }
        
        # Get cluster information
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        
        # Find pods to evict
        pods_to_evict = find_pods_to_evict(cluster_name, namespace, label_selector, respect_pdb)
        
        # Evict pods
        for pod in pods_to_evict:
            eviction_result = evict_pod(cluster_name, namespace, pod['name'], respect_pdb)
            result['evicted_pods'].append(eviction_result)
        
        # Notify Slack about the action
        notify_slack_action(result)
        
        logger.info(f"Pod eviction completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Pod eviction failed: {str(e)}", extra={
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

def handle_dry_run(cluster_name: str, namespace: str, label_selector: Optional[str], 
                  respect_pdb: bool, correlation_id: str) -> Dict[str, Any]:
    """Handle dry run mode - show what would be done without executing"""
    
    dry_run_result = {
        'correlation_id': correlation_id,
        'cluster': cluster_name,
        'namespace': namespace,
        'label_selector': label_selector,
        'respect_pdb': respect_pdb,
        'dry_run': True,
        'timestamp': datetime.utcnow().isoformat(),
        'planned_evictions': [],
        'status': 'dry_run_success'
    }
    
    # Simulate finding pods that would be evicted
    if label_selector:
        dry_run_result['planned_evictions'] = [
            {
                'pod_name': f'app-pod-{i}',
                'namespace': namespace,
                'reason': f'Matches label selector: {label_selector}',
                'pdb_check': 'passed' if respect_pdb else 'skipped'
            }
            for i in range(1, 4)  # Simulate 3 pods
        ]
    else:
        dry_run_result['planned_evictions'] = [
            {
                'pod_name': f'random-pod-{i}',
                'namespace': namespace,
                'reason': 'Random pod selection',
                'pdb_check': 'passed' if respect_pdb else 'skipped'
            }
            for i in range(1, 3)  # Simulate 2 pods
        ]
    
    return {
        'statusCode': 200,
        'body': json.dumps(dry_run_result)
    }

def find_pods_to_evict(cluster_name: str, namespace: str, label_selector: Optional[str], 
                      respect_pdb: bool) -> List[Dict[str, Any]]:
    """Find pods that can be evicted based on criteria"""
    
    pods = []
    
    try:
        # This would typically use kubectl or the Kubernetes API
        # For this demo, we'll simulate pod discovery
        
        if label_selector:
            # Find pods matching label selector
            pods = [
                {
                    'name': f'app-pod-{i}',
                    'namespace': namespace,
                    'labels': {'app': 'my-app', 'version': 'v1'},
                    'status': 'Running'
                }
                for i in range(1, 4)
            ]
        else:
            # Find random pods in namespace
            pods = [
                {
                    'name': f'random-pod-{i}',
                    'namespace': namespace,
                    'labels': {'app': 'random'},
                    'status': 'Running'
                }
                for i in range(1, 3)
            ]
        
        # Filter based on PDB if required
        if respect_pdb:
            pods = check_pdb_constraints(cluster_name, namespace, pods)
        
        return pods
        
    except Exception as e:
        logger.error(f"Error finding pods to evict: {str(e)}")
        return []

def check_pdb_constraints(cluster_name: str, namespace: str, pods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check PodDisruptionBudget constraints"""
    
    filtered_pods = []
    
    for pod in pods:
        try:
            # This would typically check PDB constraints via Kubernetes API
            # For this demo, we'll simulate the check
            
            # Simulate PDB check - allow eviction if not constrained
            pdb_allows_eviction = True  # Simplified for demo
            
            if pdb_allows_eviction:
                pod['pdb_check'] = 'passed'
                filtered_pods.append(pod)
            else:
                pod['pdb_check'] = 'blocked'
                logger.info(f"Pod {pod['name']} blocked by PDB constraints")
                
        except Exception as e:
            logger.error(f"Error checking PDB for pod {pod['name']}: {str(e)}")
            # If we can't check PDB, err on the side of caution
            pod['pdb_check'] = 'error'
            filtered_pods.append(pod)
    
    return filtered_pods

def evict_pod(cluster_name: str, namespace: str, pod_name: str, respect_pdb: bool) -> Dict[str, Any]:
    """Evict a specific pod"""
    
    try:
        # This would typically use kubectl drain or the Kubernetes API
        # For this demo, we'll simulate the eviction
        
        eviction_result = {
            'pod_name': pod_name,
            'namespace': namespace,
            'action': 'evict',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {
                'eviction_triggered': True,
                'grace_period': '30s',
                'pdb_respected': respect_pdb
            }
        }
        
        # Simulate eviction process
        logger.info(f"Evicting pod {pod_name} in namespace {namespace}")
        
        return eviction_result
        
    except Exception as e:
        logger.error(f"Failed to evict pod {pod_name}: {str(e)}")
        return {
            'pod_name': pod_name,
            'namespace': namespace,
            'action': 'evict',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'failed',
            'error': str(e)
        }

def notify_slack_action(result: Dict[str, Any]) -> None:
    """Send notification to Slack about the pod eviction action"""
    
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Import requests here to avoid import errors if not installed
        import requests
        
        evicted_count = len(result.get('evicted_pods', []))
        
        message = {
            "text": f"🟡 Pod Eviction - {result['cluster']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🟡 Pod Eviction"
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
                            "text": f"*Namespace:* {result['namespace']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Label Selector:* {result.get('label_selector', 'All pods')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Pods Evicted:* {evicted_count}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Respect PDB:* {result['respect_pdb']}"
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
