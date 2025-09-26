"""
EKS Chaos Guardian - CloudWatch Logs Detection
Lambda function to query CloudWatch Logs Insights for failure detection
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
logs_client = boto3.client('logs')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle CloudWatch Logs queries for failure detection
    
    Expected event format:
    {
        "log_groups": ["/aws/eks/cluster-name/application"],
        "query": "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T01:00:00Z",
        "limit": 100
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting CloudWatch Logs query", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        log_groups = event.get('log_groups', [])
        query = event.get('query', '')
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        limit = event.get('limit', 100)
        
        if not start_time:
            # Default to last hour if not specified
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            start_time = start_time.isoformat() + 'Z'
            end_time = end_time.isoformat() + 'Z'
        
        result = {
            'correlation_id': correlation_id,
            'log_groups': log_groups,
            'query': query,
            'start_time': start_time,
            'end_time': end_time,
            'limit': limit,
            'timestamp': datetime.utcnow().isoformat(),
            'query_results': [],
            'status': 'success'
        }
        
        # Execute queries for each log group
        for log_group in log_groups:
            query_result = execute_logs_insights_query(
                log_group, query, start_time, end_time, limit, correlation_id
            )
            result['query_results'].append(query_result)
        
        # Analyze results for failure patterns
        failure_analysis = analyze_logs_for_failures(result['query_results'])
        result['failure_analysis'] = failure_analysis
        
        logger.info(f"CloudWatch Logs query completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"CloudWatch Logs query failed: {str(e)}", extra={
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

def execute_logs_insights_query(log_group: str, query: str, start_time: str, 
                               end_time: str, limit: int, correlation_id: str) -> Dict[str, Any]:
    """Execute a CloudWatch Logs Insights query"""
    
    try:
        # Start the query
        start_query_response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp()),
            endTime=int(datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp()),
            queryString=query,
            limit=limit
        )
        
        query_id = start_query_response['queryId']
        
        # Wait for query to complete
        max_attempts = 30  # 5 minutes max wait
        attempt = 0
        
        while attempt < max_attempts:
            get_query_response = logs_client.get_query_results(queryId=query_id)
            status = get_query_response['status']
            
            if status == 'Complete':
                break
            elif status == 'Failed':
                raise Exception(f"Query failed: {get_query_response.get('statusMessage', 'Unknown error')}")
            
            # Wait 10 seconds before checking again
            import time
            time.sleep(10)
            attempt += 1
        
        if attempt >= max_attempts:
            raise Exception("Query timed out")
        
        # Get the results
        results = get_query_response.get('results', [])
        
        return {
            'log_group': log_group,
            'query_id': query_id,
            'status': status,
            'results': results,
            'result_count': len(results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing query for log group {log_group}: {str(e)}")
        return {
            'log_group': log_group,
            'status': 'error',
            'error': str(e),
            'results': [],
            'result_count': 0,
            'timestamp': datetime.utcnow().isoformat()
        }

def analyze_logs_for_failures(query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze log query results for failure patterns"""
    
    failure_patterns = {
        'oom_killed': {
            'pattern': r'OOMKilled|OutOfMemory|memory limit exceeded',
            'count': 0,
            'examples': []
        },
        'image_pull_error': {
            'pattern': r'ImagePullBackOff|ErrImagePull|Failed to pull image',
            'count': 0,
            'examples': []
        },
        'readiness_failure': {
            'pattern': r'Readiness probe failed|Liveness probe failed|health check failed',
            'count': 0,
            'examples': []
        },
        'crash_loop': {
            'pattern': r'CrashLoopBackOff|Back-off restarting failed container',
            'count': 0,
            'examples': []
        },
        'network_error': {
            'pattern': r'network error|connection refused|timeout|DNS error',
            'count': 0,
            'examples': []
        },
        'disk_pressure': {
            'pattern': r'disk pressure|no space left|filesystem full',
            'count': 0,
            'examples': []
        }
    }
    
    import re
    
    for query_result in query_results:
        if query_result['status'] == 'Complete':
            for result in query_result['results']:
                # Extract message from result
                message = ''
                timestamp = ''
                
                for field in result:
                    if field['field'] == '@message':
                        message = field['value']
                    elif field['field'] == '@timestamp':
                        timestamp = field['value']
                
                # Check against failure patterns
                for pattern_name, pattern_info in failure_patterns.items():
                    if re.search(pattern_info['pattern'], message, re.IGNORECASE):
                        pattern_info['count'] += 1
                        if len(pattern_info['examples']) < 3:  # Keep only first 3 examples
                            pattern_info['examples'].append({
                                'timestamp': timestamp,
                                'message': message[:200] + '...' if len(message) > 200 else message
                            })
    
    # Filter out patterns with no matches
    active_patterns = {k: v for k, v in failure_patterns.items() if v['count'] > 0}
    
    return {
        'total_failures': sum(p['count'] for p in active_patterns.values()),
        'failure_types': active_patterns,
        'analysis_timestamp': datetime.utcnow().isoformat()
    }

def get_common_log_queries() -> Dict[str, str]:
    """Get common log queries for different failure scenarios"""
    
    return {
        'oom_killed': '''
            fields @timestamp, @message, kubernetes.pod_name, kubernetes.container_name
            | filter @message like /OOMKilled/ or @message like /OutOfMemory/
            | sort @timestamp desc
        ''',
        
        'image_pull_error': '''
            fields @timestamp, @message, kubernetes.pod_name
            | filter @message like /ImagePullBackOff/ or @message like /ErrImagePull/
            | sort @timestamp desc
        ''',
        
        'readiness_failure': '''
            fields @timestamp, @message, kubernetes.pod_name
            | filter @message like /Readiness probe failed/ or @message like /Liveness probe failed/
            | sort @timestamp desc
        ''',
        
        'crash_loop': '''
            fields @timestamp, @message, kubernetes.pod_name
            | filter @message like /CrashLoopBackOff/ or @message like /Back-off restarting/
            | sort @timestamp desc
        ''',
        
        'network_error': '''
            fields @timestamp, @message, kubernetes.pod_name
            | filter @message like /connection refused/ or @message like /timeout/ or @message like /DNS error/
            | sort @timestamp desc
        ''',
        
        'disk_pressure': '''
            fields @timestamp, @message, kubernetes.node_name
            | filter @message like /disk pressure/ or @message like /no space left/
            | sort @timestamp desc
        ''',
        
        'general_errors': '''
            fields @timestamp, @message, kubernetes.pod_name
            | filter @message like /ERROR/ or @message like /FATAL/
            | sort @timestamp desc
        '''
    }

def create_detection_query(failure_type: str, namespace: Optional[str] = None, 
                          pod_name: Optional[str] = None) -> str:
    """Create a detection query for a specific failure type"""
    
    queries = get_common_log_queries()
    
    if failure_type not in queries:
        # Return general error query
        query = queries['general_errors']
    else:
        query = queries[failure_type]
    
    # Add namespace filter if specified
    if namespace:
        query = f'''
            fields @timestamp, @message, kubernetes.pod_name, kubernetes.container_name
            | filter kubernetes.namespace_name = "{namespace}"
            {query.split("|", 1)[1] if "|" in query else query}
        '''
    
    # Add pod name filter if specified
    if pod_name:
        query = f'''
            fields @timestamp, @message, kubernetes.pod_name, kubernetes.container_name
            | filter kubernetes.pod_name = "{pod_name}"
            {query.split("|", 1)[1] if "|" in query else query}
        '''
    
    return query.strip()
