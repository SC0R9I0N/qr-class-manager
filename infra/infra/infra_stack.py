from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_sns as sns,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion
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
            ("session_student-index", "session_id", "student_id"),
            ("class_id-index", "class_id")
        ]:
            attendance_table.add_global_secondary_index(
                index_name=index[0],
                partition_key={"name": index[1], "type": ddb.AttributeType.STRING},
                sort_key={"name": index[2], "type": ddb.AttributeType.STRING} if len(index) == 3 else None
            )

        # S3 Bucket for QR codes
        qr_bucket = s3.Bucket(
            self,
            "QrCodeBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

        qr_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{qr_bucket.bucket_arn}/qrcodes/*"],
                principals=[iam.AnyPrincipal()]
            )
        )

        qr_distribution = cloudfront.Distribution(
            self,
            "QrCodeDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(qr_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            )
        )

        lecture_materials_bucket = s3.Bucket(
            self, "LectureMaterialsBucket",
            versioned=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # SNS Topic for attendance notifications
        attendance_topic = sns.Topic(self, "AttendanceTopic")

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "ClassBitsUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes={
                "email": cognito.StandardAttribute(required=True, mutable=False)
            },
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False
            )
        )

        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "ClassBitsAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Cognito App Client
        user_pool_client = user_pool.add_client(
            "ClassBitsAppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )

        # Cognito Groups
        cognito.CfnUserPoolGroup(self, "ProfessorsGroup",
                                 user_pool_id=user_pool.user_pool_id,
                                 group_name="professors"
                                 )

        cognito.CfnUserPoolGroup(self, "StudentsGroup",
                                 user_pool_id=user_pool.user_pool_id,
                                 group_name="students"
                                 )

        # Shared environment variables
        env_vars = {
            "CLASSES_TABLE": classes_table.table_name,
            "SESSIONS_TABLE": sessions_table.table_name,
            "ATTENDANCE_TABLE": attendance_table.table_name,
            "QR_CODE_BUCKET": qr_bucket.bucket_name,
            "CLOUDFRONT_DOMAIN": qr_distribution.domain_name,
            "LECTURE_MATERIALS_BUCKET": lecture_materials_bucket.bucket_name,
            "USER_POOL_ID": user_pool.user_pool_id,
            "COGNITO_CLIENT_ID": user_pool_client.user_pool_client_id,
            "ATTENDANCE_TOPIC_ARN": attendance_topic.topic_arn,
            # "AWS_REGION": self.region
        }

        # Shared Lambda Layer (Uses PythonLayerVersion to bundle dependencies from requirements.txt)
        shared_layer = PythonLayerVersion(
            self, "SharedLayer",
            entry="../lambdas/shared",  # Directory containing your shared code AND requirements.txt
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Shared utilities for all Lambdas"
        )

        # Helper to create Lambdas
        def create_lambda(id: str, path: str):
            fn = _lambda.Function(
                self, id,
                runtime=_lambda.Runtime.PYTHON_3_11,
                handler="lambda_function.lambda_handler",
                code=_lambda.Code.from_asset(path),
                environment=env_vars,
                layers=[shared_layer]
            )
            return fn

        # Create Lambdas
        lambdas ={}

        lambdas["manage_sessions"] = PythonFunction(
            self, "ManageSessionsLambda",
            entry="../lambdas/manage-sessions",  # CDK will look for lambda_function.py and requirements.txt here
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["upload_lecture_materials"] = PythonFunction(
            self, "UploadLectureMaterialsLambda",
            entry="../lambdas/upload-lecture-materials",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["get_lecture_materials"] = PythonFunction(
            self, "GetLectureMaterialsLambda",
            entry="../lambdas/get-lecture-materials",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["generate_qr"] = PythonFunction(
            self, "GenerateQrLambda",
            entry="../lambdas/generate-qr",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["scan_attendance"] = PythonFunction(
            self, "ScanAttendanceLambda",
            entry="../lambdas/scan-attendance",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["get_attendance"] = PythonFunction(
            self, "GetAttendanceLambda",
            entry="../lambdas/get-attendance",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        lambdas["get_analytics"] = PythonFunction(
            self, "GetAnalyticsLambda",
            entry="../lambdas/get-analytics",
            runtime=_lambda.Runtime.PYTHON_3_11,
            index="lambda_function.py",
            handler="lambda_handler",
            environment=env_vars,
            layers=[shared_layer]
        )

        # Grant permissions
        for fn in lambdas.values():
            classes_table.grant_read_write_data(fn)
            sessions_table.grant_read_write_data(fn)
            attendance_table.grant_read_write_data(fn)
            qr_bucket.grant_read_write(fn)
            attendance_topic.grant_publish(fn)

        # Grant S3 access for lecture materials
        lecture_materials_bucket.grant_read_write(lambdas["upload_lecture_materials"])
        lecture_materials_bucket.grant_read(lambdas["get_lecture_materials"])

        # API Gateway
        api = apigw.RestApi(self, "ClassBitsApi", rest_api_name="ClassBits Service")

        def add_cors_options(resource: apigw.Resource):
            resource.add_method(
                "OPTIONS",
                apigw.MockIntegration(
                    integration_responses=[{
                        "statusCode": "200",
                        "responseParameters": {
                            "method.response.header.Access-Control-Allow-Headers": "'Authorization,Content-Type'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'"
                        }
                    }],
                    passthrough_behavior=apigw.PassthroughBehavior.NEVER,
                    request_templates={"application/json": '{"statusCode": 200}'}
                ),
                method_responses=[{
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True
                    }
                }]
            )

        # Routes
        sessions = api.root.add_resource("sessions")
        add_cors_options(sessions)
        session_id = sessions.add_resource("{session_id}")
        add_cors_options(session_id)
        qr_code = session_id.add_resource("qr-code")
        add_cors_options(qr_code)
        qr_code.add_method(
            "POST",
            apigw.LambdaIntegration(lambdas["generate_qr"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        sessions.add_method(
            "GET",
            apigw.LambdaIntegration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        sessions.add_method(
            "POST",
            apigw.LambdaIntegration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        sessions.add_method(
            "PUT",
            apigw.LambdaIntegration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        sessions.add_method(
            "DELETE",
            apigw.LambdaIntegration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        attendance = api.root.add_resource("attendance")
        add_cors_options(attendance)
        attendance.add_method(
            "GET",
            apigw.LambdaIntegration(lambdas["get_attendance"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        scan = attendance.add_resource("scan")
        add_cors_options(scan)
        scan.add_method(
            "POST",
            apigw.LambdaIntegration(
                lambdas["scan_attendance"]
            ),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        analytics = api.root.add_resource("analytics")
        add_cors_options(analytics)
        analytics.add_method(
            "GET",
            apigw.LambdaIntegration(lambdas["get_analytics"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        materials = api.root.add_resource("materials")
        add_cors_options(materials)

        materials.add_method(
            "POST",
            apigw.LambdaIntegration(lambdas["upload_lecture_materials"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        materials.add_method(
            "GET",
            apigw.LambdaIntegration(lambdas["get_lecture_materials"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer
        )