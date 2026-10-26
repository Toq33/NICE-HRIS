"""drf-spectacular OpenAPI 3 security scheme extensions for CookieOrHeaderJWTAuthentication and APIKeyAuthentication."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CookieOrHeaderJWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = "core.authentication.CookieOrHeaderJWTAuthentication"
    name = "BearerOrCookieJWT"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token in `Authorization: Bearer <token>` header or HTTP-only `access_token` cookie.",
        }


class APIKeyAuthScheme(OpenApiAuthenticationExtension):
    target_class = "core.authentication.APIKeyAuthentication"
    name = "TenantAPIKey"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Scoped tenant API key (`nhris_...`) or OAuth2 client token.",
        }
