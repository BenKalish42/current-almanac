"""
RevenueCat + subscription normalization helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

CURRENT_PLUS_ENTITLEMENT = "current_plus"


def _parse_optional_datetime(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, str):
        return value
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class RevenueCatConfig:
    api_key: str
    project_id: str | None = None
    base_url: str = "https://api.revenuecat.com/v1"


def get_revenuecat_config() -> RevenueCatConfig | None:
    import os

    api_key = os.environ.get("REVENUECAT_SECRET_API_KEY")
    if not api_key:
        return None
    return RevenueCatConfig(
        api_key=api_key,
        project_id=os.environ.get("REVENUECAT_PROJECT_ID"),
        base_url=os.environ.get("REVENUECAT_API_BASE_URL", "https://api.revenuecat.com/v1"),
    )


def _coerce_entitlement_snapshot(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "identifier": name,
        "product_identifier": payload.get("product_identifier"),
        "purchase_date": payload.get("purchase_date"),
        "expires_date": payload.get("expires_date"),
        "grace_period_expires_date": payload.get("grace_period_expires_date"),
    }


def normalize_revenuecat_subscriber(
    subscriber_payload: dict[str, Any],
    *,
    entitlement_name: str = CURRENT_PLUS_ENTITLEMENT,
) -> dict[str, Any]:
    subscriber = subscriber_payload.get("subscriber", subscriber_payload)
    entitlements = subscriber.get("entitlements") or {}
    subscriptions = subscriber.get("subscriptions") or {}

    entitlement_info = entitlements.get(entitlement_name)
    is_paid = False
    expires_at = None
    if entitlement_info:
        expires_at = _parse_optional_datetime(entitlement_info.get("expires_date"))
        if expires_at is None:
            is_paid = True
        else:
            try:
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                is_paid = expiry > datetime.now(timezone.utc)
            except ValueError:
                is_paid = True

    active_products = [
        product_id
        for product_id, details in subscriptions.items()
        if _parse_optional_datetime(details.get("expires_date")) is None
        or (
            _parse_optional_datetime(details.get("expires_date"))
            and datetime.fromisoformat(
                str(details.get("expires_date")).replace("Z", "+00:00")
            )
            > datetime.now(timezone.utc)
        )
    ]

    preferred_subscription: dict[str, Any] | None = None
    for details in subscriptions.values():
        if not preferred_subscription:
            preferred_subscription = details
            continue
        current_expires = _parse_optional_datetime(preferred_subscription.get("expires_date"))
        candidate_expires = _parse_optional_datetime(details.get("expires_date"))
        if candidate_expires and (
            not current_expires
            or candidate_expires > current_expires
        ):
            preferred_subscription = details

    return {
        "app_user_id": subscriber.get("original_app_user_id") or subscriber.get("app_user_id"),
        "original_app_user_id": subscriber.get("original_app_user_id"),
        "is_paid": is_paid,
        "active_entitlements": {
            name: _coerce_entitlement_snapshot(name, payload)
            for name, payload in entitlements.items()
        },
        "active_products": active_products,
        "store": preferred_subscription.get("store") if preferred_subscription else None,
        "period_type": preferred_subscription.get("period_type") if preferred_subscription else None,
        "expires_at": expires_at,
        "will_renew": preferred_subscription.get("unsubscribe_detected_at") is None
        if preferred_subscription
        else None,
        "billing_issue_detected_at": preferred_subscription.get("billing_issues_detected_at")
        if preferred_subscription
        else None,
        "management_url": subscriber.get("management_url"),
        "raw_customer_info": subscriber_payload,
        "updated_at": _now_iso(),
    }


def fetch_revenuecat_subscriber(app_user_id: str, platform: str | None = None) -> dict[str, Any]:
    config = get_revenuecat_config()
    if not config:
        raise RuntimeError("RevenueCat is not configured.")

    encoded_id = quote(app_user_id, safe="")
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    if platform:
        headers["X-Platform"] = platform

    url = f"{config.base_url.rstrip('/')}/subscribers/{encoded_id}"
    response = httpx.get(url, headers=headers, timeout=20.0)
    response.raise_for_status()
    return response.json()
