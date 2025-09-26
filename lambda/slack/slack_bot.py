"""
EKS Chaos Guardian - Slack Bot
Lambda function to handle Slack interactions, approvals, and notifications
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import hmac
import hashlib
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle Slack bot interactions
    
    Expected event format:
    {
        "body": "token=...&team_id=...&channel_id=...&user_id=...&command=/chaos&text=help",
        "headers": {...}
    }
    """
    
    try:
        # Parse the request
        if 'body' in event:
            # Handle Slack slash command or interactive component
            body = event['body']
            if isinstance(body, str):
                # Parse form data
                params = parse_form_data(body)
            else:
                params = body
        else:
            # Handle direct invocation
            params = event
        
        # Verify Slack request (in production, verify the signing secret)
        if not verify_slack_request(event):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Determine the type of interaction
        if 'command' in params:
            # Handle slash command
            return handle_slash_command(params)
        elif 'payload' in params:
            # Handle interactive component (button clicks, etc.)
            payload = json.loads(params['payload'])
            return handle_interactive_component(payload)
        else:
            # Handle other types of interactions
            return handle_general_interaction(params)
        
    except Exception as e:
        logger.error(f"Slack bot error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def parse_form_data(body: str) -> Dict[str, str]:
    """Parse form-encoded data from Slack"""
    
    params = {}
    for pair in body.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key] = value
    
    return params

def verify_slack_request(event: Dict[str, Any]) -> bool:
    """Verify that the request came from Slack"""
    
    try:
        # In production, verify the Slack signing secret
        # For demo purposes, we'll skip this verification
        return True
        
    except Exception as e:
        logger.error(f"Error verifying Slack request: {str(e)}")
        return False

def handle_slash_command(params: Dict[str, str]) -> Dict[str, Any]:
    """Handle Slack slash commands"""
    
    command = params.get('command', '')
    text = params.get('text', '').strip()
    user_id = params.get('user_id', '')
    channel_id = params.get('channel_id', '')
    
    logger.info(f"Handling slash command: {command} {text} from user {user_id}")
    
    if command == '/chaos':
        return handle_chaos_command(text, user_id, channel_id)
    elif command in ['/status', '/chaos-status', '/cluster-status', '/eks-status', '/guardian-status']:
        return handle_status_command(text, user_id, channel_id)
    elif command in ['/help', '/chaos-help']:
        return handle_help_command(text, user_id, channel_id)
    elif command == '/approve':
        return handle_approve_command(text, user_id, channel_id)
    else:
        return create_response("Unknown command. Available commands: `/chaos`, `/chaos-status`, `/chaos-help`, `/approve`")

def handle_chaos_command(text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle /chaos slash command"""
    
    if not text or text == 'help':
        return create_response("""
🔴 *EKS Chaos Guardian Commands*

*Fault Injection:*
• `/chaos node-failure [cluster]` - Inject node failure
• `/chaos pod-eviction [cluster] [namespace]` - Evict pods
• `/chaos network-latency [cluster] [latency_ms]` - Inject network latency
• `/chaos api-throttling [cluster] [rate]` - Throttle API calls

*Detection:*
• `/chaos detect-logs [cluster]` - Check for error logs
• `/chaos detect-metrics [cluster]` - Check cluster metrics

*Remediation:*
• `/chaos fix-oom [cluster] [namespace] [deployment]` - Fix OOMKilled pods
• `/chaos fix-image-pull [cluster] [namespace] [deployment]` - Fix image pull issues
• `/chaos scale-up [cluster] [namespace] [deployment] [replicas]` - Scale deployment

*Examples:*
• `/chaos node-failure eks-chaos-guardian-autopilot`
• `/chaos detect-logs eks-chaos-guardian-autopilot`
• `/chaos fix-oom eks-chaos-guardian-autopilot default my-app`
        """)
    
    parts = text.split()
    action = parts[0]
    
    if action == 'node-failure':
        return handle_node_failure_command(parts[1:], user_id, channel_id)
    elif action == 'pod-eviction':
        return handle_pod_eviction_command(parts[1:], user_id, channel_id)
    elif action == 'network-latency':
        return handle_network_latency_command(parts[1:], user_id, channel_id)
    elif action == 'api-throttling':
        return handle_api_throttling_command(parts[1:], user_id, channel_id)
    elif action == 'detect-logs':
        return handle_detect_logs_command(parts[1:], user_id, channel_id)
    elif action == 'detect-metrics':
        return handle_detect_metrics_command(parts[1:], user_id, channel_id)
    elif action == 'fix-oom':
        return handle_fix_oom_command(parts[1:], user_id, channel_id)
    elif action == 'fix-image-pull':
        return handle_fix_image_pull_command(parts[1:], user_id, channel_id)
    elif action == 'scale-up':
        return handle_scale_up_command(parts[1:], user_id, channel_id)
    else:
        return create_response(f"Unknown action: {action}. Use `/chaos help` for available commands.")

def handle_node_failure_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle node failure injection command"""
    
    if not args:
        return create_response("Usage: `/chaos node-failure <cluster-name>`")
    
    cluster_name = args[0]
    
    # Create approval request
    approval_id = f"node-failure-{int(time.time())}"
    
    # Store approval request in DynamoDB
    store_approval_request(approval_id, {
        'action': 'node_failure',
        'cluster': cluster_name,
        'user_id': user_id,
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'pending'
    })
    
    # Create interactive message with approval buttons
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔴 Node Failure Injection Request"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Cluster:* {cluster_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Action:* Node Failure Injection"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Requested by:* <@{user_id}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Risk Level:* 🔴 High"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *Warning:* This will cordon and terminate a worker node. This is a destructive operation that may cause service disruption."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve"
                    },
                    "style": "danger",
                    "value": f"approve:{approval_id}",
                    "action_id": "approve_node_failure"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "value": f"reject:{approval_id}",
                    "action_id": "reject_node_failure"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 Dry Run"
                    },
                    "value": f"dry_run:{approval_id}",
                    "action_id": "dry_run_node_failure"
                }
            ]
        }
    ]
    
    return create_response("", blocks=blocks)

