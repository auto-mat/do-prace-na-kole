from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
import logging

# logger = logging.getLogger(__name__)
logger = logging.getLogger("dpnk")


class DetailedJWTCookieAuthentication(JWTCookieAuthentication):
    def get_validated_token(self, raw_token):
        """
        Override to capture detailed token validation errors
        """
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            # Handle different token error types
            error_type = "token_error"
            error_detail = str(e)

            if "Token is invalid or expired" in error_detail:
                error_type = "token_expired"
            elif "Token has no user" in error_detail:
                error_type = "invalid_user"
            elif "Signature verification failed" in error_detail:
                error_type = "signature_failed"

            logger.error(f"JWT validation error: {error_detail}", exc_info=True)
            # Attach error details to the exception
            e.error_type = error_type
            e.error_detail = error_detail
            raise e

    def authenticate(self, request):
        logger.warning("Starting JWT authentication process")
        try:
            return super().authenticate(request)
        except AuthenticationFailed as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            # Add custom header to indicate authentication failure reason
            request.META["X-AUTH-ERROR"] = "authentication_failed"
            raise
        except InvalidToken as e:
            # Use the error details attached in get_validated_token
            if hasattr(e, "error_type") and hasattr(e, "error_detail"):
                request.META["X-TOKEN-ERROR"] = e.error_type
                request.META["X-TOKEN-ERROR-DETAIL"] = e.error_detail
            else:
                # Fallback if for some reason we don't have the details
                request.META["X-TOKEN-ERROR"] = "unknown_token_error"
                request.META["X-TOKEN-ERROR-DETAIL"] = str(e)
            raise
