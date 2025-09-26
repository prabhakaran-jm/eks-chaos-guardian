"""
EKS Chaos Guardian - Runbook Manager
Lambda function to manage runbook storage, retrieval, and reuse
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import hashlib
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle runbook management requests
    
    Expected event format:
    {
        "action": "store|retrieve|search|update|delete",
        "runbook_id": "optional-runbook-id",
        "runbook_data": {...},
        "search_criteria": {...}
    }
    """
    
    correlation_id = event.get('correlation_id', context.aws_request_id)
    
    try:
        logger.info(f"Starting runbook management", extra={
            'correlation_id': correlation_id,
            'event': event
        })
        
        action = event.get('action')
        runbook_id = event.get('runbook_id')
        runbook_data = event.get('runbook_data', {})
        search_criteria = event.get('search_criteria', {})
        
        result = {
            'correlation_id': correlation_id,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        if action == 'store':
            result['runbook_id'] = store_runbook(runbook_data, correlation_id)
        elif action == 'retrieve':
            result['runbook'] = retrieve_runbook(runbook_id, correlation_id)
        elif action == 'search':
            result['runbooks'] = search_runbooks(search_criteria, correlation_id)
        elif action == 'update':
            result['runbook_id'] = update_runbook(runbook_id, runbook_data, correlation_id)
        elif action == 'delete':
            result['deleted'] = delete_runbook(runbook_id, correlation_id)
        elif action == 'get_similar':
            result['similar_runbooks'] = get_similar_runbooks(runbook_data, correlation_id)
        elif action == 'execute_runbook':
            result['execution_result'] = execute_runbook(runbook_id, event.get('parameters', {}), correlation_id)
        else:
            result['status'] = 'error'
            result['error'] = f'Unknown action: {action}'
        
        logger.info(f"Runbook management completed", extra={
            'correlation_id': correlation_id,
            'result': result
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Runbook management failed: {str(e)}", extra={
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

def store_runbook(runbook_data: Dict[str, Any], correlation_id: str) -> str:
    """Store a new runbook"""
    
    try:
        # Generate unique runbook ID
        runbook_id = str(uuid.uuid4())
        
        # Add metadata
        runbook_data['runbook_id'] = runbook_id
        runbook_data['created_at'] = datetime.utcnow().isoformat()
        runbook_data['updated_at'] = datetime.utcnow().isoformat()
        runbook_data['version'] = 1
        runbook_data['correlation_id'] = correlation_id
        
        # Generate searchable tags
        tags = generate_runbook_tags(runbook_data)
        runbook_data['tags'] = tags
        
        # Store in S3
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-runbooks')
        s3_key = f"runbooks/{runbook_id}.json"
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(runbook_data, indent=2),
            ContentType='application/json',
            Metadata={
                'runbook_id': runbook_id,
                'created_at': runbook_data['created_at'],
                'tags': ','.join(tags)
            }
        )
        
        # Store index in DynamoDB
        store_runbook_index(runbook_id, runbook_data, tags)
        
        logger.info(f"Stored runbook {runbook_id}")
        return runbook_id
        
    except Exception as e:
        logger.error(f"Error storing runbook: {str(e)}")
        raise

def retrieve_runbook(runbook_id: str, correlation_id: str) -> Dict[str, Any]:
    """Retrieve a runbook by ID"""
    
    try:
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-runbooks')
        s3_key = f"runbooks/{runbook_id}.json"
        
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        runbook_data = json.loads(response['Body'].read())
        
        # Update access count
        update_runbook_access_count(runbook_id)
        
        logger.info(f"Retrieved runbook {runbook_id}")
        return runbook_data
        
    except Exception as e:
        logger.error(f"Error retrieving runbook {runbook_id}: {str(e)}")
        raise

def search_runbooks(search_criteria: Dict[str, Any], correlation_id: str) -> List[Dict[str, Any]]:
    """Search for runbooks based on criteria"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        
        # Build query based on search criteria
        if 'pattern_id' in search_criteria:
            # Search by pattern ID
            response = table.get_item(Key={'pattern_id': search_criteria['pattern_id']})
            if 'Item' in response:
                return [response['Item']]
            return []
        
        elif 'tags' in search_criteria:
            # Search by tags
            tags = search_criteria['tags']
            if isinstance(tags, str):
                tags = [tags]
            
            # Scan for runbooks with matching tags
            response = table.scan(
                FilterExpression='contains(tags, :tag)',
                ExpressionAttributeValues={':tag': tags[0]}
            )
            
            return response.get('Items', [])
        
        elif 'failure_type' in search_criteria:
            # Search by failure type
            failure_type = search_criteria['failure_type']
            response = table.scan(
                FilterExpression='contains(failure_type, :failure_type)',
                ExpressionAttributeValues={':failure_type': failure_type}
            )
            
            return response.get('Items', [])
        
        elif 'cluster' in search_criteria:
            # Search by cluster
            cluster = search_criteria['cluster']
            response = table.scan(
                FilterExpression='contains(cluster, :cluster)',
                ExpressionAttributeValues={':cluster': cluster}
            )
            
            return response.get('Items', [])
        
        else:
            # Return all runbooks
            response = table.scan()
            return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error searching runbooks: {str(e)}")
        return []

def update_runbook(runbook_id: str, runbook_data: Dict[str, Any], correlation_id: str) -> str:
    """Update an existing runbook"""
    
    try:
        # Get existing runbook
        existing_runbook = retrieve_runbook(runbook_id, correlation_id)
        
        # Update fields
        existing_runbook.update(runbook_data)
        existing_runbook['updated_at'] = datetime.utcnow().isoformat()
        existing_runbook['version'] = existing_runbook.get('version', 1) + 1
        existing_runbook['correlation_id'] = correlation_id
        
        # Update tags
        tags = generate_runbook_tags(existing_runbook)
        existing_runbook['tags'] = tags
        
        # Store updated runbook in S3
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-runbooks')
        s3_key = f"runbooks/{runbook_id}.json"
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(existing_runbook, indent=2),
            ContentType='application/json',
            Metadata={
                'runbook_id': runbook_id,
                'updated_at': existing_runbook['updated_at'],
                'tags': ','.join(tags)
            }
        )
        
        # Update index in DynamoDB
        store_runbook_index(runbook_id, existing_runbook, tags)
        
        logger.info(f"Updated runbook {runbook_id}")
        return runbook_id
        
    except Exception as e:
        logger.error(f"Error updating runbook {runbook_id}: {str(e)}")
        raise

def delete_runbook(runbook_id: str, correlation_id: str) -> bool:
    """Delete a runbook"""
    
    try:
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-runbooks')
        s3_key = f"runbooks/{runbook_id}.json"
        
        # Delete from S3
        s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)
        
        # Delete from DynamoDB
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        table.delete_item(Key={'pattern_id': runbook_id})
        
        logger.info(f"Deleted runbook {runbook_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting runbook {runbook_id}: {str(e)}")
        return False

def get_similar_runbooks(runbook_data: Dict[str, Any], correlation_id: str) -> List[Dict[str, Any]]:
    """Find similar runbooks based on content"""
    
    try:
        # Extract key features for similarity matching
        features = extract_runbook_features(runbook_data)
        
        # Search for runbooks with similar features
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        
        # Get all runbooks and calculate similarity
        response = table.scan()
        all_runbooks = response.get('Items', [])
        
        similar_runbooks = []
        
        for runbook in all_runbooks:
            similarity_score = calculate_similarity(features, runbook)
            if similarity_score > 0.7:  # 70% similarity threshold
                runbook['similarity_score'] = similarity_score
                similar_runbooks.append(runbook)
        
        # Sort by similarity score
        similar_runbooks.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_runbooks[:10]  # Return top 10 similar runbooks
        
    except Exception as e:
        logger.error(f"Error finding similar runbooks: {str(e)}")
        return []

def execute_runbook(runbook_id: str, parameters: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Execute a runbook with given parameters"""
    
    try:
        # Get runbook
        runbook = retrieve_runbook(runbook_id, correlation_id)
        
        # Execute runbook steps
        execution_result = {
            'runbook_id': runbook_id,
            'execution_id': str(uuid.uuid4()),
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running',
            'steps': [],
            'parameters': parameters
        }
        
        steps = runbook.get('steps', [])
        
        for i, step in enumerate(steps):
            step_result = execute_runbook_step(step, parameters, correlation_id)
            execution_result['steps'].append(step_result)
            
            if step_result['status'] == 'failed':
                execution_result['status'] = 'failed'
                execution_result['failed_at'] = datetime.utcnow().isoformat()
                break
        
        if execution_result['status'] == 'running':
            execution_result['status'] = 'completed'
            execution_result['completed_at'] = datetime.utcnow().isoformat()
        
        # Store execution result
        store_execution_result(execution_result)
        
        logger.info(f"Executed runbook {runbook_id}")
        return execution_result
        
    except Exception as e:
        logger.error(f"Error executing runbook {runbook_id}: {str(e)}")
        return {
            'runbook_id': runbook_id,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def execute_runbook_step(step: Dict[str, Any], parameters: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Execute a single runbook step"""
    
    try:
        step_type = step.get('type')
        step_config = step.get('config', {})
        
        step_result = {
            'step_type': step_type,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running'
        }
        
        if step_type == 'lambda_invoke':
            # Invoke Lambda function
            lambda_client = boto3.client('lambda')
            function_name = step_config.get('function_name')
            payload = step_config.get('payload', {})
            
            # Merge parameters into payload
            payload.update(parameters)
            
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            step_result['result'] = result
            step_result['status'] = 'completed' if result.get('statusCode') == 200 else 'failed'
            
        elif step_type == 'k8s_operation':
            # Execute Kubernetes operation
            operation = step_config.get('operation')
            cluster = step_config.get('cluster')
            namespace = step_config.get('namespace')
            resource = step_config.get('resource')
            
            # This would typically invoke the K8s operations Lambda
            step_result['result'] = {
                'operation': operation,
                'cluster': cluster,
                'namespace': namespace,
                'resource': resource,
                'status': 'simulated'
            }
            step_result['status'] = 'completed'
            
        elif step_type == 'wait':
            # Wait for specified duration
            duration = step_config.get('duration', 30)
            import time
            time.sleep(duration)
            step_result['status'] = 'completed'
            
        else:
            step_result['status'] = 'failed'
            step_result['error'] = f'Unknown step type: {step_type}'
        
        step_result['completed_at'] = datetime.utcnow().isoformat()
        return step_result
        
    except Exception as e:
        logger.error(f"Error executing runbook step: {str(e)}")
        return {
            'step_type': step.get('type'),
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def generate_runbook_tags(runbook_data: Dict[str, Any]) -> List[str]:
    """Generate searchable tags for a runbook"""
    
    tags = []
    
    # Add failure type tags
    failure_type = runbook_data.get('failure_type')
    if failure_type:
        tags.append(f"failure:{failure_type}")
    
    # Add cluster tags
    cluster = runbook_data.get('cluster')
    if cluster:
        tags.append(f"cluster:{cluster}")
    
    # Add namespace tags
    namespace = runbook_data.get('namespace')
    if namespace:
        tags.append(f"namespace:{namespace}")
    
    # Add resource tags
    resource_type = runbook_data.get('resource_type')
    if resource_type:
        tags.append(f"resource:{resource_type}")
    
    # Add severity tags
    severity = runbook_data.get('severity', 'medium')
    tags.append(f"severity:{severity}")
    
    # Add action tags
    actions = runbook_data.get('actions', [])
    for action in actions:
        if isinstance(action, dict):
            action_type = action.get('type')
            if action_type:
                tags.append(f"action:{action_type}")
    
    return tags

def store_runbook_index(runbook_id: str, runbook_data: Dict[str, Any], tags: List[str]) -> None:
    """Store runbook index in DynamoDB"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        
        index_item = {
            'pattern_id': runbook_id,
            'title': runbook_data.get('title', 'Untitled Runbook'),
            'description': runbook_data.get('description', ''),
            'failure_type': runbook_data.get('failure_type', ''),
            'cluster': runbook_data.get('cluster', ''),
            'namespace': runbook_data.get('namespace', ''),
            'resource_type': runbook_data.get('resource_type', ''),
            'severity': runbook_data.get('severity', 'medium'),
            'tags': tags,
            'created_at': runbook_data.get('created_at'),
            'updated_at': runbook_data.get('updated_at'),
            'version': runbook_data.get('version', 1),
            'access_count': 0,
            'success_count': 0,
            'failure_count': 0
        }
        
        table.put_item(Item=index_item)
        
    except Exception as e:
        logger.error(f"Error storing runbook index: {str(e)}")

def update_runbook_access_count(runbook_id: str) -> None:
    """Update access count for a runbook"""
    
    try:
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        table.update_item(
            Key={'pattern_id': runbook_id},
            UpdateExpression='ADD access_count :inc',
            ExpressionAttributeValues={':inc': 1}
        )
    except Exception as e:
        logger.error(f"Error updating access count: {str(e)}")

def store_execution_result(execution_result: Dict[str, Any]) -> None:
    """Store runbook execution result"""
    
    try:
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-runbooks')
        s3_key = f"executions/{execution_result['execution_id']}.json"
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(execution_result, indent=2),
            ContentType='application/json'
        )
        
        # Update success/failure counts
        runbook_id = execution_result['runbook_id']
        table = dynamodb.Table('eks-chaos-guardian-runbook-index')
        
        if execution_result['status'] == 'completed':
            table.update_item(
                Key={'pattern_id': runbook_id},
                UpdateExpression='ADD success_count :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        else:
            table.update_item(
                Key={'pattern_id': runbook_id},
                UpdateExpression='ADD failure_count :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        
    except Exception as e:
        logger.error(f"Error storing execution result: {str(e)}")

def extract_runbook_features(runbook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract features for similarity matching"""
    
    features = {
        'failure_type': runbook_data.get('failure_type', ''),
        'cluster': runbook_data.get('cluster', ''),
        'namespace': runbook_data.get('namespace', ''),
        'resource_type': runbook_data.get('resource_type', ''),
        'severity': runbook_data.get('severity', 'medium'),
        'actions': [action.get('type', '') for action in runbook_data.get('actions', [])],
        'tags': runbook_data.get('tags', [])
    }
    
    return features

def calculate_similarity(features1: Dict[str, Any], runbook2: Dict[str, Any]) -> float:
    """Calculate similarity between two runbooks"""
    
    similarity_score = 0.0
    total_weight = 0.0
    
    # Weight different features
    weights = {
        'failure_type': 0.3,
        'cluster': 0.1,
        'namespace': 0.1,
        'resource_type': 0.2,
        'severity': 0.1,
        'actions': 0.2
    }
    
    for feature, weight in weights.items():
        if feature in features1 and feature in runbook2:
            if features1[feature] == runbook2[feature]:
                similarity_score += weight
            total_weight += weight
    
    return similarity_score / total_weight if total_weight > 0 else 0.0

def create_sample_runbooks() -> List[Dict[str, Any]]:
    """Create sample runbooks for demonstration"""
    
    sample_runbooks = [
        {
            'title': 'Fix OOMKilled Pods',
            'description': 'Automated remediation for Out of Memory killed pods',
            'failure_type': 'oom_killed',
            'severity': 'high',
            'steps': [
                {
                    'type': 'k8s_operation',
                    'config': {
                        'operation': 'patch_deployment',
                        'cluster': 'eks-cluster',
                        'namespace': 'default',
                        'resource': 'my-app',
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
                    }
                },
                {
                    'type': 'k8s_operation',
                    'config': {
                        'operation': 'rollout_restart',
                        'cluster': 'eks-cluster',
                        'namespace': 'default',
                        'resource': 'my-app'
                    }
                }
            ]
        },
        {
            'title': 'Fix ImagePullBackOff',
            'description': 'Remediate image pull failures',
            'failure_type': 'image_pull_error',
            'severity': 'medium',
            'steps': [
                {
                    'type': 'k8s_operation',
                    'config': {
                        'operation': 'rollout_restart',
                        'cluster': 'eks-cluster',
                        'namespace': 'default',
                        'resource': 'my-app'
                    }
                },
                {
                    'type': 'wait',
                    'config': {
                        'duration': 30
                    }
                }
            ]
        },
        {
            'title': 'Scale Up Deployment',
            'description': 'Scale deployment to handle increased load',
            'failure_type': 'high_load',
            'severity': 'medium',
            'steps': [
                {
                    'type': 'k8s_operation',
                    'config': {
                        'operation': 'scale_deployment',
                        'cluster': 'eks-cluster',
                        'namespace': 'default',
                        'resource': 'my-app',
                        'replicas': 5
                    }
                }
            ]
        }
    ]
    
    return sample_runbooks