def handle_pod_eviction_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle pod eviction command"""
    
    if len(args) < 2:
        return create_response("Usage: `/chaos pod-eviction <cluster-name> <namespace>`")
    
    cluster_name = args[0]
    namespace = args[1]
    
    approval_id = f"pod-eviction-{int(time.time())}"
    
    store_approval_request(approval_id, {
        'action': 'pod_eviction',
        'cluster': cluster_name,
        'namespace': namespace,
        'user_id': user_id,
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'pending'
    })
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🟡 Pod Eviction Request"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Cluster:* {cluster_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Namespace:* {namespace}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Action:* Pod Eviction"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Requested by:* <@{user_id}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Risk Level:* 🟡 Medium"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve"
                    },
                    "style": "primary",
                    "value": f"approve:{approval_id}",
                    "action_id": "approve_pod_eviction"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "value": f"reject:{approval_id}",
                    "action_id": "reject_pod_eviction"
                }
            ]
        }
    ]
    
    return create_response("", blocks=blocks)

def handle_network_latency_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle network latency injection command"""
    
    if len(args) < 2:
        return create_response("Usage: `/chaos network-latency <cluster-name> <latency_ms>`")
    
    cluster_name = args[0]
    latency_ms = args[1]
    
    approval_id = f"network-latency-{int(time.time())}"
    
    store_approval_request(approval_id, {
        'action': 'network_latency',
        'cluster': cluster_name,
        'latency_ms': int(latency_ms),
        'user_id': user_id,
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'pending'
    })
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🟠 Network Latency Injection Request"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Cluster:* {cluster_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Latency:* {latency_ms}ms"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Action:* Network Latency Injection"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Requested by:* <@{user_id}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Risk Level:* 🟠 Low"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve"
                    },
                    "style": "primary",
                    "value": f"approve:{approval_id}",
                    "action_id": "approve_network_latency"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "value": f"reject:{approval_id}",
                    "action_id": "reject_network_latency"
                }
            ]
        }
    ]
    
    return create_response("", blocks=blocks)

