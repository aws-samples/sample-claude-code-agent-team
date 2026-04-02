# AWS Security Guidelines

Service-specific security requirements for all AWS services used by agents. All agents MUST follow these guidelines when creating, configuring, or reviewing AWS resources.

## Data Security Implementation Order

Implement data security controls in phased priority order:

**Phase 1** (blocks task completion):
1. Encryption at rest: `aws <service> describe-<resource> --<id> <value> | jq '.EncryptionConfiguration'` (expect: AWS Key Management Service (AWS KMS) key ARN present)
2. TLS enforcement: For Amazon S3, add a DENY policy to reject non-TLS requests (note: `Principal: "*"` in a DENY statement is an AWS-recommended security pattern to enforce TLS for all callers — this differs from ALLOW policies with wildcards, which grant overly broad permissions): `{"Effect": "Deny", "Principal": "*", "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"], "Resource": ["arn:aws:s3:::<your-bucket>/*", "arn:aws:s3:::<your-bucket>"], "Condition": {"Bool": {"aws:SecureTransport": "false"}}}`, verify with `aws s3api get-bucket-policy`
3. Block Public Access: `aws s3api put-public-access-block --bucket <name> --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true`, verify with `aws s3api get-public-access-block`

**Phase 2** (required for review PASS):
4. Access logging: `aws s3api put-bucket-logging --bucket <name> --bucket-logging-status file://logging.json`, verify with `aws s3api get-bucket-logging`
5. Data classification tags: `aws s3api put-bucket-tagging --bucket <name> --tagging 'TagSet=[{Key=data-classification,Value=confidential}]'`, verify with `aws s3api get-bucket-tagging`

**Phase 3** (production requirement):
6. Versioning: `aws s3api put-bucket-versioning --bucket <name> --versioning-configuration Status=Enabled`, verify with `aws s3api get-bucket-versioning` (expect: Status=Enabled for data-classification=confidential|internal)
7. MFA Delete: `aws s3api put-bucket-versioning --bucket <name> --versioning-configuration Status=Enabled,MFADelete=Enabled --mfa "<device-arn> <code>"`, verify with `aws s3api get-bucket-versioning` (expect: MFADelete=Enabled for data-classification=confidential)
8. BYOK documentation: Create `.claude/specs/<slug>/kms-key-usage.md` documenting key ARNs, rotation schedule, and access policies, flag for security review in `review.md`

## Data Security Verification Checklist

For infrastructure handling sensitive data, verify the following:

1. **Encryption at rest**: `aws <service> describe-<resource> | jq '.EncryptionConfiguration'` (expect: AWS KMS key ARN present)
2. **Encryption in transit**: Verify TLS 1.2+ enforcement via service configuration or bucket policies
3. **Key management**: Verify AWS KMS key usage is documented in `.claude/specs/<slug>/kms-key-usage.md`
4. **Data classification**: `aws <service> get-<resource>-tagging | jq '.TagSet[] | select(.Key=="data-classification")'` (expect: tag present)
5. **Access logging**: `aws <service> get-<resource>-logging` (expect: logging enabled)

## Amazon Simple Storage Service (Amazon S3)

- Encryption at rest using AWS KMS keys — **Critical** if missing
- Encryption in transit via `aws:SecureTransport` bucket policy condition — **Critical** if missing
- Block Public Access (BPA) enabled — **Critical** if missing (unless public access is explicitly documented and justified)
- Bucket policies enforce TLS/HTTPS using `aws:SecureTransport` condition (deny when false) — **Critical** if missing
- Versioning enabled for buckets containing critical data — **Warning** if missing
- MFA Delete configured for buckets with sensitive data — **Warning** if missing
- Access logging enabled to an audit bucket — **Warning** if missing
- Data classification tags present — **Warning** if missing
- BYOK (customer-managed AWS KMS keys) usage documented and flagged for security review — **Warning** if not documented
- Key management strategy documented (key rotation, access policies) — **Warning** if missing

