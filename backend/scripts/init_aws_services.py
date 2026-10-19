"""Initialize all FinShock AWS resources strictly within Free Tier."""

import os
import sys
import boto3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.storage import _load_env_file

_load_env_file()
region = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
bucket_name = os.environ.get("FINSHOCK_S3_BUCKET", "finshock-reports")

print(f"==> Initializing FinShock AWS Services in region: {region}")

# 1. DynamoDB Table
print("\n[1/6] DynamoDB Table: finshock_experiments...")
try:
    dynamodb = boto3.client("dynamodb", region_name=region)
    try:
        dynamodb.describe_table(TableName="finshock_experiments")
        print("    ✓ Table already exists.")
    except dynamodb.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName="finshock_experiments",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}]
        )
        print("    ✓ Table created (PAY_PER_REQUEST / Always Free).")
except Exception as e:
    print(f"    ✗ DynamoDB: {e}")

# 2. S3 Bucket
print(f"\n[2/6] S3 Bucket: {bucket_name}...")
try:
    s3 = boto3.client("s3", region_name=region)
    try:
        s3.head_bucket(Bucket=bucket_name)
        print("    ✓ Bucket already exists.")
    except Exception:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print("    ✓ Bucket created (Free Tier).")
except Exception as e:
    print(f"    ✗ S3: {e}")

# 3. SNS Topic
print("\n[3/6] SNS Topic: finshock-risk-alerts...")
try:
    sns = boto3.client("sns", region_name=region)
    resp = sns.create_topic(Name="finshock-risk-alerts")
    print(f"    ✓ SNS Topic ready: {resp.get('TopicArn')}")
except Exception as e:
    print(f"    ✗ SNS: {e}")

# 4. SQS Queue
print("\n[4/6] SQS Queue: finshock-simulation-queue...")
try:
    sqs = boto3.client("sqs", region_name=region)
    resp = sqs.create_queue(QueueName="finshock-simulation-queue")
    print(f"    ✓ SQS Queue ready: {resp.get('QueueUrl')}")
except Exception as e:
    print(f"    ✗ SQS: {e}")

# 5. SSM Parameter Store
print("\n[5/6] SSM Parameter: /finshock/config/risk_free_rate...")
try:
    ssm = boto3.client("ssm", region_name=region)
    ssm.put_parameter(
        Name="/finshock/config/risk_free_rate",
        Value="0.065",
        Type="String",
        Overwrite=True,
        Description="Global benchmark risk-free interest rate"
    )
    print("    ✓ SSM Parameter ready (Standard / Always Free).")
except Exception as e:
    print(f"    ✗ SSM: {e}")

# 6. CloudWatch Metric & Alarm
print("\n[6/6] CloudWatch Custom Metric & Alarm...")
try:
    cw = boto3.client("cloudwatch", region_name=region)
    cw.put_metric_data(
        Namespace="FinShock/Quant",
        MetricData=[{"MetricName": "SystemHealth", "Value": 1.0, "Unit": "Count"}]
    )
    print("    ✓ CloudWatch Custom Metric successfully emitted.")
except Exception as e:
    print(f"    ✗ CloudWatch: {e}")

print("\n==> Initialization complete.")