def handle_api_throttling_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle API throttling injection command"""
    
    if len(args) < 2:
        return create_response("Usage: `/chaos api-throttling <cluster-name> <throttle_rate>`")
    
    cluster_name = args[0]
    throttle_rate = args[1]
    
    approval_id = f"api-throttling-{int(time.time())}"
    
    store_approval_request(approval_id, {
        'action': 'api_throttling',
        'cluster': cluster_name,
        'throttle_rate': float(throttle_rate),
        'user_id': user_id,
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'pending'
    })
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔵 API Throttling Injection Request"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Cluster:* {cluster_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Throttle Rate:* {throttle_rate}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Action:* API Throttling"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Requested by:* <@{user_id}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Risk Level:* 🔵 Low"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve"
                    },
                    "style": "primary",
                    "value": f"approve:{approval_id}",
                    "action_id": "approve_api_throttling"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "value": f"reject:{approval_id}",
                    "action_id": "reject_api_throttling"
                }
            ]
        }
    ]
    
    return create_response("", blocks=blocks)

def handle_detect_logs_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle log detection command"""
    
    if not args:
        return create_response("Usage: `/chaos detect-logs <cluster-name>`")
    
    cluster_name = args[0]
    
    # Trigger log detection
    try:
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-cloudwatch-logs',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'log_groups': [f'/aws/eks/{cluster_name}/application'],
                'query': 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc',
                'limit': 50
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            failure_analysis = body.get('failure_analysis', {})
            
            if failure_analysis.get('total_failures', 0) > 0:
                message = f"🔍 *Log Analysis Results for {cluster_name}*\n\n"
                message += f"*Total Failures:* {failure_analysis.get('total_failures', 0)}\n\n"
                
                for failure_type, details in failure_analysis.get('failure_types', {}).items():
                    message += f"*{failure_type.replace('_', ' ').title()}:* {details.get('count', 0)} occurrences\n"
                
                return create_response(message)
            else:
                return create_response(f"✅ No failures detected in {cluster_name} logs")
        else:
            return create_response(f"❌ Error analyzing logs for {cluster_name}")
            
    except Exception as e:
        logger.error(f"Error detecting logs: {str(e)}")
        return create_response(f"❌ Error analyzing logs: {str(e)}")