## AWS Lambda

- **Execution role permissions**: Apply least-privilege IAM policies. Each function gets its own execution role — never share roles across functions. Verify with `aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <actions>` (expect: Deny for unused actions)
- **Environment variable encryption**: Use AWS KMS encryption for environment variables containing sensitive data. Verify with `aws lambda get-function-configuration --function-name <name> | jq '.KMSKeyArn'` (expect: AWS KMS key ARN present for functions with sensitive env vars)
- **VPC configuration**: Place functions in an Amazon VPC when accessing private resources (Amazon RDS, ElastiCache, internal APIs). Configure security groups to restrict outbound traffic. Verify with `aws lambda get-function-configuration --function-name <name> | jq '.VpcConfig'`
- **Resource-based policies**: Restrict invoke permissions to specific principals. Verify with `aws lambda get-policy --function-name <name>` (expect: no wildcard principals)
- **Reserved concurrency**: Set reserved concurrency to prevent runaway invocations from exhausting account limits

## Amazon DynamoDB

- **Encryption at rest**: Use AWS KMS keys (not default AWS owned keys) for tables containing sensitive data. Verify with `aws dynamodb describe-table --table-name <name> | jq '.Table.SSEDescription'` (expect: SSEType=KMS with KMSMasterKeyArn)
- **Point-in-time recovery**: Enable PITR for all tables. Verify with `aws dynamodb describe-continuous-backups --table-name <name> | jq '.ContinuousBackupsDescription.PointInTimeRecoveryDescription'` (expect: PointInTimeRecoveryStatus=ENABLED)
- **IAM policies for table access**: Use fine-grained IAM conditions (`dynamodb:LeadingKeys`, `dynamodb:Attributes`) to restrict row and attribute-level access. Never grant `dynamodb:*` on production tables
- **Data classification tags**: Apply data classification tags. Verify with `aws dynamodb list-tags-of-resource --resource-arn <arn> | jq '.Tags[] | select(.Key=="data-classification")'`
- **Encryption in transit**: Use HTTPS endpoints only (default for AWS SDK, but verify custom clients)

## Amazon Relational Database Service (Amazon RDS)

- **Encryption at rest**: Enable at creation with AWS KMS keys (cannot be enabled after creation). Verify with `aws rds describe-db-instances --db-instance-identifier <name> | jq '.DBInstances[0].StorageEncrypted, .DBInstances[0].KmsKeyId'` (expect: true with KMS key ARN)
- **Encryption in transit**: Enforce SSL/TLS connections via parameter groups (`rds.force_ssl=1` for PostgreSQL, `require_secure_transport=ON` for MySQL). Verify with `aws rds describe-db-parameters --db-parameter-group-name <name> | jq '.Parameters[] | select(.ParameterName=="rds.force_ssl")'`
- **Authentication**: Use IAM database authentication where supported. For password auth, store credentials in AWS Secrets Manager with automatic rotation. Verify with `aws rds describe-db-instances --db-instance-identifier <name> | jq '.DBInstances[0].IAMDatabaseAuthenticationEnabled'`
- **Network isolation**: Place in private subnets with no public accessibility. Verify with `aws rds describe-db-instances --db-instance-identifier <name> | jq '.DBInstances[0].PubliclyAccessible'` (expect: false)
- **Automated backups**: Enable with appropriate retention period. Verify with `aws rds describe-db-instances --db-instance-identifier <name> | jq '.DBInstances[0].BackupRetentionPeriod'` (expect: >= 7)
- **Data classification tags**: Apply tags. Verify with `aws rds list-tags-for-resource --resource-name <arn> | jq '.TagList[] | select(.Key=="data-classification")'`

## Amazon Elastic Block Store (Amazon EBS)

