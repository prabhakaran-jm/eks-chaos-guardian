"""
EKS Chaos Guardian - CloudWatch Metrics Detection
Lambda function to query CloudWatch metrics for failure detection
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
cloudwatch_client = boto3.client('cloudwatch')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle CloudWatch metrics queries for failure detection
    
    Expected event format:
    {
        "namespace": "AWS/EKS",
        "metric_name": "cluster_failed_request_count",
        "dimensions": {
            "ClusterName": "my-cluster"
        },
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T01:00:00Z",
        "period": 300,
        "statistics": ["Sum", "Average"]
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting CloudWatch metrics query", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        namespace = event.get('namespace', 'AWS/EKS')
        metric_name = event.get('metric_name')
        dimensions = event.get('dimensions', {})
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        period = event.get('period', 300)
        statistics = event.get('statistics', ['Sum', 'Average'])
        
        if not start_time:
            # Default to last hour if not specified
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            start_time = start_time.isoformat() + 'Z'
            end_time = end_time.isoformat() + 'Z'
        
        result = {
            'correlation_id': correlation_id,
            'namespace': namespace,
            'metric_name': metric_name,
            'dimensions': dimensions,
            'start_time': start_time,
            'end_time': end_time,
            'period': period,
            'statistics': statistics,
            'timestamp': datetime.utcnow().isoformat(),
            'metric_data': [],
            'status': 'success'
        }
        
        if metric_name:
            # Query specific metric
            metric_data = get_metric_data(
                namespace, metric_name, dimensions, start_time, end_time, period, statistics
            )
            result['metric_data'] = metric_data
        else:
            # Query multiple relevant metrics for EKS health
            health_metrics = get_eks_health_metrics(namespace, dimensions, start_time, end_time, period)
            result['metric_data'] = health_metrics
        
        # Analyze metrics for anomalies
        anomaly_analysis = analyze_metrics_for_anomalies(result['metric_data'])
        result['anomaly_analysis'] = anomaly_analysis
        
        logger.info(f"CloudWatch metrics query completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"CloudWatch metrics query failed: {str(e)}", extra={
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

def get_metric_data(namespace: str, metric_name: str, dimensions: Dict[str, str], 
                   start_time: str, end_time: str, period: int, statistics: List[str]) -> List[Dict[str, Any]]:
    """Get metric data from CloudWatch"""
    
    try:
        # Convert time strings to datetime objects
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Prepare dimensions list
        dimensions_list = [{'Name': k, 'Value': v} for k, v in dimensions.items()]
        
        response = cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions_list,
            StartTime=start_dt,
            EndTime=end_dt,
            Period=period,
            Statistics=statistics
        )
        
        return response.get('Datapoints', [])
        
    except Exception as e:
        logger.error(f"Error getting metric data: {str(e)}")
        return []

def get_eks_health_metrics(namespace: str, dimensions: Dict[str, str], 
                          start_time: str, end_time: str, period: int) -> List[Dict[str, Any]]:
    """Get comprehensive EKS health metrics"""
    
    health_metrics = []
    
    # Define key EKS metrics to monitor
    eks_metrics = [
        {
            'name': 'cluster_failed_request_count',
            'statistics': ['Sum'],
            'description': 'Number of failed API requests to the cluster'
        },
        {
            'name': 'cluster_total_request_count',
            'statistics': ['Sum'],
            'description': 'Total number of API requests to the cluster'
        },
        {
            'name': 'cluster_request_rate',
            'statistics': ['Average'],
            'description': 'Rate of API requests to the cluster'
        }
    ]
    
    for metric_info in eks_metrics:
        try:
            metric_data = get_metric_data(
                namespace, metric_info['name'], dimensions, start_time, end_time, period, metric_info['statistics']
            )
            
            health_metrics.append({
                'metric_name': metric_info['name'],
                'description': metric_info['description'],
                'statistics': metric_info['statistics'],
                'data': metric_data,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting metric {metric_info['name']}: {str(e)}")
            health_metrics.append({
                'metric_name': metric_info['name'],
                'description': metric_info['description'],
                'statistics': metric_info['statistics'],
                'data': [],
                'status': 'error',
                'error': str(e)
            })
    
    return health_metrics

def analyze_metrics_for_anomalies(metric_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze metrics for anomalies and failure patterns"""
    
    anomaly_analysis = {
        'anomalies_detected': False,
        'failure_indicators': [],
        'threshold_violations': [],
        'trend_analysis': {},
        'analysis_timestamp': datetime.utcnow().isoformat()
    }
    
    for metric in metric_data:
        if isinstance(metric, dict) and 'metric_name' in metric:
            # Handle structured metric data
            metric_name = metric['metric_name']
            data_points = metric.get('data', [])
            
            if data_points:
                analysis = analyze_metric_trend(metric_name, data_points)
                if analysis['anomalies_detected']:
                    anomaly_analysis['anomalies_detected'] = True
                    anomaly_analysis['failure_indicators'].extend(analysis['failure_indicators'])
                    anomaly_analysis['threshold_violations'].extend(analysis['threshold_violations'])
                
                anomaly_analysis['trend_analysis'][metric_name] = analysis
        
        elif isinstance(metric, dict) and 'Timestamp' in metric:
            # Handle direct datapoint data
            analysis = analyze_datapoint_anomaly(metric)
            if analysis['anomaly_detected']:
                anomaly_analysis['anomalies_detected'] = True
                anomaly_analysis['failure_indicators'].append(analysis)
    
    return anomaly_analysis