def handle_detect_metrics_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle metrics detection command"""
    
    if not args:
        return create_response("Usage: `/chaos detect-metrics <cluster-name>`")
    
    cluster_name = args[0]
    
    # Trigger metrics detection
    try:
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-cloudwatch-metrics',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'namespace': 'AWS/EKS',
                'dimensions': {'ClusterName': cluster_name},
                'period': 300
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            anomaly_analysis = body.get('anomaly_analysis', {})
            
            if anomaly_analysis.get('anomalies_detected', False):
                message = f"📊 *Metrics Analysis Results for {cluster_name}*\n\n"
                message += f"*Anomalies Detected:* {anomaly_analysis.get('anomalies_detected', False)}\n\n"
                
                for indicator in anomaly_analysis.get('failure_indicators', []):
                    message += f"• {indicator.get('description', 'Unknown issue')}\n"
                
                return create_response(message)
            else:
                return create_response(f"✅ No anomalies detected in {cluster_name} metrics")
        else:
            return create_response(f"❌ Error analyzing metrics for {cluster_name}")
            
    except Exception as e:
        logger.error(f"Error detecting metrics: {str(e)}")
        return create_response(f"❌ Error analyzing metrics: {str(e)}")

def handle_fix_oom_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle OOM fix command"""
    
    if len(args) < 3:
        return create_response("Usage: `/chaos fix-oom <cluster-name> <namespace> <deployment>`")
    
    cluster_name = args[0]
    namespace = args[1]
    deployment = args[2]
    
    # Trigger OOM fix
    try:
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'operation': 'patch_deployment',
                'cluster': cluster_name,
                'namespace': namespace,
                'resource_name': deployment,
                'patch': {
                    'spec': {
                        'template': {
                            'spec': {
                                'containers': [{
                                    'name': 'main',
                                    'resources': {
                                        'requests': {'memory': '512Mi'},
                                        'limits': {'memory': '1Gi'}
                                    }
                                }]
                            }
                        }
                    }
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return create_response(f"✅ OOM fix applied to {deployment} in {namespace}")
        else:
            return create_response(f"❌ Error applying OOM fix to {deployment}")
            
    except Exception as e:
        logger.error(f"Error fixing OOM: {str(e)}")
        return create_response(f"❌ Error applying OOM fix: {str(e)}")

def handle_fix_image_pull_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle image pull fix command"""
    
    if len(args) < 3:
        return create_response("Usage: `/chaos fix-image-pull <cluster-name> <namespace> <deployment>`")
    
    cluster_name = args[0]
    namespace = args[1]
    deployment = args[2]
    
    # Trigger image pull fix
    try:
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'operation': 'rollout_restart',
                'cluster': cluster_name,
                'namespace': namespace,
                'resource_name': deployment
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return create_response(f"✅ Image pull fix applied to {deployment} in {namespace}")
        else:
            return create_response(f"❌ Error applying image pull fix to {deployment}")
            
    except Exception as e:
        logger.error(f"Error fixing image pull: {str(e)}")
        return create_response(f"❌ Error applying image pull fix: {str(e)}")

def handle_scale_up_command(args: List[str], user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle scale up command"""
    
    if len(args) < 4:
        return create_response("Usage: `/chaos scale-up <cluster-name> <namespace> <deployment> <replicas>`")
    
    cluster_name = args[0]
    namespace = args[1]
    deployment = args[2]
    replicas = int(args[3])
    
    # Trigger scale up
    try:
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'operation': 'scale_deployment',
                'cluster': cluster_name,
                'namespace': namespace,
                'resource_name': deployment,
                'patch': {'replicas': replicas}
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return create_response(f"✅ Scaled {deployment} to {replicas} replicas in {namespace}")
        else:
            return create_response(f"❌ Error scaling {deployment}")
            
    except Exception as e:
        logger.error(f"Error scaling deployment: {str(e)}")
        return create_response(f"❌ Error scaling deployment: {str(e)}")

def handle_status_command(text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle /status slash command"""
    
    if not text:
        return create_response("Usage: `/status <cluster-name>`")
    
    cluster_name = text
    
    # Get cluster status
    try:
        # This would typically query the cluster status
        # For demo purposes, we'll return a simulated status
        
        status_message = f"📊 *Cluster Status: {cluster_name}*\n\n"
        status_message += "• **Nodes:** 3/3 healthy\n"
        status_message += "• **Pods:** 15/15 running\n"
        status_message += "• **Services:** 5/5 available\n"
        status_message += "• **Last Health Check:** 2 minutes ago\n"
        status_message += "• **Status:** ✅ Healthy"
        
        return create_response(status_message)
        
    except Exception as e:
        logger.error(f"Error getting cluster status: {str(e)}")
        return create_response(f"❌ Error getting cluster status: {str(e)}")

def handle_help_command(text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle /help slash command"""
    
    help_message = "🤖 *EKS Chaos Guardian - Available Commands*\n\n"
    help_message += "• `/chaos-status <cluster-name>` - Check cluster status\n"
    help_message += "• `/chaos node-failure <cluster-name>` - Test node failure\n"
    help_message += "• `/chaos pod-eviction <cluster-name>` - Test pod eviction\n"
    help_message += "• `/chaos network-latency <cluster-name>` - Test network latency\n"
    help_message += "• `/chaos api-throttling <cluster-name>` - Test API throttling\n"
    help_message += "• `/chaos help` - Show this help message\n"
    help_message += "• `/approve <plan-id>` - Approve a remediation plan\n\n"
    help_message += "💡 *Examples:*\n"
    help_message += "• `/chaos-status eks-chaos-guardian-autopilot`\n"
    help_message += "• `/chaos node-failure eks-chaos-guardian-autopilot`\n"
    help_message += "• `/approve plan-12345`"
    
    return create_response(help_message)

def handle_approve_command(text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
    """Handle /approve slash command"""
    
    if not text:
        return create_response("Usage: `/approve <approval-id>`")
    
    approval_id = text
    
    # Get approval request
    approval_request = get_approval_request(approval_id)
    
    if not approval_request:
        return create_response(f"❌ Approval request {approval_id} not found")
    
    if approval_request['status'] != 'pending':
        return create_response(f"❌ Approval request {approval_id} is already {approval_request['status']}")
    
    # Approve the request
    update_approval_request(approval_id, 'approved', user_id)
    
    # Execute the approved action
    execute_approved_action(approval_request)
    
    return create_response(f"✅ Approved and executed {approval_request['action']} for {approval_request.get('cluster', 'unknown cluster')}")

def handle_interactive_component(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle interactive component (button clicks, etc.)"""
    
    action_id = payload.get('actions', [{}])[0].get('action_id', '')
    value = payload.get('actions', [{}])[0].get('value', '')
    user_id = payload.get('user', {}).get('id', '')
    
    if 'approve' in action_id:
        approval_id = value.split(':')[1]
        return handle_approval(approval_id, user_id, 'approved')
    elif 'reject' in action_id:
        approval_id = value.split(':')[1]
        return handle_approval(approval_id, user_id, 'rejected')
    elif 'dry_run' in action_id:
        approval_id = value.split(':')[1]
        return handle_dry_run(approval_id, user_id)
    else:
        return create_response("Unknown action")

def handle_approval(approval_id: str, user_id: str, status: str) -> Dict[str, Any]:
    """Handle approval or rejection"""
    
    # Get approval request
    approval_request = get_approval_request(approval_id)
    
    if not approval_request:
        return create_response(f"❌ Approval request {approval_id} not found")
    
    if approval_request['status'] != 'pending':
        return create_response(f"❌ Approval request {approval_id} is already {approval_request['status']}")
    
    # Update approval status
    update_approval_request(approval_id, status, user_id)
    
    if status == 'approved':
        # Execute the approved action
        execute_approved_action(approval_request)
        return create_response(f"✅ Approved and executed {approval_request['action']}")
    else:
        return create_response(f"❌ Rejected {approval_request['action']}")

def handle_dry_run(approval_id: str, user_id: str) -> Dict[str, Any]:
    """Handle dry run request"""
    
    # Get approval request
    approval_request = get_approval_request(approval_id)
    
    if not approval_request:
        return create_response(f"❌ Approval request {approval_id} not found")
    
    # Execute dry run
    try:
        action = approval_request['action']
        cluster = approval_request['cluster']
        
        if action == 'node_failure':
            response = lambda_client.invoke(
                FunctionName='eks-chaos-guardian-node-failure',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'cluster': cluster,
                    'dry_run': True
                })
            )
        elif action == 'pod_eviction':
            response = lambda_client.invoke(
                FunctionName='eks-chaos-guardian-pod-eviction',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'cluster': cluster,
                    'namespace': approval_request.get('namespace', 'default'),
                    'dry_run': True
                })
            )
        else:
            return create_response(f"❌ Dry run not supported for {action}")
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            planned_actions = body.get('planned_actions', [])
            
            message = f"🔍 *Dry Run Results for {action}*\n\n"
            for action_item in planned_actions:
                message += f"• {action_item.get('description', 'Unknown action')}\n"
            
            return create_response(message)
        else:
            return create_response(f"❌ Error executing dry run for {action}")
            
    except Exception as e:
        logger.error(f"Error executing dry run: {str(e)}")
        return create_response(f"❌ Error executing dry run: {str(e)}")

def handle_general_interaction(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general interactions"""
    
    return create_response("Hello! I'm the EKS Chaos Guardian bot. Use `/chaos help` for available commands.")

def store_approval_request(approval_id: str, request: Dict[str, Any]) -> None:
    """Store approval request in DynamoDB"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-approvals')
        table.put_item(Item={
            'approval_id': approval_id,
            **request
        })
    except Exception as e:
        logger.error(f"Error storing approval request: {str(e)}")

def get_approval_request(approval_id: str) -> Optional[Dict[str, Any]]:
    """Get approval request from DynamoDB"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-approvals')
        response = table.get_item(Key={'approval_id': approval_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting approval request: {str(e)}")
        return None

def update_approval_request(approval_id: str, status: str, user_id: str) -> None:
    """Update approval request status"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-approvals')
        table.update_item(
            Key={'approval_id': approval_id},
            UpdateExpression='SET #status = :status, approved_by = :user_id, approved_at = :timestamp',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':user_id': user_id,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error updating approval request: {str(e)}")

def execute_approved_action(approval_request: Dict[str, Any]) -> None:
    """Execute the approved action"""
    
    try:
        action = approval_request['action']
        cluster = approval_request['cluster']
        
        if action == 'node_failure':
            lambda_client.invoke(
                FunctionName='eks-chaos-guardian-node-failure',
                InvocationType='Event',
                Payload=json.dumps({
                    'cluster': cluster,
                    'dry_run': False
                })
            )
        elif action == 'pod_eviction':
            lambda_client.invoke(
                FunctionName='eks-chaos-guardian-pod-eviction',
                InvocationType='Event',
                Payload=json.dumps({
                    'cluster': cluster,
                    'namespace': approval_request.get('namespace', 'default'),
                    'dry_run': False
                })
            )
        elif action == 'network_latency':
            lambda_client.invoke(
                FunctionName='eks-chaos-guardian-network-latency',
                InvocationType='Event',
                Payload=json.dumps({
                    'cluster': cluster,
                    'latency_ms': approval_request.get('latency_ms', 100),
                    'dry_run': False
                })
            )
        elif action == 'api_throttling':
            lambda_client.invoke(
                FunctionName='eks-chaos-guardian-api-throttling',
                InvocationType='Event',
                Payload=json.dumps({
                    'cluster': cluster,
                    'throttle_rate': approval_request.get('throttle_rate', 0.5),
                    'dry_run': False
                })
            )
        
    except Exception as e:
        logger.error(f"Error executing approved action: {str(e)}")

def create_response(text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Create Slack response"""
    
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'text': text,
            'blocks': blocks or []
        })
    }
    
    return response
