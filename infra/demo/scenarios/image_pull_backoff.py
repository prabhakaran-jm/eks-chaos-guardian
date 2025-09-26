"""
EKS Chaos Guardian - ImagePullBackOff Demo Scenario
Demonstrates detection and remediation of image pull failures
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

class ImagePullBackOffScenario:
    """Demo scenario for ImagePullBackOff detection and remediation"""
    
    def __init__(self, cluster_name: str = "eks-chaos-guardian-cluster", 
                 namespace: str = "chaos-test"):
        self.cluster_name = cluster_name
        self.namespace = namespace
        self.correlation_id = f"image-pull-demo-{int(time.time())}"
        
        # AWS clients
        self.lambda_client = boto3.client('lambda')
        self.eks_client = boto3.client('eks')
        
    def run_scenario(self) -> Dict[str, Any]:
        """Run the complete ImagePullBackOff scenario"""
        
        logger.info(f"🚀 Starting ImagePullBackOff scenario - Correlation ID: {self.correlation_id}")
        
        scenario_result = {
            'scenario': 'image_pull_backoff',
            'correlation_id': self.correlation_id,
            'cluster': self.cluster_name,
            'namespace': self.namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'steps': [],
            'status': 'success'
        }
        
        try:
            # Step 1: Deploy app with invalid image
            step1 = self.deploy_app_with_invalid_image()
            scenario_result['steps'].append(step1)
            
            if step1['status'] != 'success':
                raise Exception(f"Failed to deploy app with invalid image: {step1.get('error')}")
            
            # Step 2: Wait for ImagePullBackOff to occur
            logger.info("⏳ Waiting for ImagePullBackOff condition...")
            time.sleep(20)
            
            # Step 3: Detect ImagePullBackOff failures
            step3 = self.detect_image_pull_failures()
            scenario_result['steps'].append(step3)
            
            if step3['status'] != 'success':
                raise Exception(f"Failed to detect image pull failures: {step3.get('error')}")
            
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
            
            logger.info("✅ ImagePullBackOff scenario completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ ImagePullBackOff scenario failed: {str(e)}")
            scenario_result['status'] = 'failed'
            scenario_result['error'] = str(e)
        
        return scenario_result
    
    def deploy_app_with_invalid_image(self) -> Dict[str, Any]:
        """Deploy an application with an invalid image reference"""
        
        logger.info("📦 Deploying application with invalid image reference...")
        
        # This would typically use kubectl or Kubernetes API
        # For demo purposes, we'll simulate the deployment
        
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'image-pull-test-app',
                'namespace': self.namespace,
                'labels': {
                    'app': 'image-pull-test',
                    'scenario': 'image-pull-backoff'
                }
            },
            'spec': {
                'replicas': 2,
                'selector': {
                    'matchLabels': {
                        'app': 'image-pull-test'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'image-pull-test'
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': 'main-container',
                                'image': 'invalid-registry.com/nonexistent-image:latest',  # Invalid image
                                'resources': {
                                    'requests': {
                                        'memory': '128Mi',
                                        'cpu': '100m'
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        # Simulate deployment
        time.sleep(5)
        
        return {
            'step': 'deploy_app_with_invalid_image',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'deployment': 'image-pull-test-app',
                'namespace': self.namespace,
                'invalid_image': 'invalid-registry.com/nonexistent-image:latest',
                'replicas': 2,
                'deployment_status': 'deployed_with_image_pull_errors'
            }
        }
    
    def detect_image_pull_failures(self) -> Dict[str, Any]:
        """Detect ImagePullBackOff failures using CloudWatch Logs"""
        
        logger.info("🔍 Detecting ImagePullBackOff failures...")
        
        # Simulate calling the CloudWatch Logs detection Lambda
        detection_event = {
            'correlation_id': self.correlation_id,
            'log_groups': [f'/aws/eks/{self.cluster_name}/application'],
            'query': '''
                fields @timestamp, @message, kubernetes.pod_name
                | filter @message like /ImagePullBackOff/ or @message like /ErrImagePull/
                | sort @timestamp desc
            ''',
            'start_time': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z',
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'limit': 50
        }
        
        # Simulate detection results
        detection_result = {
            'step': 'detect_image_pull_failures',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'failures_detected': True,
                'failure_type': 'image_pull_backoff',
                'affected_pods': [
                    'image-pull-test-app-7d4f8c9b6-abc123',
                    'image-pull-test-app-7d4f8c9b6-def456'
                ],
                'log_entries': [
                    {
                        'timestamp': datetime.utcnow().isoformat(),
                        'pod': 'image-pull-test-app-7d4f8c9b6-abc123',
                        'message': 'Failed to pull image "invalid-registry.com/nonexistent-image:latest": rpc error: code = Unknown desc = Error response from daemon: pull access denied'
                    }
                ],
                'detection_method': 'cloudwatch_logs_insights'
            }
        }
        
        return detection_result
    
    def analyze_and_plan(self) -> Dict[str, Any]:
        """Analyze ImagePullBackOff failures and create remediation plan"""
        
        logger.info("🧠 Analyzing ImagePullBackOff failures and creating remediation plan...")
        
        # Simulate Bedrock AgentCore analysis
        analysis_result = {
            'step': 'analyze_and_plan',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'root_cause': 'Invalid image reference or missing image pull secrets',
                'evidence': [
                    'Image "invalid-registry.com/nonexistent-image:latest" not found',
                    'Pull access denied error from container registry',
                    'Multiple pod restarts due to ImagePullBackOff',
                    'No imagePullSecrets configured for private registry'
                ],
                'remediation_plan': {
                    'actions': [
                        {
                            'action': 'patch_deployment',
                            'target': 'image-pull-test-app',
                            'patch': {
                                'spec': {
                                    'template': {
                                        'spec': {
                                            'imagePullSecrets': [
                                                {
                                                    'name': 'registry-secret'
                                                }
                                            ],
                                            'containers': [
                                                {
                                                    'name': 'main-container',
                                                    'image': 'nginx:1.20'  # Use valid public image
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'risk_level': 'medium'
                        },
                        {
                            'action': 'rollout_restart',
                            'target': 'image-pull-test-app',
                            'reason': 'Apply new image and pull secrets',
                            'risk_level': 'low'
                        }
                    ],
                    'autonomy_mode': 'approve',  # Medium risk requires approval
                    'estimated_recovery_time': '1-2 minutes'
                }
            }
        }
        
        return analysis_result
    
    def execute_remediation(self) -> Dict[str, Any]:
        """Execute the remediation plan"""
        
        logger.info("🔧 Executing remediation plan...")
        
        # Simulate approval process
        logger.info("📋 Medium risk action detected - requiring approval...")
        logger.info("✅ Approval granted (simulated)")
        
        # Simulate executing the remediation actions
        remediation_result = {
            'step': 'execute_remediation',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'actions_executed': [
                    {
                        'action': 'patch_deployment',
                        'target': 'image-pull-test-app',
                        'status': 'success',
                        'changes': {
                            'image': 'invalid-registry.com/nonexistent-image:latest -> nginx:1.20',
                            'imagePullSecrets': 'Added registry-secret'
                        }
                    },
                    {
                        'action': 'rollout_restart',
                        'target': 'image-pull-test-app',
                        'status': 'success',
                        'restart_triggered': True
                    }
                ],
                'execution_time': '30 seconds',
                'approval_required': True,
                'approval_granted': True,
                'autonomy_mode': 'approve'
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
                        'check': 'image_pull_status',
                        'status': 'passed',
                        'details': 'Images pulled successfully'
                    },
                    {
                        'check': 'no_image_pull_errors',
                        'status': 'passed',
                        'details': 'No new ImagePullBackOff events detected'
                    },
                    {
                        'check': 'application_health',
                        'status': 'passed',
                        'details': 'Application responding normally'
                    }
                ],
                'verification_time': '1.5 minutes',
                'recovery_time': '2 minutes'
            }
        }
        
        return verification_result
    
    def save_runbook(self) -> Dict[str, Any]:
        """Save the successful remediation as a runbook"""
        
        logger.info("💾 Saving successful remediation as runbook...")
        
        runbook = {
            'runbook_version': '1.0',
            'pattern_id': 'k8s_image_pull_backoff',
            'match': {
                'signals': ['Reason=ImagePullBackOff', 'ErrImagePull'],
                'metrics': [
                    {
                        'name': 'kube_pod_container_status_waiting_reason',
                        'op': '=',
                        'value': 'ImagePullBackOff'
                    }
                ]
            },
            'plan': [
                {
                    'action': 'patch_deployment_image',
                    'params': {
                        'image': 'nginx:1.20',
                        'imagePullSecrets': ['registry-secret']
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
            'risk': 'medium',
            'requires_approval': True,
            'evidence_extractors': ['log_lines', 'k8s_describe', 'image_pull_status']
        }
        
        # Simulate saving to S3/DynamoDB
        save_result = {
            'step': 'save_runbook',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'runbook_saved': True,
                'pattern_id': 'k8s_image_pull_backoff',
                'storage_location': 's3://eks-chaos-guardian-bucket/runbooks/k8s_image_pull_backoff.json',
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
                    'deployment/image-pull-test-app',
                    'namespace/chaos-test'
                ],
                'cleanup_completed': True
            }
        }
        
        return cleanup_result

def main():
    """Main function to run the ImagePullBackOff demo scenario"""
    
    print("🎯 EKS Chaos Guardian - ImagePullBackOff Demo Scenario")
    print("=" * 60)
    
    # Initialize scenario
    scenario = ImagePullBackOffScenario()
    
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
