const REGION = "us-east-1";
const CLIENT_ID = "6pfufvg52tejjmoa03rigpev8i";
const COGNITO_URL = `https://cognito-idp.${REGION}.amazonaws.com/`;

/* ----------------------------- Types ----------------------------- */

// Result type for Cognito InitiateAuth
export interface CognitoInitiateAuthResponse {
    AuthenticationResult?: {
        AccessToken: string;
        IdToken: string;
        RefreshToken: string;
        TokenType: string;
        ExpiresIn: number;
    };
    ChallengeName?: string;
    Session?: string;
    message?: string;
}

// Result type for Cognito SignUp
export interface CognitoSignUpResponse {
    UserConfirmed: boolean;
    CodeDeliveryDetails?: {
        Destination: string;
        DeliveryMedium: string;
        AttributeName: string;
    };
}

/* ----------------------------- Helper ----------------------------- */

async function cognitoRequest<T>(action: string, body: object): Promise<T> {
    const res = await fetch(COGNITO_URL, {
        method: "POST",
        headers: {
            "X-Amz-Target": `AWSCognitoIdentityProviderService.${action}`,
            "Content-Type": "application/x-amz-json-1.1",
        },
        body: JSON.stringify(body),
    });

    return res.json() as Promise<T>;
}

export async function getValidIdToken(): Promise<string | null> {
  const idToken = localStorage.getItem("idToken");
  const refreshTokenValue = localStorage.getItem("refreshToken");

  // naive expiry check: you can decode JWT and check exp claim
  if (idToken && !isExpired(idToken)) {
    return idToken;
  }

  if (refreshTokenValue) {
    const result = await refreshToken(refreshTokenValue);
    if (result.AuthenticationResult?.IdToken) {
      const { IdToken, AccessToken, RefreshToken } = result.AuthenticationResult; // <-- Destructure RefreshToken

      localStorage.setItem("idToken", IdToken);
      localStorage.setItem("accessToken", AccessToken);

      // CRITICAL FIX: Update the refresh token if a new one is returned
      if (RefreshToken) {
        localStorage.setItem("refreshToken", RefreshToken);
      }

      return IdToken;
    }
  }

  return null;
}

function isExpired(token: string): boolean {
  const payload = JSON.parse(atob(token.split(".")[1]));
  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

/* ----------------------------- Public APIs ----------------------------- */

// LOGIN (matches AWS CLI initiate-auth)
export function loginUser(
    username: string,
    password: string
): Promise<CognitoInitiateAuthResponse> {
    return cognitoRequest<CognitoInitiateAuthResponse>("InitiateAuth", {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: CLIENT_ID,
        AuthParameters: {
            USERNAME: username,
            PASSWORD: password,
        },
    });
}

// REFRESH TOKEN
export function refreshToken(
    refreshToken: string
): Promise<CognitoInitiateAuthResponse> {
    return cognitoRequest<CognitoInitiateAuthResponse>("InitiateAuth", {
        AuthFlow: "REFRESH_TOKEN_AUTH",
        ClientId: CLIENT_ID,
        AuthParameters: {
            REFRESH_TOKEN: refreshToken,
        },
    });
}

// REGISTER USER
export function registerUser(
    email: string,
    password: string
): Promise<CognitoSignUpResponse> {
    return cognitoRequest<CognitoSignUpResponse>("SignUp", {
        ClientId: CLIENT_ID,
        Username: email,
        Password: password,
        UserAttributes: [{ Name: "email", Value: email }],
    });
}

export interface CognitoConfirmSignUpResponse {
    $metadata?: object;
    message?: string;
}

export function confirmUser(email: string, code: string): Promise<CognitoConfirmSignUpResponse> {
    return cognitoRequest<CognitoConfirmSignUpResponse>("ConfirmSignUp", {
        ClientId: CLIENT_ID,
        Username: email,
        ConfirmationCode: code,
    });
}

// LOGOUT (local only)
export function logoutUser(): void {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("idToken");
    localStorage.removeItem("refreshToken");
}