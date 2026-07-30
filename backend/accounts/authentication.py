from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import TokenActivity


class IdleTimeoutTokenAuthentication(TokenAuthentication):
    """Reject tokens that have been idle for longer than the configured limit."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        now = timezone.now()
        activity, _ = TokenActivity.objects.get_or_create(
            token=token,
            defaults={"last_active_at": token.created},
        )
        timeout = timedelta(seconds=getattr(settings, "TOKEN_IDLE_TIMEOUT_SECONDS", 1800))
        if now - activity.last_active_at >= timeout:
            token.delete()
            raise AuthenticationFailed("登录已超时，请重新登录。")
        TokenActivity.objects.filter(pk=activity.pk).update(last_active_at=now)
        return user, token
