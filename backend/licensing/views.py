from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from licensing.permissions import IsLicenseOperator
from licensing.services import activate_license, get_license_status


@api_view(["GET"])
@permission_classes([IsLicenseOperator])
def license_status_view(request):
    return Response(get_license_status(record_activity=False))


@api_view(["GET"])
@permission_classes([IsLicenseOperator])
def license_request_view(request):
    data = get_license_status(record_activity=False)
    return Response({
        "product": "交付中台",
        "license_version": 1,
        "machine_fingerprint": data["machine_fingerprint"],
    })


@api_view(["POST"])
@permission_classes([IsLicenseOperator])
def activate_license_view(request):
    envelope = request.data.get("license")
    if isinstance(envelope, str):
        import json
        try:
            envelope = json.loads(envelope)
        except json.JSONDecodeError:
            return Response({"detail": "授权文件格式不正确。"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(activate_license(envelope))
    except ValueError as error:
        return Response({"detail": "授权文件校验失败。", "reason": str(error)}, status=status.HTTP_400_BAD_REQUEST)
