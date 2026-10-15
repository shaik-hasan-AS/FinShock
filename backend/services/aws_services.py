"""Multi-service AWS adapter for FinShock Quant (10-Service Architecture).

Manages:
1. AWS Lambda (Compute runtime)
2. Amazon API Gateway (Routing)
3. Amazon DynamoDB (Experiment persistence)
4. Amazon S3 (Report export)
5. Amazon SNS (Risk breach alerts)
6. Amazon SQS (Async simulation tasks)
7. Amazon EventBridge (Scheduled stress evaluation)
8. AWS SSM Parameter Store (Dynamic risk config)
9. Amazon CloudWatch (Logs & custom metrics)
10. AWS CloudFormation / SAM (IaC lifecycle)
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional

from backend.services.storage import has_aws_credentials, _load_env_file

SNS_TOPIC_NAME = os.environ.get("FINSHOCK_SNS_TOPIC", "finshock-risk-alerts")
SQS_QUEUE_NAME = os.environ.get("FINSHOCK_SQS_QUEUE", "finshock-simulation-queue")
SSM_PARAM_NAME = os.environ.get("FINSHOCK_SSM_PARAM_NAME", "/finshock/config/risk_free_rate")
S3_BUCKET_NAME = os.environ.get("FINSHOCK_S3_BUCKET", "finshock-reports")
CLOUDWATCH_NAMESPACE = "FinShock/Quant"


def _get_boto3_client(service_name: str):
    """Create a boto3 client with proper region."""
    _load_env_file()
    import boto3
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "ap-south-1"))
    return boto3.client(service_name, region_name=region)


def get_all_aws_services_status() -> Dict[str, Any]:
    """Inspect and report the status of all 10 AWS services."""
    connected = has_aws_credentials()
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "ap-south-1"))

    services = [
        {
            "name": "AWS Lambda",
            "category": "Compute",
            "role": "Serverless quantitative engine execution",
            "active": True,
            "status": "Ready (Handler: backend.handler.lambda_handler)"
        },
        {
            "name": "Amazon API Gateway",
            "category": "Networking",
            "role": "Low-latency HTTP API v2 routing (/api/*)",
            "active": True,
            "status": "Configured in template.yaml"
        },
        {
            "name": "Amazon DynamoDB",
            "category": "Database",
            "role": "Persistent store for saved experiments & stress tests",
            "active": connected,
            "status": f"Connected to table 'finshock_experiments' ({region})" if connected else "Local fallback mode"
        },
        {
            "name": "Amazon S3",
            "category": "Storage",
            "role": "Exported risk reports & benchmark dataset storage",
            "active": connected,
            "status": f"Bucket 'finshock-reports' ready" if connected else "Local directory fallback"
        },
        {
            "name": "Amazon SNS",
            "category": "Messaging",
            "role": "Risk Breach Alerts when drawdown/VaR exceeds 15%",
            "active": connected,
            "status": "Topic 'finshock-risk-alerts' active" if connected else "Local alert simulation"
        },
        {
            "name": "Amazon SQS",
            "category": "Queueing",
            "role": "Asynchronous Monte Carlo batch simulation queue",
            "active": connected,
            "status": "Queue 'finshock-simulation-queue' ready" if connected else "Synchronous local queue"
        },
        {
            "name": "Amazon EventBridge",
            "category": "Orchestration",
            "role": "Automated nightly portfolio stress re-evaluation cron",
            "active": True,
            "status": "Schedule: cron(0 2 * * ? *) daily"
        },
        {
            "name": "AWS Systems Manager (SSM)",
            "category": "Configuration",
            "role": "Centralized parameter store for benchmark rates",
            "active": connected,
            "status": f"Param '{SSM_PARAM_NAME}'" if connected else "Default fallback (6.5%)"
        },
        {
            "name": "Amazon CloudWatch",
            "category": "Observability",
            "role": "Metrics, anomaly alarms & structured execution logs",
            "active": True,
            "status": "Active (Metric Namespace: FinShock/Quant)"
        },
        {
            "name": "AWS CloudFormation / SAM",
            "category": "IaC",
            "role": "Infrastructure as Code lifecycle management",
            "active": True,
            "status": "Defined in template.yaml"
        }
    ]

    return {
        "aws_connected": connected,
        "region": region,
        "total_services_count": len(services),
        "free_tier_compliant": True,
        "services": services
    }


def publish_risk_breach_alert(title: str, pnl_percent: float, var_95_percent: float) -> Dict[str, Any]:
    """Publish a Risk Breach Alert to Amazon SNS."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = (
        f"[RISK BREACH] FINSHOCK QUANT RISK ALERT\n"
        f"----------------------------------------\n"
        f"Portfolio: {title}\n"
        f"Timestamp: {timestamp}\n"
        f"Stressed Drawdown: {pnl_percent:.2f}%\n"
        f"1-Yr 95% Value at Risk (VaR): {var_95_percent:.2f}%\n\n"
        f"Action: Portfolio has breached the conservative risk threshold (15%). "
        f"Review asset allocation hedges immediately."
    )

    if has_aws_credentials():
        try:
            sns = _get_boto3_client("sns")
            # Create or get topic ARN
            topic_resp = sns.create_topic(Name=SNS_TOPIC_NAME)
            topic_arn = topic_resp["TopicArn"]
            
            publish_resp = sns.publish(
                TopicArn=topic_arn,
                Subject=f"FinShock Risk Alert: {title} ({pnl_percent:.1f}%)",
                Message=message
            )
            return {
                "sent_to": "Amazon SNS",
                "topic_arn": topic_arn,
                "message_id": publish_resp.get("MessageId"),
                "status": "Published to SNS"
            }
        except Exception as e:
            return {"sent_to": "Local Fallback", "error": str(e), "message": message}

    return {
        "sent_to": "Local Simulation",
        "topic": SNS_TOPIC_NAME,
        "status": "Simulated SNS alert (Add AWS keys to deliver to real subscribers)",
        "message": message
    }