def analyze_metric_trend(metric_name: str, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze trend of a specific metric"""
    
    analysis = {
        'metric_name': metric_name,
        'anomalies_detected': False,
        'failure_indicators': [],
        'threshold_violations': [],
        'trend': 'stable',
        'data_points_count': len(data_points)
    }
    
    if not data_points:
        return analysis
    
    # Sort data points by timestamp
    sorted_points = sorted(data_points, key=lambda x: x['Timestamp'])
    
    # Define thresholds for different metrics
    thresholds = {
        'cluster_failed_request_count': {'Sum': 10},  # More than 10 failed requests
        'cluster_request_rate': {'Average': 1000},    # More than 1000 requests per minute
        'cpu_utilization': {'Average': 80},           # More than 80% CPU
        'memory_utilization': {'Average': 85}         # More than 85% memory
    }
    
    # Check for threshold violations
    metric_thresholds = thresholds.get(metric_name, {})
    
    for point in sorted_points:
        for stat, threshold in metric_thresholds.items():
            if stat in point and point[stat] > threshold:
                analysis['threshold_violations'].append({
                    'timestamp': point['Timestamp'].isoformat(),
                    'statistic': stat,
                    'value': point[stat],
                    'threshold': threshold,
                    'severity': 'high' if point[stat] > threshold * 1.5 else 'medium'
                })
                analysis['anomalies_detected'] = True
    
    # Analyze trend
    if len(sorted_points) >= 2:
        first_value = sorted_points[0].get('Average', sorted_points[0].get('Sum', 0))
        last_value = sorted_points[-1].get('Average', sorted_points[-1].get('Sum', 0))
        
        if last_value > first_value * 1.5:
            analysis['trend'] = 'increasing'
            analysis['failure_indicators'].append({
                'type': 'increasing_trend',
                'description': f'{metric_name} showing increasing trend',
                'first_value': first_value,
                'last_value': last_value,
                'increase_percentage': ((last_value - first_value) / first_value) * 100
            })
            analysis['anomalies_detected'] = True
        elif last_value < first_value * 0.5:
            analysis['trend'] = 'decreasing'
        else:
            analysis['trend'] = 'stable'
    
    return analysis

def analyze_datapoint_anomaly(datapoint: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single datapoint for anomalies"""
    
    analysis = {
        'timestamp': datapoint['Timestamp'].isoformat(),
        'anomaly_detected': False,
        'type': 'unknown',
        'severity': 'low',
        'description': ''
    }
    
    # Check for high values in different statistics
    for stat in ['Sum', 'Average', 'Maximum']:
        if stat in datapoint:
            value = datapoint[stat]
            
            # Define anomaly thresholds
            if stat == 'Sum' and value > 100:
                analysis['anomaly_detected'] = True
                analysis['type'] = 'high_sum_value'
                analysis['severity'] = 'high' if value > 500 else 'medium'
                analysis['description'] = f'High {stat} value: {value}'
                break
            elif stat == 'Average' and value > 80:
                analysis['anomaly_detected'] = True
                analysis['type'] = 'high_average_value'
                analysis['severity'] = 'high' if value > 95 else 'medium'
                analysis['description'] = f'High {stat} value: {value}'
                break
            elif stat == 'Maximum' and value > 90:
                analysis['anomaly_detected'] = True
                analysis['type'] = 'high_maximum_value'
                analysis['severity'] = 'high' if value > 99 else 'medium'
                analysis['description'] = f'High {stat} value: {value}'
                break
    
    return analysis

def get_common_eks_metrics() -> Dict[str, Dict[str, Any]]:
    """Get common EKS metrics for monitoring"""
    
    return {
        'cluster_health': {
            'namespace': 'AWS/EKS',
            'metrics': [
                'cluster_failed_request_count',
                'cluster_total_request_count',
                'cluster_request_rate'
            ],
            'dimensions': ['ClusterName'],
            'description': 'Cluster API request metrics'
        },
        'node_health': {
            'namespace': 'AWS/EKS',
            'metrics': [
                'node_cpu_utilization',
                'node_memory_utilization',
                'node_disk_utilization'
            ],
            'dimensions': ['ClusterName', 'NodeName'],
            'description': 'Node resource utilization metrics'
        },
        'pod_health': {
            'namespace': 'AWS/EKS',
            'metrics': [
                'pod_cpu_utilization',
                'pod_memory_utilization',
                'pod_restart_count'
            ],
            'dimensions': ['ClusterName', 'Namespace', 'PodName'],
            'description': 'Pod resource and restart metrics'
        }
    }

def create_health_check_query(cluster_name: str, namespace: Optional[str] = None, 
                             pod_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a comprehensive health check query for EKS"""
    
    query = {
        'cluster_metrics': {
            'namespace': 'AWS/EKS',
            'dimensions': {'ClusterName': cluster_name},
            'metrics': ['cluster_failed_request_count', 'cluster_total_request_count']
        }
    }
    
    if namespace:
        query['namespace_metrics'] = {
            'namespace': 'AWS/EKS',
            'dimensions': {'ClusterName': cluster_name, 'Namespace': namespace},
            'metrics': ['pod_cpu_utilization', 'pod_memory_utilization']
        }
    
    if pod_name:
        query['pod_metrics'] = {
            'namespace': 'AWS/EKS',
            'dimensions': {'ClusterName': cluster_name, 'PodName': pod_name},
            'metrics': ['pod_cpu_utilization', 'pod_memory_utilization', 'pod_restart_count']
        }
    
    return query
