"""Lightweight, 100% Free-Tier AWS Lambda & API Gateway HTTP API v2 deployer.

Uses boto3 (no Docker or heavy SAM CLI required).
Provisions:
1. Lambda Execution Role (with least-privilege policies for FinShock)
2. AWS Lambda Function ('FinShockFunction', Python 3.11, 256MB)
3. Amazon API Gateway HTTP API v2 ('FinShockHttpApi')
4. API Gateway Lambda Integration & Permissions
"""

import os
import sys
import io
import zipfile
import json
import time
import boto3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.storage import _load_env_file

_load_env_file()
region = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
account_id = boto3.client("sts").get_caller_identity()["Account"]
role_name = "FinShockLambdaRole"
function_name = "FinShockFunction"
api_name = "FinShockHttpApi"

print(f"==> Deploying FinShock Compute & Routing to AWS [{region} / Account: {account_id}]")

# 1. Lambda IAM Execution Role
iam = boto3.client("iam", region_name=region)
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role_arn = None
try:
    role_resp = iam.get_role(RoleName=role_name)
    role_arn = role_resp["Role"]["Arn"]
    print(f"    ✓ Found existing IAM execution role: {role_arn}")
except Exception:
    try:
        print(f"    Creating IAM execution role: {role_name}...")
        role_resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for FinShock quantitative Lambda function"
        )
        role_arn = role_resp["Role"]["Arn"]
        
        # Attach basic execution
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        # Attach permissions policy for FinShock resources
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "finshock-iam-policy.json")) as f:
            finshock_policy = f.read()
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="FinShockResourceAccess",
            PolicyDocument=finshock_policy
        )
        print("    ✓ IAM execution role created and configured.")
        # Wait a few seconds for IAM propagation
        time.sleep(8)
    except Exception as e:
        print(f"\n[!] IAM Role Setup Error: {e}")
        print("\nACTION NEEDED: Your 'Finshock' IAM user needs 'iam:CreateRole' permissions to create Lambda's execution role.")
        print("Please update your user policy in the AWS Console using 'finshock-iam-policy.json' and re-run.")
        sys.exit(1)

# 2. Package Backend Code into Zip
print("\n[2/4] Packaging backend code...")
zip_buffer = io.BytesIO()
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(os.path.join(backend_root, "backend")):
        if "__pycache__" in root or ".pytest_cache" in root:
            continue
        for file in files:
            if file.endswith((".pyc", ".pyo")):
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, backend_root)
            zf.write(abs_path, rel_path)

zip_bytes = zip_buffer.getvalue()
print(f"    ✓ Packaged {len(zip_bytes) / 1024:.1f} KB deployment zip.")

# 3. Create or Update Lambda Function
print(f"\n[3/4] Deploying Lambda Function: {function_name}...")
lam = boto3.client("lambda", region_name=region)
# Public AWS SDK Pandas layer includes numpy for Python 3.11 in ap-south-1
numpy_layer = f"arn:aws:lambda:{region}:336392948345:layer:AWSSDKPandas-Python311:12"

function_arn = None
try:
    func_info = lam.get_function(FunctionName=function_name)
    function_arn = func_info["Configuration"]["FunctionArn"]
    print("    Updating function code...")
    lam.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
    lam.update_function_configuration(
        FunctionName=function_name,
        Handler="backend.handler.lambda_handler",
        Runtime="python3.11",
        Timeout=15,
        MemorySize=256,
        Environment={
            "Variables": {
                "FINSHOCK_DYNAMODB_TABLE": os.environ.get("FINSHOCK_DYNAMODB_TABLE", "finshock_experiments"),
                "FINSHOCK_S3_BUCKET": os.environ.get("FINSHOCK_S3_BUCKET", "finshock-reports"),
                "FINSHOCK_SSM_PARAM_NAME": "/finshock/config/risk_free_rate",
                "FINSHOCK_SNS_TOPIC": "finshock-risk-alerts",
                "FINSHOCK_SQS_QUEUE": "finshock-simulation-queue"
            }
        }
    )
    print("    ✓ Function code and configuration updated.")
