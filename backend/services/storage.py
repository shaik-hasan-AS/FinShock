"""Storage adapter supporting both Local JSON storage and AWS DynamoDB / S3.

Automatically detects AWS credentials. When AWS keys are provided, it persists to
DynamoDB and S3; otherwise, it persists to a local JSON file store.
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "local_experiments")
DYNAMODB_TABLE_NAME = os.environ.get("FINSHOCK_DYNAMODB_TABLE", "finshock_experiments")
S3_BUCKET_NAME = os.environ.get("FINSHOCK_S3_BUCKET", "finshock-reports")


def _load_env_file():
    """Load variables from .env if present in project root."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v

_load_env_file()


def has_aws_credentials() -> bool:
    """Check if AWS credentials are set in environment."""
    _load_env_file()
    return bool(
        os.environ.get("AWS_ACCESS_KEY_ID") and
        os.environ.get("AWS_SECRET_ACCESS_KEY")
    )


def get_aws_status() -> Dict[str, Any]:
    """Return status of AWS connection and configuration."""
    has_creds = has_aws_credentials()
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "ap-south-1"))
    return {
        "aws_connected": has_creds,
        "region": region,
        "dynamodb_table": DYNAMODB_TABLE_NAME,
        "s3_bucket": S3_BUCKET_NAME,
        "mode": "aws_cloud" if has_creds else "local_fallback",
        "message": (
            f"Connected to AWS Region '{region}'. DynamoDB and S3 enabled."
            if has_creds
            else "Running in Local Fallback mode. AWS keys not set yet; all experiments are saved locally."
        )
    }


def save_experiment(experiment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a scenario/simulation experiment run."""
    exp_id = experiment_data.get("id") or str(uuid.uuid4())[:8]
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    record = {
        "id": exp_id,
        "created_at": created_at,
        "title": experiment_data.get("title", f"Experiment {exp_id}"),
        "capital": experiment_data.get("capital", 1_000_000.0),
        "weights": experiment_data.get("weights", {}),
        "scenario_id": experiment_data.get("scenario_id"),
        "metrics": experiment_data.get("metrics", {}),
        "shock_result": experiment_data.get("shock_result", {}),
        "notes": experiment_data.get("notes", ""),
    }

    if has_aws_credentials():
        try:
            import boto3
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(DYNAMODB_TABLE_NAME)
            # DynamoDB requires float conversion to Decimal or string; convert via JSON roundtrip
            table.put_item(Item=json.loads(json.dumps(record), parse_float=str))
            record["saved_to"] = "DynamoDB"
            return record
        except Exception as e:
            record["aws_error"] = str(e)
            record["saved_to"] = "Local (DynamoDB attempt failed)"
    
    # Local fallback
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    file_path = os.path.join(LOCAL_STORAGE_DIR, f"{exp_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    record["saved_to"] = "Local JSON"
    return record


def _clean_decimals(obj: Any) -> Any:
    """Recursively convert boto3 Decimal objects to int or float."""
    from decimal import Decimal
    if isinstance(obj, list):
        return [_clean_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _clean_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def list_experiments() -> List[Dict[str, Any]]:
    """List saved experiments."""
    if has_aws_credentials():
        try:
            import boto3
            dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-south-1"))
            table = dynamodb.Table(DYNAMODB_TABLE_NAME)
            resp = table.scan(Limit=50)
            items = resp.get("Items", [])
            cleaned = _clean_decimals(items)
            return sorted(cleaned, key=lambda x: x.get("created_at", ""), reverse=True)
        except Exception:
            pass

    # Read from local storage
    if not os.path.exists(LOCAL_STORAGE_DIR):
        return []
    
    experiments = []
    for fname in os.listdir(LOCAL_STORAGE_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(LOCAL_STORAGE_DIR, fname), "r", encoding="utf-8") as f:
                    experiments.append(json.load(f))
            except Exception:
                continue
    return sorted(experiments, key=lambda x: x.get("created_at", ""), reverse=True)
