"""
EKS Chaos Guardian - OOMKilled Demo Scenario
Demonstrates detection and remediation of Out of Memory (OOM) killed pods
"""

import json
import boto3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OOMKilledScenario:
    """Demo scenario for OOMKilled pod detection and remediation"""
    
    def __init__(self, cluster_name: str = "eks-chaos-guardian-cluster", 
                 namespace: str = "chaos-test"):
        self.cluster_name = cluster_name
        self.namespace = namespace
        self.correlation_id = f"oom-demo-{int(time.time())}"
        
        # AWS clients
        self.lambda_client = boto3.client('lambda')
        self.eks_client = boto3.client('eks')
        
    def run_scenario(self) -> Dict[str, Any]:
        """Run the complete OOMKilled scenario"""
        
        logger.info(f"🚀 Starting OOMKilled scenario - Correlation ID: {self.correlation_id}")
        
        scenario_result = {
            'scenario': 'oomkilled',
            'correlation_id': self.correlation_id,
            'cluster': self.cluster_name,
            'namespace': self.namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'steps': [],
            'status': 'success'
        }
        
        try:
            # Step 1: Deploy vulnerable application
            step1 = self.deploy_vulnerable_app()
            scenario_result['steps'].append(step1)
            
            if step1['status'] != 'success':
                raise Exception(f"Failed to deploy vulnerable app: {step1.get('error')}")
            
            # Step 2: Wait for OOM to occur
            logger.info("⏳ Waiting for OOM condition to develop...")
            time.sleep(30)
            
            # Step 3: Detect OOM failures
            step3 = self.detect_oom_failures()
            scenario_result['steps'].append(step3)
            
            if step3['status'] != 'success':
                raise Exception(f"Failed to detect OOM failures: {step3.get('error')}")
            
            # Step 4: Analyze and plan remediation
            step4 = self.analyze_and_plan()
            scenario_result['steps'].append(step4)
            
            if step4['status'] != 'success':
                raise Exception(f"Failed to analyze and plan: {step4.get('error')}")
            
            # Step 5: Execute remediation
            step5 = self.execute_remediation()
            scenario_result['steps'].append(step5)
            
            if step5['status'] != 'success':
                raise Exception(f"Failed to execute remediation: {step5.get('error')}")
            
            # Step 6: Verify recovery
            step6 = self.verify_recovery()
            scenario_result['steps'].append(step6)
            
            if step6['status'] != 'success':
                raise Exception(f"Failed to verify recovery: {step6.get('error')}")
            
            # Step 7: Save runbook
            step7 = self.save_runbook()
            scenario_result['steps'].append(step7)
            
            logger.info("✅ OOMKilled scenario completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ OOMKilled scenario failed: {str(e)}")
            scenario_result['status'] = 'failed'
            scenario_result['error'] = str(e)
        
        return scenario_result
    
    def deploy_vulnerable_app(self) -> Dict[str, Any]:
        """Deploy an application with low memory limits that will cause OOM"""
        
        logger.info("📦 Deploying vulnerable application with low memory limits...")
        
        # This would typically use kubectl or Kubernetes API
        # For demo purposes, we'll simulate the deployment
        
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'oom-vulnerable-app',
                'namespace': self.namespace,
                'labels': {
                    'app': 'oom-vulnerable',
                    'scenario': 'oomkilled'
                }
            },
            'spec': {
                'replicas': 2,
                'selector': {
                    'matchLabels': {
                        'app': 'oom-vulnerable'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'oom-vulnerable'
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': 'memory-hog',
                                'image': 'nginx:1.20',
                                'resources': {
                                    'requests': {
                                        'memory': '64Mi'
                                    },
                                    'limits': {
                                        'memory': '128Mi'  # Very low limit to trigger OOM
                                    }
                                },
                                'command': ['/bin/sh'],
                                'args': [
                                    '-c',
                                    'while true; do echo "Allocating memory..."; dd if=/dev/zero of=/tmp/memory bs=1M count=200; sleep 30; rm /tmp/memory; done'
                                ]
                            }
                        ]
                    }
                }
            }
        }
        
        # Simulate deployment
        time.sleep(5)
        
        return {
            'step': 'deploy_vulnerable_app',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'deployment': 'oom-vulnerable-app',
                'namespace': self.namespace,
                'memory_limit': '128Mi',
                'replicas': 2,
                'deployment_status': 'deployed'
            }
        }
    
    def detect_oom_failures(self) -> Dict[str, Any]:
        """Detect OOM failures using CloudWatch Logs"""
        
        logger.info("🔍 Detecting OOM failures...")
        
        # Simulate calling the CloudWatch Logs detection Lambda
        detection_event = {
            'correlation_id': self.correlation_id,
            'log_groups': [f'/aws/eks/{self.cluster_name}/application'],
            'query': '''
                fields @timestamp, @message, kubernetes.pod_name, kubernetes.container_name
                | filter @message like /OOMKilled/ or @message like /OutOfMemory/
                | sort @timestamp desc
            ''',
            'start_time': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z',
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'limit': 50
        }
        
        # Simulate detection results
        detection_result = {
            'step': 'detect_oom_failures',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'failures_detected': True,
                'failure_type': 'oom_killed',
                'affected_pods': [
                    'oom-vulnerable-app-7d4f8c9b6-abc123',
                    'oom-vulnerable-app-7d4f8c9b6-def456'
                ],
                'log_entries': [
                    {
                        'timestamp': datetime.utcnow().isoformat(),
                        'pod': 'oom-vulnerable-app-7d4f8c9b6-abc123',
                        'message': 'Container memory limit exceeded, killing container (OOMKilled)'
                    }
                ],
                'detection_method': 'cloudwatch_logs_insights'
            }
        }
        
        return detection_result
    
    def analyze_and_plan(self) -> Dict[str, Any]:
        """Analyze OOM failures and create remediation plan"""
        
        logger.info("🧠 Analyzing OOM failures and creating remediation plan...")
        
        # Simulate Bedrock AgentCore analysis
        analysis_result = {
            'step': 'analyze_and_plan',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'root_cause': 'Insufficient memory limits for application workload',
                'evidence': [
                    'Container memory limit set to 128Mi',
                    'Application attempting to allocate 200Mi',
                    'Multiple pod restarts due to OOMKilled',
                    'Memory usage spikes during application startup'
                ],
                'remediation_plan': {
                    'actions': [
                        {
                            'action': 'patch_deployment',
                            'target': 'oom-vulnerable-app',
                            'patch': {
                                'spec': {
                                    'template': {
                                        'spec': {
                                            'containers': [
                                                {
                                                    'name': 'memory-hog',
                                                    'resources': {
                                                        'limits': {
                                                            'memory': '512Mi'  # Increase memory limit
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'risk_level': 'low'
                        },
                        {
                            'action': 'rollout_restart',
                            'target': 'oom-vulnerable-app',
                            'reason': 'Apply new memory limits',
                            'risk_level': 'low'
                        }
                    ],
                    'autonomy_mode': 'auto',  # Low risk actions can be auto-executed
                    'estimated_recovery_time': '2-3 minutes'
                }
            }
        }
        
        return analysis_result
    
    def execute_remediation(self) -> Dict[str, Any]:
        """Execute the remediation plan"""
        
        logger.info("🔧 Executing remediation plan...")
        
        # Simulate executing the remediation actions
        remediation_result = {
            'step': 'execute_remediation',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'actions_executed': [
                    {
                        'action': 'patch_deployment',
                        'target': 'oom-vulnerable-app',
                        'status': 'success',
                        'changes': {
                            'memory_limit': '128Mi -> 512Mi'
                        }
                    },
                    {
                        'action': 'rollout_restart',
                        'target': 'oom-vulnerable-app',
                        'status': 'success',
                        'restart_triggered': True
                    }
                ],
                'execution_time': '45 seconds',
                'approval_required': False,
                'autonomy_mode': 'auto'
            }
        }
        
        # Simulate rollout time
        time.sleep(10)
        
        return remediation_result
    
    def verify_recovery(self) -> Dict[str, Any]:
        """Verify that the remediation was successful"""
        
        logger.info("✅ Verifying recovery...")
        
        # Simulate verification checks
        verification_result = {
            'step': 'verify_recovery',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'recovery_verified': True,
                'checks_performed': [
                    {
                        'check': 'pod_status',
                        'status': 'passed',
                        'details': 'All pods running and ready'
                    },
                    {
                        'check': 'memory_usage',
                        'status': 'passed',
                        'details': 'Memory usage within limits'
                    },
                    {
                        'check': 'no_oom_events',
                        'status': 'passed',
                        'details': 'No new OOMKilled events detected'
                    },
                    {
                        'check': 'application_health',
                        'status': 'passed',
                        'details': 'Application responding normally'
                    }
                ],
                'verification_time': '2 minutes',
                'recovery_time': '2.5 minutes'
            }
        }
        
        return verification_result
    
    def save_runbook(self) -> Dict[str, Any]:
        """Save the successful remediation as a runbook"""
        
        logger.info("💾 Saving successful remediation as runbook...")
        
        runbook = {
            'runbook_version': '1.0',
            'pattern_id': 'k8s_oomkilled',
            'match': {
                'signals': ['Reason=OOMKilled', 'container_terminated'],
                'metrics': [
                    {
                        'name': 'container_memory_working_set_bytes',
                        'op': '>',
                        'value': 'limit'
                    }
                ]
            },
            'plan': [
                {
                    'action': 'patch_deployment_resources',
                    'params': {
                        'memory_limit': '512Mi'
                    }
                },
                {
                    'action': 'rollout_restart',
                    'params': {}
                },
                {
                    'action': 'postcheck_pod_stable',
                    'params': {
                        'minutes': 2
                    }
                }
            ],
            'risk': 'low',
            'requires_approval': False,
            'evidence_extractors': ['log_lines', 'k8s_describe', 'cw_metric_window']
        }
        
        # Simulate saving to S3/DynamoDB
        save_result = {
            'step': 'save_runbook',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'runbook_saved': True,
                'pattern_id': 'k8s_oomkilled',
                'storage_location': 's3://eks-chaos-guardian-bucket/runbooks/k8s_oomkilled.json',
                'dynamodb_index': 'runbook-index'
            }
        }
        
        return save_result
    
    def cleanup(self) -> Dict[str, Any]:
        """Clean up the demo resources"""
        
        logger.info("🧹 Cleaning up demo resources...")
        
        # Simulate cleanup
        cleanup_result = {
            'step': 'cleanup',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'resources_cleaned': [
                    'deployment/oom-vulnerable-app',
                    'namespace/chaos-test'
                ],
                'cleanup_completed': True
            }
        }
        
        return cleanup_result

def main():
    """Main function to run the OOMKilled demo scenario"""
    
    print("🎯 EKS Chaos Guardian - OOMKilled Demo Scenario")
    print("=" * 60)
    
    # Initialize scenario
    scenario = OOMKilledScenario()
    
    try:
        # Run the scenario
        result = scenario.run_scenario()
        
        # Print results
        print(f"\n📊 Scenario Results:")
        print(f"Status: {result['status']}")
        print(f"Correlation ID: {result['correlation_id']}")
        
        if result['status'] == 'success':
            print("\n✅ All steps completed successfully!")
            for step in result['steps']:
                print(f"  ✓ {step['step']}: {step['status']}")
        else:
            print(f"\n❌ Scenario failed: {result.get('error', 'Unknown error')}")
        
        # Ask if user wants to cleanup
        cleanup_choice = input("\n🧹 Clean up demo resources? (y/n): ").lower().strip()
        if cleanup_choice == 'y':
            cleanup_result = scenario.cleanup()
            print(f"Cleanup: {cleanup_result['status']}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")

if __name__ == "__main__":
    main()