- **Encryption at rest**: Enable default encryption in the account or per-volume with AWS KMS keys. Verify with `aws ec2 describe-volumes --volume-ids <id> | jq '.Volumes[0].Encrypted, .Volumes[0].KmsKeyId'` (expect: true with KMS key ARN)
- **Snapshots**: Encrypt all snapshots. Verify with `aws ec2 describe-snapshots --snapshot-ids <id> | jq '.Snapshots[0].Encrypted'`
- **Data classification tags**: Apply tags. Verify with `aws ec2 describe-volumes --volume-ids <id> | jq '.Volumes[0].Tags[] | select(.Key=="data-classification")'`

## Amazon API Gateway

- **Authorization**: Configure appropriate authorizers (IAM, Cognito, Lambda) for all routes — **Critical** if missing (no open/unauthenticated endpoints unless explicitly documented)
- **Throttling**: Set rate limiting and burst limits on all stages and methods. Verify with `aws apigateway get-method-response` or `aws apigatewayv2 get-stage`
- **WAF integration**: Attach AWS WAF web ACL for public-facing APIs — **Warning** if missing
- **Mutual TLS**: Enable mTLS for API-to-API communication when handling sensitive data — **Warning** if missing
- **Access logging**: Enable access logging to CloudWatch Logs or Kinesis Data Firehose. Verify with `aws apigateway get-stage --rest-api-id <id> --stage-name <stage> | jq '.accessLogSettings'` (expect: destination ARN present) — **Warning** if missing
- **Resource policies**: Restrict API access by source IP or VPC endpoint for private APIs. Verify with `aws apigateway get-rest-api --rest-api-id <id> | jq '.policy'`
- **Request validation**: Enable request validators for body, query string, and path parameters — **Warning** if missing

## Aurora DSQL

- **IAM authentication**: Use IAM database authentication — never store database passwords. Generate auth tokens via `aws dsql generate-db-connect-auth-token`. Verify IAM policies grant `dsql:DbConnectAdmin` only to required principals — **Critical** if password-based auth is used
- **Encryption at rest**: Aurora DSQL encrypts data at rest by default using AWS-managed keys. For sensitive data, verify encryption configuration
- **Encryption in transit**: All DSQL connections use TLS by default. Verify application connection strings use `sslmode=verify-full` — **Critical** if TLS is disabled
- **Network isolation**: Use VPC endpoints for DSQL access from within VPCs. Verify with `aws ec2 describe-vpc-endpoints --filters Name=service-name,Values=dsql` — **Warning** if accessing over public internet from VPC workloads
- **Fine-grained access**: Use PostgreSQL GRANT/REVOKE for table and column-level access control. Never grant `superuser` to application roles
- **Multi-tenant isolation**: For multi-tenant schemas, enforce row-level security (RLS) policies. Verify with `readonly_query` tool: `SELECT * FROM pg_policies` (expect: RLS policies present for tenant tables)
- **Audit logging**: Enable query logging for compliance. Verify audit trail configuration

## AWS Amplify Gen 2

- **Authentication**: Use Amplify Auth (backed by Amazon Cognito) — configure MFA, password policies, and account recovery. Verify Cognito user pool settings — **Critical** if auth is unenforced on protected routes
- **Authorization rules**: Define per-model authorization rules in Amplify data schema (`@auth` directives). Verify owner-based and group-based access — **Critical** if models are publicly readable/writable without explicit justification
- **API keys**: Never expose Amplify API keys in client-side code for production. Use IAM or Cognito-based auth for production APIs
- **Storage**: Configure S3 storage access levels (guest, authenticated, owner) appropriately. Verify bucket policies — **Warning** if overly permissive
- **Environment separation**: Use separate Amplify sandbox and production environments. Never deploy dev configurations to production

## General Requirements

- All secrets via AWS Secrets Manager or Parameter Store, a capability of AWS Systems Manager — do not inline in code or IaC
- Tag all resources: service, environment, owner, cost-center, data-classification
- Document key management strategy in `design.md` including rotation policies
- Apply data classification tags (`data-classification: public|internal|confidential`) to all resources handling data
- Enable access logging for data operations: CloudTrail, S3 access logs, database audit logs
