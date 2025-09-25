# EKS Chaos Guardian - EKS Autopilot Configuration
# Simplified cluster management with cost optimization

resource "aws_eks_cluster" "chaos_guardian_autopilot" {
  name     = "${local.name}-autopilot"
  role_arn = aws_iam_role.autopilot_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = module.vpc.private_subnets
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  # Enable EKS Add-ons for better integration
  depends_on = [
    aws_iam_role_policy_attachment.autopilot_cluster_AmazonEKSClusterPolicy,
    aws_cloudwatch_log_group.autopilot,
  ]

  tags = local.tags
}

# EKS Add-ons for Autopilot
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.chaos_guardian_autopilot.name
  addon_name   = "vpc-cni"
  
  tags = local.tags
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.chaos_guardian_autopilot.name
  addon_name   = "coredns"
  
  tags = local.tags
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.chaos_guardian_autopilot.name
  addon_name   = "kube-proxy"
  
  tags = local.tags
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name = aws_eks_cluster.chaos_guardian_autopilot.name
  addon_name   = "aws-ebs-csi-driver"
  
  tags = local.tags
}

# IAM Role for Autopilot Cluster
resource "aws_iam_role" "autopilot_cluster" {
  name = "${local.name}-autopilot-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "autopilot_cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.autopilot_cluster.name
}

# CloudWatch Log Group for Autopilot
resource "aws_cloudwatch_log_group" "autopilot" {
  name              = "/aws/eks/${local.name}-autopilot/cluster"
  retention_in_days = 3

  tags = local.tags
}

# Autopilot Node Pool (Optional - for specific workloads)
resource "aws_eks_node_pool" "chaos_demo" {
  cluster_name    = aws_eks_cluster.chaos_guardian_autopilot.name
  node_pool_name  = "chaos-demo"
  node_role_arn   = aws_iam_role.autopilot_node_pool.arn
  subnet_ids      = module.vpc.private_subnets

  scaling_config {
    min_size     = 1
    max_size     = 3
    desired_size = 2
  }

  instance_types = ["t3.medium"]

  update_config {
    max_unavailable_percentage = 25
  }

  # Taints for specific workloads
  taint {
    key    = "chaos-demo"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  depends_on = [
    aws_eks_addon.vpc_cni,
    aws_eks_addon.coredns,
    aws_eks_addon.kube_proxy,
  ]

  tags = local.tags
}

# IAM Role for Autopilot Node Pool
resource "aws_iam_role" "autopilot_node_pool" {
  name = "${local.name}-autopilot-node-pool-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "autopilot_node_pool_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.autopilot_node_pool.name
}

resource "aws_iam_role_policy_attachment" "autopilot_node_pool_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.autopilot_node_pool.name
}

resource "aws_iam_role_policy_attachment" "autopilot_node_pool_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.autopilot_node_pool.name
}

# Outputs for Autopilot
output "autopilot_cluster_id" {
  description = "EKS Autopilot cluster ID"
  value       = aws_eks_cluster.chaos_guardian_autopilot.id
}

output "autopilot_cluster_endpoint" {
  description = "EKS Autopilot cluster endpoint"
  value       = aws_eks_cluster.chaos_guardian_autopilot.endpoint
}

output "autopilot_kubectl_config" {
  description = "Kubectl configuration command for Autopilot"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.chaos_guardian_autopilot.name}"
}
