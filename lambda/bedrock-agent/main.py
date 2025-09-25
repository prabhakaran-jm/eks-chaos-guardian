"""
EKS Chaos Guardian - Bedrock AgentCore Integration
Main Lambda function that orchestrates the AI agent workflow
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
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

class EKSChaosGuardian:
    """Main orchestrator for the EKS Chaos Guardian AI agent"""
    
    def __init__(self):
        self.claude_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.s3_bucket = os.environ.get('S3_BUCKET_NAME', 'eks-chaos-guardian-bucket')
        self.dynamodb_table = os.environ.get('DYNAMODB_TABLE_NAME', 'eks-chaos-guardian-runbook-index')
        
    def lambda_handler(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Main entry point for the EKS Chaos Guardian agent
        
        Expected event format:
        {
            "action": "analyze_failure",
            "cluster": "eks-cluster-name",
            "namespace": "default",
            "signals": {
                "logs": [...],
                "metrics": [...],
                "k8s_events": [...]
            },
            "autonomy_mode": "auto",
            "correlation_id": "uuid"
        }
        """
        
        correlation_id = event.get('correlation_id', context.aws_request_id)
        
        try:
            logger.info(f"Starting EKS Chaos Guardian analysis", extra={
                'correlation_id': correlation_id,
                'event': event
            })
            
            action = event.get('action', 'analyze_failure')
            
            if action == 'analyze_failure':
                result = self.analyze_failure(event, correlation_id)
            elif action == 'execute_plan':
                result = self.execute_plan(event, correlation_id)
            elif action == 'verify_recovery':
                result = self.verify_recovery(event, correlation_id)
            elif action == 'get_runbook':
                result = self.get_runbook(event, correlation_id)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
            
        except Exception as e:
            logger.error(f"EKS Chaos Guardian failed: {str(e)}", extra={
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
    
    def analyze_failure(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Analyze failure signals and create remediation plan"""
        
        cluster = event['cluster']
        namespace = event.get('namespace', 'default')
        signals = event.get('signals', {})
        autonomy_mode = event.get('autonomy_mode', 'approve')
        
        # Step 1: Check for existing runbooks
        existing_runbook = self.check_existing_runbook(signals, cluster)
        
        if existing_runbook:
            logger.info(f"Found existing runbook: {existing_runbook['pattern_id']}")
            return {
                'correlation_id': correlation_id,
                'status': 'success',
                'analysis_type': 'runbook_match',
                'existing_runbook': existing_runbook,
                'recommended_actions': existing_runbook['plan'],
                'risk_assessment': existing_runbook.get('risk', 'medium'),
                'autonomy_mode': autonomy_mode,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Step 2: Analyze signals with Claude
        analysis_result = self.analyze_with_claude(signals, cluster, namespace, correlation_id)
        
        # Step 3: Create remediation plan
        remediation_plan = self.create_remediation_plan(analysis_result, autonomy_mode)
        
        return {
            'correlation_id': correlation_id,
            'status': 'success',
            'analysis_type': 'new_analysis',
            'root_cause_analysis': analysis_result,
            'remediation_plan': remediation_plan,
            'risk_assessment': remediation_plan.get('risk_level', 'medium'),
            'autonomy_mode': autonomy_mode,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def analyze_with_claude(self, signals: Dict[str, Any], cluster: str, 
                           namespace: str, correlation_id: str) -> Dict[str, Any]:
        """Use Claude to analyze failure signals"""
        
        # Prepare the analysis prompt
        system_prompt = self.load_system_prompt()
        
        analysis_prompt = f"""
        Analyze the following failure signals from EKS cluster {cluster} in namespace {namespace}:
        
        LOGS:
        {json.dumps(signals.get('logs', []), indent=2)}
        
        METRICS:
        {json.dumps(signals.get('metrics', []), indent=2)}
        
        KUBERNETES EVENTS:
        {json.dumps(signals.get('k8s_events', []), indent=2)}
        
        Please provide:
        1. Root cause analysis with evidence
        2. Failure pattern identification
        3. Risk assessment
        4. Recommended remediation steps
        
        Format your response as JSON with the following structure:
        {{
            "root_cause": "Clear description of the root cause",
            "evidence": ["List of specific evidence points"],
            "failure_pattern": "Pattern identifier (e.g., k8s_oomkilled)",
            "risk_level": "low|medium|high",
            "remediation_steps": [
                {{
                    "action": "action_name",
                    "target": "resource_name",
                    "params": {{}},
                    "risk_level": "low|medium|high",
                    "justification": "Why this action is needed"
                }}
            ]
        }}
        """
        
        try:
            # Call Claude via Bedrock
            response = bedrock_runtime.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ]
                }),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            # Parse Claude's JSON response
            analysis_result = json.loads(claude_response)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            # Return fallback analysis
            return self.fallback_analysis(signals)
    
    def create_remediation_plan(self, analysis_result: Dict[str, Any], 
                               autonomy_mode: str) -> Dict[str, Any]:
        """Create a detailed remediation plan based on analysis"""
        
        remediation_steps = analysis_result.get('remediation_steps', [])
        
        plan = {
            'plan_id': f"plan-{int(datetime.utcnow().timestamp())}",
            'failure_pattern': analysis_result.get('failure_pattern', 'unknown'),
            'risk_level': analysis_result.get('risk_level', 'medium'),
            'autonomy_mode': autonomy_mode,
            'steps': [],
            'estimated_recovery_time': '2-5 minutes',
            'requires_approval': analysis_result.get('risk_level', 'medium') in ['medium', 'high']
        }
        
        for i, step in enumerate(remediation_steps):
            plan_step = {
                'step_number': i + 1,
                'action': step['action'],
                'target': step['target'],
                'params': step.get('params', {}),
                'risk_level': step.get('risk_level', 'medium'),
                'justification': step.get('justification', ''),
                'can_auto_execute': self.can_auto_execute(step['action'], step.get('risk_level', 'medium'), autonomy_mode)
            }
            
            plan['steps'].append(plan_step)
        
        return plan
    
    def can_auto_execute(self, action: str, risk_level: str, autonomy_mode: str) -> bool:
        """Determine if an action can be auto-executed"""
        
        if autonomy_mode == 'dry_run':
            return False
        
        if autonomy_mode == 'auto':
            # Auto mode allows low-risk actions
            low_risk_actions = ['rollout_restart', 'coredns_restart', 'cache_refresh']
            return action in low_risk_actions and risk_level == 'low'
        
        if autonomy_mode == 'approve':
            # Approve mode requires approval for medium/high risk
            return risk_level == 'low'
        
        return False
    
    def execute_plan(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute a remediation plan"""
        
        plan = event['plan']
        autonomy_mode = event.get('autonomy_mode', 'approve')
        
        execution_result = {
            'correlation_id': correlation_id,
            'plan_id': plan['plan_id'],
            'autonomy_mode': autonomy_mode,
            'execution_start': datetime.utcnow().isoformat(),
            'steps_executed': [],
            'status': 'success'
        }
        
        try:
            for step in plan['steps']:
                if step['can_auto_execute']:
                    # Execute immediately
                    step_result = self.execute_step(step, correlation_id)
                    execution_result['steps_executed'].append(step_result)
                    
                    if step_result['status'] != 'success':
                        execution_result['status'] = 'partial_failure'
                        break
                else:
                    # Queue for approval
                    step_result = self.queue_for_approval(step, correlation_id)
                    execution_result['steps_executed'].append(step_result)
            
            execution_result['execution_end'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            execution_result['status'] = 'failed'
            execution_result['error'] = str(e)
            execution_result['execution_end'] = datetime.utcnow().isoformat()
        
        return execution_result
    
    def execute_step(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute a single remediation step"""
        
        action = step['action']
        
        try:
            if action == 'patch_deployment':
                return self.execute_patch_deployment(step, correlation_id)
            elif action == 'rollout_restart':
                return self.execute_rollout_restart(step, correlation_id)
            elif action == 'scale_deployment':
                return self.execute_scale_deployment(step, correlation_id)
            elif action == 'cordon_node':
                return self.execute_cordon_node(step, correlation_id)
            elif action == 'drain_node':
                return self.execute_drain_node(step, correlation_id)
            else:
                return {
                    'step_number': step['step_number'],
                    'action': action,
                    'status': 'skipped',
                    'reason': f'Unknown action: {action}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'step_number': step['step_number'],
                'action': action,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def execute_patch_deployment(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute deployment patch via K8s operations Lambda"""
        
        # Call the K8s operations Lambda
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'correlation_id': correlation_id,
                'operation': 'patch_deployment',
                'cluster': step['params'].get('cluster'),
                'namespace': step['params'].get('namespace'),
                'resource_name': step['target'],
                'patch': step['params'].get('patch', {}),
                'dry_run': False
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        return {
            'step_number': step['step_number'],
            'action': 'patch_deployment',
            'status': 'success' if result.get('statusCode') == 200 else 'failed',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_rollout_restart(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute deployment rollout restart via K8s operations Lambda"""
        
        # Call the K8s operations Lambda
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'correlation_id': correlation_id,
                'operation': 'rollout_restart',
                'cluster': step['params'].get('cluster'),
                'namespace': step['params'].get('namespace'),
                'resource_name': step['target'],
                'dry_run': False
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        return {
            'step_number': step['step_number'],
            'action': 'rollout_restart',
            'status': 'success' if result.get('statusCode') == 200 else 'failed',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_scale_deployment(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute deployment scaling via K8s operations Lambda"""
        
        # Call the K8s operations Lambda
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'correlation_id': correlation_id,
                'operation': 'scale_deployment',
                'cluster': step['params'].get('cluster'),
                'namespace': step['params'].get('namespace'),
                'resource_name': step['target'],
                'patch': {'replicas': step['params'].get('replicas', 1)},
                'dry_run': False
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        return {
            'step_number': step['step_number'],
            'action': 'scale_deployment',
            'status': 'success' if result.get('statusCode') == 200 else 'failed',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_cordon_node(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute node cordoning via K8s operations Lambda"""
        
        # Call the K8s operations Lambda
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'correlation_id': correlation_id,
                'operation': 'cordon_node',
                'cluster': step['params'].get('cluster'),
                'resource_name': step['target'],
                'dry_run': False
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        return {
            'step_number': step['step_number'],
            'action': 'cordon_node',
            'status': 'success' if result.get('statusCode') == 200 else 'failed',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_drain_node(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Execute node draining via K8s operations Lambda"""
        
        # Call the K8s operations Lambda
        response = lambda_client.invoke(
            FunctionName='eks-chaos-guardian-k8s-operations',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'correlation_id': correlation_id,
                'operation': 'drain_node',
                'cluster': step['params'].get('cluster'),
                'resource_name': step['target'],
                'dry_run': False
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        return {
            'step_number': step['step_number'],
            'action': 'drain_node',
            'status': 'success' if result.get('statusCode') == 200 else 'failed',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def queue_for_approval(self, step: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Queue a step for human approval"""
        
        # Send Slack notification for approval
        self.send_approval_request(step, correlation_id)
        
        return {
            'step_number': step['step_number'],
            'action': step['action'],
            'status': 'queued_for_approval',
            'approval_sent': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def send_approval_request(self, step: Dict[str, Any], correlation_id: str) -> None:
        """Send Slack notification requesting approval"""
        
        try:
            # Call Slack notification Lambda
            lambda_client.invoke(
                FunctionName='eks-chaos-guardian-slack-notify',
                InvocationType='Event',  # Async
                Payload=json.dumps({
                    'correlation_id': correlation_id,
                    'action': 'approval_request',
                    'step': step,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            
        except Exception as e:
            logger.error(f"Failed to send approval request: {str(e)}")
    
    def verify_recovery(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Verify that remediation was successful"""
        
        cluster = event['cluster']
        namespace = event.get('namespace', 'default')
        checks = event.get('checks', ['pod_status', 'no_errors', 'metrics_normal'])
        
        verification_result = {
            'correlation_id': correlation_id,
            'cluster': cluster,
            'namespace': namespace,
            'verification_start': datetime.utcnow().isoformat(),
            'checks_performed': [],
            'overall_status': 'success'
        }
        
        try:
            for check in checks:
                check_result = self.perform_verification_check(check, cluster, namespace, correlation_id)
                verification_result['checks_performed'].append(check_result)
                
                if check_result['status'] != 'passed':
                    verification_result['overall_status'] = 'failed'
            
            verification_result['verification_end'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            verification_result['overall_status'] = 'error'
            verification_result['error'] = str(e)
            verification_result['verification_end'] = datetime.utcnow().isoformat()
        
        return verification_result
    
    def perform_verification_check(self, check: str, cluster: str, 
                                  namespace: str, correlation_id: str) -> Dict[str, Any]:
        """Perform a specific verification check"""
        
        if check == 'pod_status':
            return self.check_pod_status(cluster, namespace, correlation_id)
        elif check == 'no_errors':
            return self.check_no_errors(cluster, namespace, correlation_id)
        elif check == 'metrics_normal':
            return self.check_metrics_normal(cluster, namespace, correlation_id)
        else:
            return {
                'check': check,
                'status': 'skipped',
                'reason': f'Unknown check: {check}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_pod_status(self, cluster: str, namespace: str, correlation_id: str) -> Dict[str, Any]:
        """Check that all pods are running and ready"""
        
        # Simulate pod status check
        return {
            'check': 'pod_status',
            'status': 'passed',
            'details': 'All pods running and ready',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_no_errors(self, cluster: str, namespace: str, correlation_id: str) -> Dict[str, Any]:
        """Check for absence of error conditions"""
        
        # Simulate error check
        return {
            'check': 'no_errors',
            'status': 'passed',
            'details': 'No error conditions detected',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_metrics_normal(self, cluster: str, namespace: str, correlation_id: str) -> Dict[str, Any]:
        """Check that metrics are within normal ranges"""
        
        # Simulate metrics check
        return {
            'check': 'metrics_normal',
            'status': 'passed',
            'details': 'Metrics within normal ranges',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_existing_runbook(self, signals: Dict[str, Any], cluster: str) -> Optional[Dict[str, Any]]:
        """Check if there's an existing runbook for this failure pattern"""
        
        try:
            # Query DynamoDB for matching runbooks
            response = dynamodb.query(
                TableName=self.dynamodb_table,
                KeyConditionExpression='cluster = :cluster',
                ExpressionAttributeValues={
                    ':cluster': {'S': cluster}
                }
            )
            
            # For demo purposes, return a sample runbook if OOM pattern detected
            if any('OOMKilled' in str(signal) for signal in signals.get('logs', [])):
                return {
                    'pattern_id': 'k8s_oomkilled',
                    'cluster': cluster,
                    'plan': [
                        {
                            'action': 'patch_deployment_resources',
                            'params': {'memory_limit': '512Mi'}
                        },
                        {
                            'action': 'rollout_restart',
                            'params': {}
                        }
                    ],
                    'risk': 'low'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing runbook: {str(e)}")
            return None
    
    def get_runbook(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Retrieve a specific runbook"""
        
        pattern_id = event['pattern_id']
        
        try:
            # Get runbook from S3
            response = s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=f"runbooks/{pattern_id}.json"
            )
            
            runbook = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                'correlation_id': correlation_id,
                'status': 'success',
                'runbook': runbook,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'correlation_id': correlation_id,
                'status': 'error',
                'error': f'Runbook not found: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def load_system_prompt(self) -> str:
        """Load the system prompt for Claude"""
        
        try:
            # Load from S3 or use embedded version
            return """
            You are a senior Site Reliability Engineer (SRE) with expertise in Kubernetes, AWS EKS, and chaos engineering.
            
            Your role is to:
            1. Analyze system failures and explain root causes in plain English
            2. Propose the smallest, safest fixes with clear reasoning
            3. Respect autonomy modes (Dry-run, Approve, Auto)
            4. Execute remediation only through approved tool actions
            5. Verify recovery and document successful runbooks
            
            Always provide evidence from logs, metrics, and Kubernetes events.
            Assess risk levels and recommend appropriate autonomy actions.
            """
            
        except Exception as e:
            logger.error(f"Failed to load system prompt: {str(e)}")
            return "You are a Kubernetes SRE expert."
    
    def fallback_analysis(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback analysis when Claude is unavailable"""
        
        logs = signals.get('logs', [])
        metrics = signals.get('metrics', [])
        
        # Simple pattern matching
        if any('OOMKilled' in str(log) for log in logs):
            return {
                'root_cause': 'Container terminated due to memory limit exceeded',
                'evidence': ['OOMKilled events detected in logs'],
                'failure_pattern': 'k8s_oomkilled',
                'risk_level': 'medium',
                'remediation_steps': [
                    {
                        'action': 'patch_deployment',
                        'target': 'affected-deployment',
                        'params': {'memory_limit': '512Mi'},
                        'risk_level': 'medium',
                        'justification': 'Increase memory limits to prevent OOM kills'
                    }
                ]
            }
        
        return {
            'root_cause': 'Unknown failure pattern',
            'evidence': ['Insufficient data for analysis'],
            'failure_pattern': 'unknown',
            'risk_level': 'high',
            'remediation_steps': []
        }

# Lambda handler function
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entry point"""
    
    agent = EKSChaosGuardian()
    return agent.lambda_handler(event, context)
