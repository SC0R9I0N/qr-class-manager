import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Example: Attendance table
    const attendanceTable = new dynamodb.Table(this, 'AttendanceTable', {
      partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'studentId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Example: Lambda stub
    const logAttendanceLambda = new lambda.Function(this, 'LogAttendanceLambda', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'logAttendance.handler',
      code: lambda.Code.fromAsset('../lambdas'),
      environment: {
        TABLE_NAME: attendanceTable.tableName,
      },
    });

    attendanceTable.grantReadWriteData(logAttendanceLambda);

    // Example: API Gateway
    const api = new apigateway.RestApi(this, 'ClassBitsApi', {
      restApiName: 'ClassBits Service',
    });

    const attendance = api.root.addResource('attendance');
    attendance.addMethod('POST', new apigateway.LambdaIntegration(logAttendanceLambda));
  }
}