# Terraform AWS path

This module provisions the artifact and task-definition layer for Gatehouse: immutable ECR repositories with scan-on-push, lifecycle retention, ECS Fargate task definitions, an execution role, and CloudWatch log groups.

Networking, PostgreSQL, and load balancer modules are intentionally kept as environment-owned dependencies. Pass an existing execution role with `execution_role_arn` when your organization manages IAM centrally.

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -var='environment=staging'
```

Never place database passwords or API keys in `*.tfvars`; wire them through AWS Secrets Manager or SSM in the environment module.
