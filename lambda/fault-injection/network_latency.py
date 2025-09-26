"""
EKS Chaos Guardian - Network Latency Injection
Lambda function to inject network latency for chaos testing
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
ec2_client = boto3.client('ec2')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle network latency injection requests
    
    Expected event format:
    {
        "cluster": "eks-cluster-name",
        "target_type": "node|pod|service",
        "target_name": "node-name|pod-name|service-name",
        "latency_ms": 100,
        "duration_seconds": 60,
        "dry_run": false
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting network latency injection", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        cluster_name = event['cluster']
        target_type = event.get('target_type', 'node')
        target_name = event.get('target_name')
        latency_ms = event.get('latency_ms', 100)
        duration_seconds = event.get('duration_seconds', 60)
        dry_run = event.get('dry_run', False)
        
        if dry_run:
            return handle_dry_run(cluster_name, target_type, target_name, latency_ms, duration_seconds, correlation_id)
        
        result = {
            'correlation_id': correlation_id,
            'cluster': cluster_name,
            'target_type': target_type,
            'target_name': target_name,
            'latency_ms': latency_ms,
            'duration_seconds': duration_seconds,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'injection_actions': [],
            'status': 'success'
        }
        
        # Get cluster information
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        
        # Inject network latency based on target type
        if target_type == 'node':
            action_result = inject_node_latency(cluster_name, target_name, latency_ms, duration_seconds)
        elif target_type == 'pod':
            action_result = inject_pod_latency(cluster_name, target_name, latency_ms, duration_seconds)
        elif target_type == 'service':
            action_result = inject_service_latency(cluster_name, target_name, latency_ms, duration_seconds)
        else:
            raise ValueError(f"Unsupported target type: {target_type}")
        
        result['injection_actions'].append(action_result)
        
        # Notify Slack about the action
        notify_slack_action(result)
        
        logger.info(f"Network latency injection completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Network latency injection failed: {str(e)}", extra={
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

def handle_dry_run(cluster_name: str, target_type: str, target_name: Optional[str], 
                   latency_ms: int, duration_seconds: int, correlation_id: str) -> Dict[str, Any]:
    """Handle dry run mode - show what would be done without executing"""
    
    dry_run_result = {
        'correlation_id': correlation_id,
        'cluster': cluster_name,
        'target_type': target_type,
        'target_name': target_name,
        'latency_ms': latency_ms,
        'duration_seconds': duration_seconds,
        'dry_run': True,
        'timestamp': datetime.utcnow().isoformat(),
        'planned_actions': [],
        'status': 'dry_run_success'
    }
    
    if target_type == 'node':
        dry_run_result['planned_actions'] = [
            {
                'action': 'inject_node_latency',
                'target': target_name or 'random-node',
                'description': f'Inject {latency_ms}ms latency to node for {duration_seconds}s'
            }
        ]
    elif target_type == 'pod':
        dry_run_result['planned_actions'] = [
            {
                'action': 'inject_pod_latency',
                'target': target_name or 'random-pod',
                'description': f'Inject {latency_ms}ms latency to pod for {duration_seconds}s'
            }
        ]
    elif target_type == 'service':
        dry_run_result['planned_actions'] = [
            {
                'action': 'inject_service_latency',
                'target': target_name or 'random-service',
                'description': f'Inject {latency_ms}ms latency to service for {duration_seconds}s'
            }
        ]
    
    return {
        'statusCode': 200,
        'body': json.dumps(dry_run_result)
    }

def inject_node_latency(cluster_name: str, node_name: Optional[str], latency_ms: int, duration_seconds: int) -> Dict[str, Any]:
    """Inject network latency to a specific node"""
    
    try:
        # This would typically use tools like tc (traffic control) on the node
        # For this demo, we'll simulate the action
        
        target_node = node_name or "random-node"
        
        action_result = {
            'action': 'inject_node_latency',
            'target': target_node,
            'latency_ms': latency_ms,
            'duration_seconds': duration_seconds,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {
                'method': 'tc qdisc add dev eth0 root netem delay',
                'command': f'tc qdisc add dev eth0 root netem delay {latency_ms}ms',
                'cleanup_command': f'tc qdisc del dev eth0 root netem',
                'auto_cleanup': True
            }
        }
        
        logger.info(f"Injecting {latency_ms}ms latency to node {target_node} for {duration_seconds}s")
        
        return action_result
        
    except Exception as e:
        logger.error(f"Failed to inject node latency: {str(e)}")
        return {
            'action': 'inject_node_latency',
            'target': node_name,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def inject_pod_latency(cluster_name: str, pod_name: Optional[str], latency_ms: int, duration_seconds: int) -> Dict[str, Any]:
    """Inject network latency to a specific pod"""
    
    try:
        # This would typically use kubectl exec to run tc commands in the pod
        # For this demo, we'll simulate the action
        
        target_pod = pod_name or "random-pod"
        
        action_result = {
            'action': 'inject_pod_latency',
            'target': target_pod,
            'latency_ms': latency_ms,
            'duration_seconds': duration_seconds,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {
                'method': 'kubectl exec with tc command',
                'command': f'kubectl exec {target_pod} -- tc qdisc add dev eth0 root netem delay {latency_ms}ms',
                'cleanup_command': f'kubectl exec {target_pod} -- tc qdisc del dev eth0 root netem',
                'auto_cleanup': True
            }
        }
        
        logger.info(f"Injecting {latency_ms}ms latency to pod {target_pod} for {duration_seconds}s")
        
        return action_result
        
    except Exception as e:
        logger.error(f"Failed to inject pod latency: {str(e)}")
        return {
            'action': 'inject_pod_latency',
            'target': pod_name,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def inject_service_latency(cluster_name: str, service_name: Optional[str], latency_ms: int, duration_seconds: int) -> Dict[str, Any]:
    """Inject network latency to a service (affects all pods in the service)"""
    
    try:
        # This would typically affect all pods in the service
        # For this demo, we'll simulate the action
        
        target_service = service_name or "random-service"
        
        action_result = {
            'action': 'inject_service_latency',
            'target': target_service,
            'latency_ms': latency_ms,
            'duration_seconds': duration_seconds,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {
                'method': 'Service-wide latency injection',
                'description': f'Inject latency to all pods in service {target_service}',
                'affected_pods': ['pod-1', 'pod-2', 'pod-3'],  # Simulated
                'auto_cleanup': True
            }
        }
        
        logger.info(f"Injecting {latency_ms}ms latency to service {target_service} for {duration_seconds}s")
        
        return action_result
        
    except Exception as e:
        logger.error(f"Failed to inject service latency: {str(e)}")
        return {
            'action': 'inject_service_latency',
            'target': service_name,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def notify_slack_action(result: Dict[str, Any]) -> None:
    """Send notification to Slack about the network latency injection"""
    
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Import requests here to avoid import errors if not installed
        import requests
        
        message = {
            "text": f"🟠 Network Latency Injection - {result['cluster']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🟠 Network Latency Injection"
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
                            "text": f"*Target:* {result.get('target_name', 'Random')} ({result['target_type']})"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Latency:* {result['latency_ms']}ms"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {result['duration_seconds']}s"
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
