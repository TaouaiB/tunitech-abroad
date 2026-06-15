from apps.privacy.models import ConsentRecord


class ConsentService:
    @staticmethod
    def record(
        user,
        consent_type,
        consent_text="",
        consent_version="1.0",
        request_meta=None,
        accepted=True,
        ip_address=None,
        user_agent="",
    ):
        request_meta = request_meta or {}
        source_path = request_meta.get("source_path") or request_meta.get("path") or ""
        stored_text = consent_text
        if source_path:
            stored_text = f"{stored_text} Source: {source_path}".strip()[:255]

        return ConsentRecord.objects.create(
            user=user,
            consent_type=consent_type,
            consent_text=stored_text[:255],
            consent_version=consent_version,
            accepted=accepted,
            ip_address=ip_address or request_meta.get("ip_address"),
            user_agent=(user_agent or request_meta.get("user_agent", ""))[:500],
        )
