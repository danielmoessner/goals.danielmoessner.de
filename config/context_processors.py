from __future__ import annotations

from django.conf import settings


def build_info(request):
    image_version = getattr(settings, "IMAGE_VERSION", "unknown")
    image_version = (image_version or "unknown").strip()

    return {
        "image_version": image_version,
        "image_version_short": image_version[:7] if image_version != "unknown" else "",
    }
