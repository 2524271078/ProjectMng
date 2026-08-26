from django.http import JsonResponse

from licensing.services import get_license_status


EXEMPT_API_PREFIXES = (
    "/api/auth/login/",
    "/api/auth/me/",
    "/api/license/",
)


class LicenseEnforcementMiddleware:
    """Locks every business API when a production license is not valid."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and not request.path.startswith(EXEMPT_API_PREFIXES):
            license_status = get_license_status()
            if not license_status["active"]:
                return JsonResponse(
                    {
                        "code": "LICENSE_EXPIRED",
                        "detail": "系统授权无效或已到期，请联系授权管理员续期。",
                        "reason": license_status["reason"],
                    },
                    status=423,
                )
        return self.get_response(request)
