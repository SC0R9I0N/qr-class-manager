from aws_cdk import (
    Stack,
    Duration,
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


# UTILITY FUNCTION: Guaranteed Integration Response with CORS
def create_cors_integration_response():
    # Defines the response from the Integration (Lambda) to the Method (API Gateway)
    # This explicitly maps the necessary CORS headers and ensures the Lambda body is passed through.
    return [
        apigw.IntegrationResponse(
            status_code="200",
            response_parameters={
                # Hardcoded values for universal CORS success
                "method.response.header.Access-Control-Allow-Origin": "'*'",
                "method.response.header.Access-Control-Allow-Headers":
                    "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods":
                    "'OPTIONS,GET,PUT,POST,DELETE'",
            },
            # Map the response body from the Lambda output
            response_templates={
                "application/json": "$input.json('$')"
            }
        )
    ]


# UTILITY FUNCTION: Guaranteed Method Response for CORS headers
# Defines the parameters required on the API Gateway Method Response
cors_method_response = {
    "statusCode": "200",
    "responseParameters": {
        # Must be set to True to instruct API Gateway to include them in the response
        "method.response.header.Access-Control-Allow-Origin": True,
        "method.response.header.Access-Control-Allow-Headers": True,
        "method.response.header.Access-Control-Allow-Methods": True,
    }
}


# UTILITY FUNCTION: Lambda Integration Helper
def create_lambda_integration(lambda_fn):
    # Combines the Lambda function with the explicit CORS Integration Responses
    return apigw.LambdaIntegration(
        handler=lambda_fn,
        integration_responses=create_cors_integration_response()
    )


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
        lambdas = {}

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
            layers=[shared_layer],
            # Boost memory and timeout for Base64/ZIP processing
            memory_size=512,
            timeout=Duration.seconds(30)
        )

        lambdas["upload_lecture_materials"].add_to_role_policy(
            iam.PolicyStatement(
                actions=["cognito-idp:AdminGetUser", "cognito-idp:AdminListGroupsForUser"],
                resources=[user_pool.user_pool_arn]
            )
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

        lambdas["get_attendance"].add_to_role_policy(
            iam.PolicyStatement(
                actions=["cognito-idp:AdminGetUser"],
                resources=[user_pool.user_pool_arn]
            )
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
        lecture_materials_bucket.grant_read(lambdas["scan_attendance"])

        # ------------------------------------------------------------
        # FRONTEND HOSTING: S3 Bucket + CloudFront Distribution
        # ------------------------------------------------------------

        # 1. Bucket to hold the built React files (dist folder)
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            website_index_document="index.html",
            website_error_document="index.html",  # Critical for React Router deep links
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # 2. Distribution to serve the frontend over HTTPS
        frontend_distribution = cloudfront.Distribution(
            self, "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(frontend_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            )
        )

        # Output the URL so you can retrieve the CloudFront link after deployment
        self.frontend_url = frontend_distribution.distribution_domain_name

        # API Gateway
        api = apigw.RestApi(
            self, "ClassBitsApi",
            rest_api_name="ClassBits Service",
            # 1. KEEP THE GLOBAL CORS SETTING for the OPTIONS preflight method
            default_cors_preflight_options={
                "allow_origins": apigw.Cors.ALL_ORIGINS,
                "allow_methods": apigw.Cors.ALL_METHODS,
                "allow_headers": ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"],
            }
        )

        # 2. APPLY FIX TO ALL METHOD INTEGRATIONS

        # Routes
        sessions = api.root.add_resource("sessions")

        session_id = sessions.add_resource("{session_id}")

        qr_code = session_id.add_resource("generate-qr")

        qr_code.add_method(
            "POST",
            create_lambda_integration(lambdas["generate_qr"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        session_id.add_method(
            "GET",
            create_lambda_integration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        sessions.add_method(
            "GET",
            create_lambda_integration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )
        sessions.add_method(
            "POST",
            create_lambda_integration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )
        sessions.add_method(
            "PUT",
            create_lambda_integration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )
        sessions.add_method(
            "DELETE",
            create_lambda_integration(lambdas["manage_sessions"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        attendance = api.root.add_resource("attendance")

        attendance.add_method(
            "GET",
            create_lambda_integration(lambdas["get_attendance"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )
        scan = attendance.add_resource("scan")

        scan.add_method(
            "POST",
            create_lambda_integration(
                lambdas["scan_attendance"]
            ),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        analytics = api.root.add_resource("analytics")

        analytics.add_method(
            "GET",
            create_lambda_integration(lambdas["get_analytics"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        materials = api.root.add_resource("materials")

        materials.add_method(
            "POST",
            create_lambda_integration(lambdas["upload_lecture_materials"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )

        materials.add_method(
            "GET",
            create_lambda_integration(lambdas["get_lecture_materials"]),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[cors_method_response]
        )