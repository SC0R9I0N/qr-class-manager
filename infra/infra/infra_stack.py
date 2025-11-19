from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_sns as sns,
    RemovalPolicy,
)
from constructs import Construct

class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Tables
        classes_table = ddb.Table(
            self, "ClassesTable",
            partition_key={"name": "class_id", "type": ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )
        classes_table.add_global_secondary_index(
            index_name="professor_id-index",
            partition_key={"name": "professor_id", "type": ddb.AttributeType.STRING}
        )

        sessions_table = ddb.Table(
            self, "SessionsTable",
            partition_key={"name": "session_id", "type": ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )
        sessions_table.add_global_secondary_index(
            index_name="class_id-index",
            partition_key={"name": "class_id", "type": ddb.AttributeType.STRING}
        )

        attendance_table = ddb.Table(
            self, "AttendanceTable",
            partition_key={"name": "attendance_id", "type": ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )
        for index in [
            ("session_id-index", "session_id"),
            ("student_id-index", "student_id"),
            ("student_class-index", "student_id", "class_id"),
            ("session_student-index", "session_id", "student_id")
        ]:
            attendance_table.add_global_secondary_index(
                index_name=index[0],
                partition_key={"name": index[1], "type": ddb.AttributeType.STRING},
                sort_key={"name": index[2], "type": ddb.AttributeType.STRING} if len(index) == 3 else None
            )

        # S3 Bucket for QR codes
        qr_bucket = s3.Bucket(
            self, "QrCodeBucket",
            versioned=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # SNS Topic for attendance notifications
        attendance_topic = sns.Topic(self, "AttendanceTopic")

        # Shared environment variables
        env_vars = {
            "CLASSES_TABLE": classes_table.table_name,
            "SESSIONS_TABLE": sessions_table.table_name,
            "ATTENDANCE_TABLE": attendance_table.table_name,
            "QR_CODE_BUCKET": qr_bucket.bucket_name,
            "USER_POOL_ID": "your-user-pool-id",
            "COGNITO_CLIENT_ID": "your-client-id",
            "ATTENDANCE_TOPIC_ARN": attendance_topic.topic_arn,
            # "AWS_REGION": self.region
        }

        # Shared Lambda Layer
        shared_layer = _lambda.LayerVersion(
            self, "SharedLayer",
            code=_lambda.Code.from_asset("../lambdas/shared"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Shared utilities for all Lambdas"
        )

        # Helper to create Lambdas
        def create_lambda(id: str, path: str):
            fn = _lambda.Function(
                self, id,
                runtime=_lambda.Runtime.PYTHON_3_11,
                handler="lambda_function.handler",
                code=_lambda.Code.from_asset(path),
                environment=env_vars,
                layers=[shared_layer]
            )
            return fn

        # Create Lambdas
        lambdas = {
            "generate_qr": create_lambda("GenerateQrLambda", "../lambdas/generate-qr"),
            "scan_attendance": create_lambda("ScanAttendanceLambda", "../lambdas/scan-attendance"),
            "get_attendance": create_lambda("GetAttendanceLambda", "../lambdas/get-attendance"),
            "get_analytics": create_lambda("GetAnalyticsLambda", "../lambdas/get-analytics"),
            "manage_sessions": create_lambda("ManageSessionsLambda", "../lambdas/manage-sessions")
        }

        # Grant permissions
        for fn in lambdas.values():
            classes_table.grant_read_write_data(fn)
            sessions_table.grant_read_write_data(fn)
            attendance_table.grant_read_write_data(fn)
            qr_bucket.grant_read_write(fn)
            attendance_topic.grant_publish(fn)

        # API Gateway
        api = apigw.RestApi(self, "ClassBitsApi", rest_api_name="ClassBits Service")

        # Routes
        sessions = api.root.add_resource("sessions")
        session_id = sessions.add_resource("{session_id}")
        qr_code = session_id.add_resource("qr-code")
        qr_code.add_method("POST", apigw.LambdaIntegration(lambdas["generate_qr"]))

        sessions.add_method("GET", apigw.LambdaIntegration(lambdas["manage_sessions"]))
        sessions.add_method("POST", apigw.LambdaIntegration(lambdas["manage_sessions"]))
        sessions.add_method("PUT", apigw.LambdaIntegration(lambdas["manage_sessions"]))
        sessions.add_method("DELETE", apigw.LambdaIntegration(lambdas["manage_sessions"]))

        attendance = api.root.add_resource("attendance")
        attendance.add_method("GET", apigw.LambdaIntegration(lambdas["get_attendance"]))
        scan = attendance.add_resource("scan")
        scan.add_method("POST", apigw.LambdaIntegration(lambdas["scan_attendance"]))

        analytics = api.root.add_resource("analytics")
        analytics.add_method("GET", apigw.LambdaIntegration(lambdas["get_analytics"]))