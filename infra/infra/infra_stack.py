from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_s3 as s3,
)
from constructs import Construct

class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table
        attendance_table = ddb.Table(
            self, "AttendanceTable",
            partition_key={"name": "sessionId", "type": ddb.AttributeType.STRING},
            sort_key={"name": "studentId", "type": ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )

        # S3 bucket
        resource_bucket = s3.Bucket(
            self, "ResourceBucket",
            versioned=True,
            removal_policy=Stack.of(self).removal_policy.DESTROY,
            auto_delete_objects=True
        )

        # Lambda stub
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

        attendance_table.grant_read_write_data(log_attendance_lambda)
        resource_bucket.grant_read_write(log_attendance_lambda)

        # API Gateway
        api = apigw.RestApi(self, "ClassBitsApi", rest_api_name="ClassBits Service")
        attendance = api.root.add_resource("attendance")
        attendance.add_method("POST", apigw.LambdaIntegration(log_attendance_lambda))