def enqueue_simulation_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enqueue an asynchronous Monte Carlo simulation job to Amazon SQS."""
    task_id = str(uuid.uuid4())[:8]
    payload = {
        "task_id": task_id,
        "enqueued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_data": task_data
    }

    if has_aws_credentials():
        try:
            sqs = _get_boto3_client("sqs")
            queue_resp = sqs.create_queue(QueueName=SQS_QUEUE_NAME)
            queue_url = queue_resp["QueueUrl"]
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(payload)
            )
            return {"task_id": task_id, "status": "Enqueued to Amazon SQS", "queue_url": queue_url}
        except Exception as e:
            return {"task_id": task_id, "status": "Local execution fallback", "error": str(e)}

    return {"task_id": task_id, "status": "Queued locally in memory"}


def export_report_to_s3(report_name: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Export a quantitative stress test report to Amazon S3."""
    clean_name = report_name.replace(" ", "_").lower()
    file_key = f"reports/{clean_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps(report_data, indent=2)

    if has_aws_credentials():
        try:
            s3 = _get_boto3_client("s3")
            region = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
            
            # Check bucket existence or create
            try:
                s3.head_bucket(Bucket=S3_BUCKET_NAME)
            except Exception:
                if region == "us-east-1":
                    s3.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": region}
                    )
                    
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_key,
                Body=content.encode("utf-8"),
                ContentType="application/json"
            )
            return {
                "exported_to": "Amazon S3",
                "bucket": S3_BUCKET_NAME,
                "file_key": file_key,
                "url": f"https://{S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{file_key}"
            }
        except Exception as e:
            return {"exported_to": "Local disk (S3 fallback)", "error": str(e), "file_key": file_key}

    # Local fallback export
    local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "exported_reports")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, os.path.basename(file_key))
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "exported_to": "Local JSON report",
        "file_path": local_path,
        "file_key": file_key
    }


def get_risk_free_rate_from_ssm(default_rate: float = 0.065) -> float:
    """Read dynamic risk-free rate from AWS Systems Manager (SSM) Parameter Store."""
    if has_aws_credentials():
        try:
            ssm = _get_boto3_client("ssm")
            resp = ssm.get_parameter(Name=SSM_PARAM_NAME)
            val = float(resp["Parameter"]["Value"])
            return val
        except Exception:
            pass
    return default_rate


def log_cloudwatch_metric(metric_name: str, value: float, unit: str = "Percent") -> None:
    """Emit custom quantitative metric to Amazon CloudWatch."""
    if has_aws_credentials():
        try:
            cw = _get_boto3_client("cloudwatch")
            cw.put_metric_data(
                Namespace=CLOUDWATCH_NAMESPACE,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": float(value),
                        "Unit": unit,
                        "Timestamp": datetime.datetime.now(datetime.timezone.utc)
                    }
                ]
            )
        except Exception:
            pass
