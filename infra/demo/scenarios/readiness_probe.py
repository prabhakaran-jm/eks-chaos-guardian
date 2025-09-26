"""
EKS Chaos Guardian - Readiness Probe Demo Scenario
Demonstrates detection and remediation of readiness probe failures
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

class ReadinessProbeScenario:
    """Demo scenario for readiness probe failure detection and remediation"""
    
    def __init__(self, cluster_name: str = "eks-chaos-guardian-cluster", 
                 namespace: str = "chaos-test"):
        self.cluster_name = cluster_name
        self.namespace = namespace
        self.correlation_id = f"readiness-demo-{int(time.time())}"
        
        # AWS clients
        self.lambda_client = boto3.client('lambda')
        self.eks_client = boto3.client('eks')
        
    def run_scenario(self) -> Dict[str, Any]:
        """Run the complete readiness probe scenario"""
        
        logger.info(f"🚀 Starting Readiness Probe scenario - Correlation ID: {self.correlation_id}")
        
        scenario_result = {
            'scenario': 'readiness_probe',
            'correlation_id': self.correlation_id,
            'cluster': self.cluster_name,
            'namespace': self.namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'steps': [],
            'status': 'success'
        }
        
        try:
            # Step 1: Deploy app with misconfigured readiness probe
            step1 = self.deploy_app_with_bad_probe()
            scenario_result['steps'].append(step1)
            
            if step1['status'] != 'success':
                raise Exception(f"Failed to deploy app with bad probe: {step1.get('error')}")
            
            # Step 2: Wait for readiness probe failures
            logger.info("⏳ Waiting for readiness probe failures...")
            time.sleep(25)
            
            # Step 3: Detect readiness probe failures
            step3 = self.detect_readiness_failures()
            scenario_result['steps'].append(step3)
            
            if step3['status'] != 'success':
                raise Exception(f"Failed to detect readiness failures: {step3.get('error')}")
            
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
            
            logger.info("✅ Readiness Probe scenario completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Readiness Probe scenario failed: {str(e)}")
            scenario_result['status'] = 'failed'
            scenario_result['error'] = str(e)
        
        return scenario_result
    
    def deploy_app_with_bad_probe(self) -> Dict[str, Any]:
        """Deploy an application with a misconfigured readiness probe"""
        
        logger.info("📦 Deploying application with misconfigured readiness probe...")
        
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'readiness-test-app',
                'namespace': self.namespace,
                'labels': {
                    'app': 'readiness-test',
                    'scenario': 'readiness-probe'
                }
            },
            'spec': {
                'replicas': 2,
                'selector': {
                    'matchLabels': {
                        'app': 'readiness-test'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'readiness-test'
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': 'web-server',
                                'image': 'nginx:1.20',
                                'ports': [
                                    {
                                        'containerPort': 80,
                                        'protocol': 'TCP'
                                    }
                                ],
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/health',  # Wrong path - doesn't exist
                                        'port': 80
                                    },
                                    'initialDelaySeconds': 5,
                                    'periodSeconds': 10,
                                    'timeoutSeconds': 5,
                                    'failureThreshold': 3
                                },
                                'livenessProbe': {
                                    'httpGet': {
                                        'path': '/',
                                        'port': 80
                                    },
                                    'initialDelaySeconds': 30,
                                    'periodSeconds': 10
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
            'step': 'deploy_app_with_bad_probe',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'deployment': 'readiness-test-app',
                'namespace': self.namespace,
                'readiness_probe_path': '/health',  # This path doesn't exist
                'replicas': 2,
                'deployment_status': 'deployed_with_readiness_issues'
            }
        }
    
    def detect_readiness_failures(self) -> Dict[str, Any]:
        """Detect readiness probe failures using CloudWatch Logs"""
        
        logger.info("🔍 Detecting readiness probe failures...")
        
        # Simulate calling the CloudWatch Logs detection Lambda
        detection_event = {
            'correlation_id': self.correlation_id,
            'log_groups': [f'/aws/eks/{self.cluster_name}/application'],
            'query': '''
                fields @timestamp, @message, kubernetes.pod_name
                | filter @message like /Readiness probe failed/ or @message like /Liveness probe failed/
                | sort @timestamp desc
            ''',
            'start_time': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z',
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'limit': 50
        }
        
        # Simulate detection results
        detection_result = {
            'step': 'detect_readiness_failures',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'failures_detected': True,
                'failure_type': 'readiness_probe_failure',
                'affected_pods': [
                    'readiness-test-app-7d4f8c9b6-abc123',
                    'readiness-test-app-7d4f8c9b6-def456'
                ],
                'log_entries': [
                    {
                        'timestamp': datetime.utcnow().isoformat(),
                        'pod': 'readiness-test-app-7d4f8c9b6-abc123',
                        'message': 'Readiness probe failed: HTTP probe failed with statuscode: 404'
                    }
                ],
                'detection_method': 'cloudwatch_logs_insights'
            }
        }
        
        return detection_result
    
    def analyze_and_plan(self) -> Dict[str, Any]:
        """Analyze readiness probe failures and create remediation plan"""
        
        logger.info("🧠 Analyzing readiness probe failures and creating remediation plan...")
        
        # Simulate Bedrock AgentCore analysis
        analysis_result = {
            'step': 'analyze_and_plan',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'root_cause': 'Readiness probe configured with incorrect path',
                'evidence': [
                    'Readiness probe failing with HTTP 404 status',
                    'Probe path "/health" does not exist on nginx',
                    'Default nginx serves content on "/" path',
                    'Pods not becoming ready due to failed probes'
                ],
                'remediation_plan': {
                    'actions': [
                        {
                            'action': 'patch_deployment',
                            'target': 'readiness-test-app',
                            'patch': {
                                'spec': {
                                    'template': {
                                        'spec': {
                                            'containers': [
                                                {
                                                    'name': 'web-server',
                                                    'readinessProbe': {
                                                        'httpGet': {
                                                            'path': '/',  # Fix: use correct path
                                                            'port': 80
                                                        },
                                                        'initialDelaySeconds': 5,
                                                        'periodSeconds': 10,
                                                        'timeoutSeconds': 5,
                                                        'failureThreshold': 3
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
                            'target': 'readiness-test-app',
                            'reason': 'Apply corrected readiness probe configuration',
                            'risk_level': 'low'
                        }
                    ],
                    'autonomy_mode': 'auto',  # Low risk actions can be auto-executed
                    'estimated_recovery_time': '1-2 minutes'
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
                        'target': 'readiness-test-app',
                        'status': 'success',
                        'changes': {
                            'readiness_probe_path': '/health -> /'
                        }
                    },
                    {
                        'action': 'rollout_restart',
                        'target': 'readiness-test-app',
                        'status': 'success',
                        'restart_triggered': True
                    }
                ],
                'execution_time': '25 seconds',
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
                        'check': 'readiness_probe',
                        'status': 'passed',
                        'details': 'Readiness probes passing successfully'
                    },
                    {
                        'check': 'no_probe_failures',
                        'status': 'passed',
                        'details': 'No new readiness probe failures detected'
                    },
                    {
                        'check': 'service_endpoints',
                        'status': 'passed',
                        'details': 'Service endpoints healthy and accessible'
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
            'pattern_id': 'k8s_readiness_probe_failure',
            'match': {
                'signals': ['Reason=Readiness probe failed', 'HTTP 404'],
                'metrics': [
                    {
                        'name': 'kube_pod_status_phase',
                        'op': '=',
                        'value': 'NotReady'
                    }
                ]
            },
            'plan': [
                {
                    'action': 'patch_readiness_probe',
                    'params': {
                        'path': '/',
                        'port': 80,
                        'initial_delay': 5
                    }
                },
                {
                    'action': 'rollout_restart',
                    'params': {}
                },
                {
                    'action': 'postcheck_pod_ready',
                    'params': {
                        'minutes': 2
                    }
                }
            ],
            'risk': 'low',
            'requires_approval': False,
            'evidence_extractors': ['log_lines', 'k8s_describe', 'probe_status']
        }
        
        # Simulate saving to S3/DynamoDB
        save_result = {
            'step': 'save_runbook',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'runbook_saved': True,
                'pattern_id': 'k8s_readiness_probe_failure',
                'storage_location': 's3://eks-chaos-guardian-bucket/runbooks/k8s_readiness_probe_failure.json',
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
                    'deployment/readiness-test-app',
                    'namespace/chaos-test'
                ],
                'cleanup_completed': True
            }
        }
        
        return cleanup_result

def main():
    """Main function to run the Readiness Probe demo scenario"""
    
    print("🎯 EKS Chaos Guardian - Readiness Probe Demo Scenario")
    print("=" * 60)
    
    # Initialize scenario
    scenario = ReadinessProbeScenario()
    
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
