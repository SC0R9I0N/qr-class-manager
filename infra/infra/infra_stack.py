from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_s3 as s3,
)
from constructs import Construct

class QrClassManagerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for attendance
        attendance_table = ddb.Table(
            self, "AttendanceTable",
            partition_key={"name": "sessionId", "type": ddb.AttributeType.STRING},
            sort_key={"name": "studentId", "type": ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )

        # S3 bucket for resource uploads
        resource_bucket = s3.Bucket(
            self, "ResourceBucket",
            versioned=True,
            removal_policy=Stack.of(self).removal_policy.DESTROY,
            auto_delete_objects=True
        )

        # Lambda: log_attendance
        log_attendance_lambda = _lambda.Function(
            self, "LogAttendanceLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="log_attendance.handler",
            code=_lambda.Code.from_asset("../lambdas"),
            environment={
                "TABLE_NAME": attendance_table.table_name,
                "BUCKET_NAME": resource_bucket.bucket_name
            }
        )

        # Lambda: upload_resource
        upload_resource_lambda = _lambda.Function(
            self, "UploadResourceLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="upload_resource.handler",
            code=_lambda.Code.from_asset("../lambdas"),
            environment={
                "BUCKET_NAME": resource_bucket.bucket_name
            }
        )

        # Lambda: get_stats
        get_stats_lambda = _lambda.Function(
            self, "GetStatsLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="get_stats.handler",
            code=_lambda.Code.from_asset("../lambdas"),
            environment={
                "TABLE_NAME": attendance_table.table_name
            }
        )

        # Lambda: get_resource
        get_resource_lambda = _lambda.Function(
            self, "GetResourceLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="get_resource.handler",
            code=_lambda.Code.from_asset("../lambdas"),
            environment={
                "BUCKET_NAME": resource_bucket.bucket_name
            }
        )

        # Grant permissions
        attendance_table.grant_read_write_data(log_attendance_lambda)
        attendance_table.grant_read_data(get_stats_lambda)
        resource_bucket.grant_read_write(log_attendance_lambda)
        resource_bucket.grant_read_write(upload_resource_lambda)
        resource_bucket.grant_read(get_resource_lambda)

        # API Gateway
        api = apigw.RestApi(self, "ClassBitsApi", rest_api_name="ClassBits Service")

        # POST /attendance
        attendance = api.root.add_resource("attendance")
        attendance.add_method("POST", apigw.LambdaIntegration(log_attendance_lambda))

        # POST /resource
        resource = api.root.add_resource("resource")
        resource.add_method("POST", apigw.LambdaIntegration(upload_resource_lambda))

        # GET /stats
        stats = api.root.add_resource("stats")
        stats.add_method("GET", apigw.LambdaIntegration(get_stats_lambda))

        # GET /resource/{id}
        resource_id = resource.add_resource("{id}")
        resource_id.add_method("GET", apigw.LambdaIntegration(get_resource_lambda))