# authaction-python-django-example

A Python Django application demonstrating API authorization using [AuthAction](https://app.authaction.com/) with JWKS-based JWT validation.

## Overview

This application shows how to configure and handle authorization using AuthAction's access tokens in a Django REST Framework API. It validates JSON Web Tokens (JWT) signed with RS256 by fetching public keys dynamically from AuthAction's JWKS endpoint.

## Prerequisites

- **Python 3.11+**
- **AuthAction credentials**: `tenantDomain` and `apiIdentifier` from your AuthAction account.

## Installation

1. **Clone the repository**:

   ```bash
   git clone git@github.com:authaction/authaction-python-django-example.git
   cd authaction-python-django-example
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your AuthAction credentials**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace the placeholders:

   ```env
   AUTHACTION_DOMAIN=your-authaction-tenant-domain
   AUTHACTION_AUDIENCE=your-authaction-api-identifier
   DJANGO_SECRET_KEY=your-django-secret-key
   ```

## Usage

1. **Start the development server**:

   ```bash
   python manage.py runserver
   ```

   The API will be available at `http://localhost:8000`.

2. **Obtain an access token** via client credentials:

   ```bash
   curl --request POST \
     --url https://your-authaction-tenant-domain/oauth2/m2m/token \
     --header 'content-type: application/json' \
     --data '{
       "client_id": "your-authaction-app-clientid",
       "client_secret": "your-authaction-app-client-secret",
       "audience": "your-authaction-api-identifier",
       "grant_type": "client_credentials"
     }'
   ```

3. **Call the public endpoint** (no token required):

   ```bash
   curl http://localhost:8000/public
   ```

   ```json
   { "message": "This is a public message!" }
   ```

4. **Call the protected endpoint** with the access token:

   ```bash
   curl --request GET \
     --url http://localhost:8000/protected \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
   ```

   ```json
   { "message": "This is a protected message!", "sub": "client-id@clients" }
   ```

## Project Structure

```
authaction-python-django-example/
├── authaction_django/
│   ├── settings.py          # Django + DRF configuration
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── api/
│   ├── authentication.py    # JWKS fetching and JWT validation
│   ├── views.py             # public + protected views
│   └── urls.py              # API URL routing
├── manage.py
├── .env.example
├── requirements.txt
└── README.md
```

## Code Explanation

### `api/authentication.py` — JWT Validation

Equivalent to `JwtStrategy` in the NestJS example.

- **`_get_jwks()`** — Fetches and in-memory caches the public keys from
  `https://{AUTHACTION_DOMAIN}/.well-known/jwks.json`. On a cache miss caused
  by key rotation, it busts the cache and retries once.

- **`_find_rsa_key(token)`** — Extracts the `kid` from the unverified token
  header and finds the matching RSA key in the JWKS response.

- **`verify_token(token)`** — Decodes and validates the JWT using:
  - Algorithm: `RS256`
  - Issuer: `https://{AUTHACTION_DOMAIN}`
  - Audience: `{AUTHACTION_AUDIENCE}`

- **`JWTAuthentication`** — A DRF `BaseAuthentication` subclass. It extracts the
  `Bearer` token from the `Authorization` header, calls `verify_token`, and
  returns an `AuthenticatedToken` object that DRF assigns to `request.user`.

### `api/views.py` — Views

- **`GET /public`** — Uses `@permission_classes([AllowAny])`, accessible without
  authentication.
- **`GET /protected`** — Uses `@permission_classes([IsAuthenticated])` with
  `@authentication_classes([JWTAuthentication])`. Returns 401 if no valid token
  is provided.

### `authaction_django/settings.py` — DRF Configuration

`REST_FRAMEWORK` sets `JWTAuthentication` as the default authentication class
and `IsAuthenticated` as the default permission class, so all views are protected
by default unless explicitly overridden with `AllowAny`.

## Common Issues

**Invalid token errors** — Verify that `AUTHACTION_DOMAIN` and
`AUTHACTION_AUDIENCE` match the values in your AuthAction dashboard exactly.

**Public key fetching errors** — Check that your application can reach
`https://{AUTHACTION_DOMAIN}/.well-known/jwks.json`.

**Unauthorized access** — Ensure the `Authorization: Bearer <token>` header is
present and the token was issued for the correct audience.

## Contributing

Feel free to submit issues or pull requests if you encounter bugs or have suggestions for improvement!
