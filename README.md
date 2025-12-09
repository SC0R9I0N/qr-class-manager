# ClassBits: Serverless Deployment Guide

This document provides a comprehensive guide to deploying the QR Class Manager application, which uses AWS CDK for infrastructure and a React/Vite application for the frontend.

The current cloudfront website can be found [here](https://d12l6j7r4rtj92.cloudfront.net/).

If you want to simply test the functionality of it, you could register your own student user (Instructor users have to be manually assigned to the professor by the system administrator Cognito user group so as to not pose a security risk) or you could use our two test accounts that we made to test its functionality:

| **Role** | **Email** | **Password** |
|----------|-----------|--------------|
| Instructor | `prof@example.com` | `SecurePass123!` |
| Student   | `student1@example.com` | `StrongPass123!` |

# Architecture Summary

The infrastructure is built entirely on a modern serverless stack managed by AWS CDK (Python).

| **AWS Service** | **Purpose** |
|-----------------|-------------|
| IAM | Provides Execution Roles for Lambdas and the User for the deployment process. |  
| API Gateway | The public REST API endpoint for the frontend. |  
| Lambda | Serverless compute for all business logic (e.g., creating sessions, scanning attendance). |  
| DynamoDB | High-performance NoSQL storage for class, session, and attendance data. |  
| Cognito | Handles all user authentication (sign-up, sign-in). |  
| S3 | Hosts the static React assets and the QR code images. |
| CloudFront | Contend Delivery Network that caches content from S3 and delivers the website globally. |

---

### 1. Prerequisites

Before you begin, ensure you have the following tools installed:  
- Git: For cloning the repository.  
- AWS CLI: For configuring your AWS credentials.  
- Python 3.11+: For running the CDK infrastructure code.  
- Node.js (LTS) & npm: For building and running the React frontend.  
- AWS CDK CLI: Install globally via npm:  

```bash
npm install -g aws-cdk
```

### 2. Manual AWS Setup (IAM)

To allow the CDK to deploy resources into your account, you must set up an administrative user.
- Create an IAM User: Log into your AWS Management Console and navigate to IAM. Create a new user (e.g., cdk-deployer).
- Set Credentials Type: Choose Access key - Programmatic access.
- Attach Policy: For simplicity during initial deployment, attach the AdministratorAccess managed policy. In a production environment, you should follow the principle of least privilege and use a granular policy limited to the resources deployed by CDK (Lambda, DynamoDB, API Gateway, S3, CloudFront, etc.).
- Save Credentials: Once created, save the Access Key ID and Secret Access Key. You will need these for the next step.
- Configure AWS CLI:

```bash
aws configure
```
When prompted, enter your Access Key ID, Secret Access Key, and your desired Region (e.g., us-east-1).

### 3. Infrastructure Deployment (AWS CDK)
This process deploys the entire serverless backend: Lambda functions, DynamoDB tables, API Gateway, and Cognito.

A. Clone and Setup

```bash
git clone <your-repo-url>
cd qr-class-manager/infra
```

Initialize Python Environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\Activate.ps1  # On Windows (CMD) or source .venv/Scripts/activate (PowerShell)
```

Install Dependencies:

```bash
pip install -r requirements-dev.txt
```

B. CDK Deploy
Bootstrap CDK (first-time only):

```bash
cdk bootstrap
```

Deploy the Stack:

```bash
cdk deploy
```

Record Outputs: After a successful deployment, the terminal will display several outputs across your AWS consoles, including the Cognito User Pool ID, Client ID, and the FrontendDistributionDomainName (the CloudFront URL). Record these values as they are needed for the frontend configuration. For example, ours looked like this:

| **Item** | **Value** |
|----------|-----------|
| Cognito User Pool ID | `us-east-1_z61jO4Mni` |
| Cognito App Client ID | `6pfufvg52tejjmoa03rigpev8i` |
| Base URL | `https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/` |

4. Frontend Local Development (React/Vite)
You can run the frontend locally to verify API connectivity before the final static deployment.
Navigate to the Frontend:

```bash
cd ../frontend/qr-class-manager
```

Install Node Dependencies:

```bash
npm install
```

Configure Environment Variables: The React application needs the AWS resource IDs created by the CDK. Create a file named .env.local in the current directory and paste the outputs from the previous step.

```env
# .env.local (Example - Use your actual values from the CDK output)
VITE_API_BASE_URL="<API_Gateway_Endpoint_URL>" 
VITE_USER_POOL_ID="<CognitoUserPoolID>"
VITE_APP_CLIENT_ID="<CognitoAppClientID>"
VITE_QR_DISTRIBUTION_DOMAIN="<QrCodeDistributionDomainName>" 
# VITE_REGION is usually inferred but can be set if needed
```

Run locally:

```bash
npm run dev
```

The application will open at http://localhost:5173 (or similar, output will be in the npm run dev). You can now test sign-up and sign-in functionality.

5. Final Deployment to CloudFront
The final step is to build the optimized React bundle and upload it to the S3 bucket that is connected to the CloudFront distribution.
A. Build the Frontend

```bash
npm run build
```

B. Upload to S3 and Serve via CloudFront
You need to identify the name of the S3 bucket that was created by the CDK for frontend hosting. Its name typically follows the pattern frontendbucket<hash>.
Identify S3 Bucket Name: Look at your CDK outputs or run cdk synth and check the S3 bucket resource name. Alternatively, you can list the buckets in your console. The bucket created by the FrontendBucket construct is the target.
Sync the dist folder to S3:

```bash
# IMPORTANT: Ensure you are in the qr-class-manager/frontend/qr-class-manager directory
aws s3 sync dist/ s3://<YourFrontendBucketName>/ --delete --profile cdk-qr-manager
```

Access the Application: The application is now live! Access it using the CloudFront URL from the CloudFront console in AWS (FrontendDistributionDomainName).

```plaintext
https://<YourFrontendDistributionDomainName>
```

C. (Optional) Invalidate CloudFront Cache
If you deploy updates and the changes don't immediately appear, the CDN is likely caching the old files. You can force a refresh by invalidating the cache.
Get Distribution ID: Find the ID of the FrontendDistribution in the CloudFront console.
Run Invalidation:

```bash
aws cloudfront create-invalidation --distribution-id <YourDistributionID> --paths "/*" --profile cdk-qr-manager
```

Changes will propagate within a few minutes.

This is the overall guide on how to set up this project on your own, if you wish, you could also add all of the necessary secrets to a GitHub repository and push the code and ci.yml will do most of this process with the exception of manually creating the IAM user and finding the necessary values such as the Cognito User Pool ID, Cognito App Client ID, and the Base Link.

## Architecture Diagram

<img width="1191" height="937" alt="Architecture Diagram" src="https://github.com/user-attachments/assets/65f44f30-bbb0-47d5-b6a6-3e8ca4d4007e" />


## Written Justification

We chose to use AWS Lambda instead of EC2 because our workload is entirely event-driven and triggered by user actions such as scanning QR codes or uploading materials. Lambda’s serverless architecture eliminates the need to manage any sort of infrastructure and is more suitable for bursty and unpredictable traffic patterns, which is to be expected from our project. 

We chose DynamoDB as our backend database rather than a service like AWS Relational Database Service (RDS) because all our data entries are key-value and non-relational, making DynamoDB’s flexible schema a better fit for our workload. Since queries for our project are predictable (by class_id, student_id, etc.), DynamoDB’s Global Secondary Indexes (GSI) provide us with efficient lookups that are useful for analytics and student tracking. 

We used Amazon S3 to store both QR codes and lecture materials. We chose Amazon S3 for storage over AWS Elastic Block Store (EBS) because S3 allows easy object-based storage access directly from the web, enabling students and professors to download materials or scan QR codes without a running server. Its seamless integration with CloudFront along with its scalability and easy access made it ideal for our project. 

We chose CloudFront for our front-end React application and for publicly served QR code images. Instead of accessing S3 directly, CloudFront ensures HTTPS delivery, fast response times, and ultimately better security. This improves user experience, especially for devices in classrooms or locations that have varying network speeds. 

We chose Cognito to manage user authentication and authorization for professors and students. This was chosen over other services such as custom JWT systems because Cognito integrates directly with API Gateway and simplifies secure sign-up, sign-in, and group-based access control. With Cognito, we avoided the complexity of building and maintaining our own authentication backend, handling password security, token refresh, and user group management manually. 

We chose IAM (Identity and Access Management) as the core security and permissions layer. This was essential because it allows us to implement the Principle of Least Privilege (POLP). For example, we use IAM Roles to ensure our Lambda functions can only write attendance data to the DynamoDB table and only read files from the S3 bucket dedicated to student photos. This prevents a misconfigured or compromised service from accessing or deleting unrelated resources, providing granular, verifiable control over every component's interaction within the AWS environment.

API Gateway exposes a unified REST interface for all backend functions of our project. We chose this over manually managing API endpoints on EC2 because it supports CORS, request validation, and integration with Lambda and Cognito. This ultimately made it easy to manage APIs across services in a secure and consistent manner. 
