"""
EKS Chaos Guardian - API Throttling Injection
Lambda function to inject API throttling for chaos testing
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
apigateway_client = boto3.client('apigateway')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API throttling injection requests
    
    Expected event format:
    {
        "cluster": "eks-cluster-name",
        "api_endpoint": "https://api.example.com",
        "throttle_rate": 0.5,
        "duration_seconds": 60,
        "method": "GET|POST|PUT|DELETE",
        "dry_run": false
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting API throttling injection", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        cluster_name = event['cluster']
        api_endpoint = event.get('api_endpoint')
        throttle_rate = event.get('throttle_rate', 0.5)  # 50% of requests throttled
        duration_seconds = event.get('duration_seconds', 60)
        method = event.get('method', 'GET')
        dry_run = event.get('dry_run', False)
        
        if dry_run:
            return handle_dry_run(cluster_name, api_endpoint, throttle_rate, duration_seconds, method, correlation_id)
        
        result = {
            'correlation_id': correlation_id,
            'cluster': cluster_name,
            'api_endpoint': api_endpoint,
            'throttle_rate': throttle_rate,
            'duration_seconds': duration_seconds,
            'method': method,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat(),
            'throttling_actions': [],
            'status': 'success'
        }
        
        # Get cluster information
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        
        # Inject API throttling
        throttling_result = inject_api_throttling(
            cluster_name, api_endpoint, throttle_rate, duration_seconds, method
        )
        result['throttling_actions'].append(throttling_result)
        
        # Notify Slack about the action
        notify_slack_action(result)
        
        logger.info(f"API throttling injection completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"API throttling injection failed: {str(e)}", extra={
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

def handle_dry_run(cluster_name: str, api_endpoint: Optional[str], throttle_rate: float, 
                  duration_seconds: int, method: str, correlation_id: str) -> Dict[str, Any]:
    """Handle dry run mode - show what would be done without executing"""
    
    dry_run_result = {
        'correlation_id': correlation_id,
        'cluster': cluster_name,
        'api_endpoint': api_endpoint,
        'throttle_rate': throttle_rate,
        'duration_seconds': duration_seconds,
        'method': method,
        'dry_run': True,
        'timestamp': datetime.utcnow().isoformat(),
        'planned_actions': [],
        'status': 'dry_run_success'
    }
    
    dry_run_result['planned_actions'] = [
        {
            'action': 'inject_api_throttling',
            'target': api_endpoint or 'cluster-apis',
            'description': f'Throttle {throttle_rate*100}% of {method} requests for {duration_seconds}s'
        },
        {
            'action': 'configure_rate_limiting',
            'target': 'api-gateway',
            'description': f'Set rate limit to {throttle_rate*100}% of normal capacity'
        },
        {
            'action': 'monitor_throttling_effects',
            'target': 'cloudwatch',
            'description': 'Monitor API response times and error rates'
        }
    ]
    
    return {
        'statusCode': 200,
        'body': json.dumps(dry_run_result)
    }

def inject_api_throttling(cluster_name: str, api_endpoint: Optional[str], throttle_rate: float, 
                         duration_seconds: int, method: str) -> Dict[str, Any]:
    """Inject API throttling"""
    
    try:
        # This would typically involve:
        # 1. Configuring API Gateway throttling
        # 2. Setting up rate limiting in the application
        # 3. Using service mesh (Istio/Linkerd) for traffic control
        # For this demo, we'll simulate the action
        
        target_endpoint = api_endpoint or f"https://{cluster_name}.internal"
        
        action_result = {
            'action': 'inject_api_throttling',
            'target': target_endpoint,
            'throttle_rate': throttle_rate,
            'duration_seconds': duration_seconds,
            'method': method,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'details': {
                'throttling_method': 'api_gateway_throttling',
                'rate_limit': f'{throttle_rate*100}% of normal capacity',
                'affected_endpoints': [target_endpoint],
                'monitoring': {
                    'cloudwatch_metrics': ['API_4XX_Error', 'API_5XX_Error', 'API_Latency'],
                    'alerts': ['HighErrorRate', 'HighLatency']
                },
                'cleanup': {
                    'auto_cleanup': True,
                    'cleanup_time': f'{duration_seconds}s after injection'
                }
            }
        }
        
        logger.info(f"Injecting API throttling: {throttle_rate*100}% rate limit to {target_endpoint} for {duration_seconds}s")
        
        return action_result
        
    except Exception as e:
        logger.error(f"Failed to inject API throttling: {str(e)}")
        return {
            'action': 'inject_api_throttling',
            'target': api_endpoint,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def configure_api_gateway_throttling(api_id: str, throttle_rate: float, duration_seconds: int) -> Dict[str, Any]:
    """Configure API Gateway throttling"""
    
    try:
        # This would typically use AWS API Gateway throttling settings
        # For this demo, we'll simulate the configuration
        
        throttling_config = {
            'api_id': api_id,
            'throttle_rate': throttle_rate,
            'duration_seconds': duration_seconds,
            'burst_limit': int(100 * throttle_rate),  # Reduced burst limit
            'rate_limit': int(1000 * throttle_rate),  # Reduced rate limit
            'quota_limit': int(10000 * throttle_rate)  # Reduced quota
        }
        
        logger.info(f"Configured API Gateway throttling: {throttling_config}")
        
        return {
            'action': 'configure_api_gateway_throttling',
            'status': 'success',
            'config': throttling_config,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to configure API Gateway throttling: {str(e)}")
        return {
            'action': 'configure_api_gateway_throttling',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def monitor_throttling_effects(cluster_name: str, api_endpoint: str, duration_seconds: int) -> Dict[str, Any]:
    """Monitor the effects of API throttling"""
    
    try:
        # This would typically query CloudWatch metrics
        # For this demo, we'll simulate monitoring
        
        monitoring_result = {
            'action': 'monitor_throttling_effects',
            'cluster': cluster_name,
            'api_endpoint': api_endpoint,
            'duration_seconds': duration_seconds,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success',
            'metrics': {
                'error_rate_before': 0.02,  # 2% before throttling
                'error_rate_after': 0.15,   # 15% after throttling
                'latency_p50_before': 100,  # 100ms before
                'latency_p50_after': 500,   # 500ms after
                'latency_p95_before': 200,  # 200ms before
                'latency_p95_after': 2000,  # 2000ms after
                'requests_per_second_before': 100,
                'requests_per_second_after': 50
            },
            'alerts_triggered': [
                'HighErrorRate',
                'HighLatency',
                'ReducedThroughput'
            ]
        }
        
        logger.info(f"Monitoring throttling effects for {api_endpoint}")
        
        return monitoring_result
        
    except Exception as e:
        logger.error(f"Failed to monitor throttling effects: {str(e)}")
        return {
            'action': 'monitor_throttling_effects',
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def notify_slack_action(result: Dict[str, Any]) -> None:
    """Send notification to Slack about the API throttling injection"""
    
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Import requests here to avoid import errors if not installed
        import requests
        
        message = {
            "text": f"🔵 API Throttling Injection - {result['cluster']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔵 API Throttling Injection"
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
                            "text": f"*API Endpoint:* {result.get('api_endpoint', 'Cluster APIs')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Throttle Rate:* {result['throttle_rate']*100}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {result['duration_seconds']}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Method:* {result['method']}"
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
