// AWS Amplify Configuration for ClassBits
// This configures AWS Cognito for authentication

export const amplifyConfig = {
    Auth: {
        Cognito: {
            userPoolId: 'us-east-1_z61jO4Mni',
            userPoolClientId: '6pfufvg52tejjmoa03rigpev8i',
            loginWith: {
                email: true,
            },
        }
    }
};