except lam.exceptions.ResourceNotFoundException:
    print("    Creating function...")
    retries = 3
    while retries > 0:
        try:
            res = lam.create_function(
                FunctionName=function_name,
                Runtime="python3.11",
                Role=role_arn,
                Handler="backend.handler.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Timeout=15,
                MemorySize=256,
                Layers=[numpy_layer],
                Environment={
                    "Variables": {
                        "FINSHOCK_DYNAMODB_TABLE": os.environ.get("FINSHOCK_DYNAMODB_TABLE", "finshock_experiments"),
                        "FINSHOCK_S3_BUCKET": os.environ.get("FINSHOCK_S3_BUCKET", "finshock-reports"),
                        "FINSHOCK_SSM_PARAM_NAME": "/finshock/config/risk_free_rate",
                        "FINSHOCK_SNS_TOPIC": "finshock-risk-alerts",
                        "FINSHOCK_SQS_QUEUE": "finshock-simulation-queue"
                    }
                }
            )
            function_arn = res["FunctionArn"]
            print(f"    ✓ Lambda created: {function_arn}")
            break
        except lam.exceptions.InvalidParameterValueException as e:
            if "The role defined for the function cannot be assumed" in str(e):
                print("    Waiting for IAM role propagation...")
                time.sleep(5)
                retries -= 1
            else:
                raise e

# 4. Amazon API Gateway (HTTP API v2)
print(f"\n[4/4] Configuring Amazon API Gateway HTTP API v2: {api_name}...")
apigw = boto3.client("apigatewayv2", region_name=region)

# Check existing API
apis = apigw.get_apis().get("Items", [])
existing_api = next((a for a in apis if a.get("Name") == api_name), None)

if existing_api:
    api_id = existing_api["ApiId"]
    api_endpoint = existing_api["ApiEndpoint"]
    print(f"    ✓ Using existing HTTP API: {api_id}")
else:
    api_res = apigw.create_api(
        Name=api_name,
        ProtocolType="HTTP",
        CorsConfiguration={
            "AllowOrigins": ["*"],
            "AllowMethods": ["GET", "POST", "OPTIONS"],
            "AllowHeaders": ["Content-Type", "Authorization"]
        }
    )
    api_id = api_res["ApiId"]
    api_endpoint = api_res["ApiEndpoint"]
    print(f"    ✓ Created HTTP API v2: {api_id}")

# Create Lambda Integration
integrations = apigw.get_integrations(ApiId=api_id).get("Items", [])
integration_id = integrations[0]["IntegrationId"] if integrations else None

if not integration_id:
    int_res = apigw.create_integration(
        ApiId=api_id,
        IntegrationType="AWS_PROXY",
        IntegrationUri=function_arn,
        PayloadFormatVersion="2.0"
    )
    integration_id = int_res["IntegrationId"]
    print(f"    ✓ Lambda Integration created: {integration_id}")

# Create Default Catch-all Route: $default -> Integration
routes = apigw.get_routes(ApiId=api_id).get("Items", [])
default_route = next((r for r in routes if r.get("RouteKey") == "$default"), None)
if not default_route:
    apigw.create_route(
        ApiId=api_id,
        RouteKey="$default",
        Target=f"integrations/{integration_id}"
    )
    print("    ✓ Catch-all route ($default) created.")

# Create Auto-deploy Stage: $default
stages = apigw.get_stages(ApiId=api_id).get("Items", [])
default_stage = next((s for s in stages if s.get("StageName") == "$default"), None)
if not default_stage:
    apigw.create_stage(
        ApiId=api_id,
        StageName="$default",
        AutoDeploy=True
    )
    print("    ✓ $default stage auto-deploy configured.")

# Grant API Gateway permission to invoke Lambda
try:
    lam.add_permission(
        FunctionName=function_name,
        StatementId="FinShockApiGatewayInvoke",
        Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*"
    )
    print("    ✓ Granted API Gateway invoke permission on Lambda.")
except lam.exceptions.ResourceConflictException:
    pass

print(f"\n🎉 Compute & Routing Deployment Complete!")
print(f"🌐 Public API Gateway Endpoint: {api_endpoint}/api/health")
print(f"   (Test with: curl {api_endpoint}/api/health)")
