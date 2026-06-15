from django.db import connection
from django.core.cache import cache

class HealthCheckService:
    @classmethod
    def check(cls) -> dict:
        db_status = "ok"
        redis_status = "ok"
        status = "ok"

        try:
            connection.ensure_connection()
        except Exception:
            db_status = "error"
            status = "degraded"

        try:
            cache.set("health_check_test", "1", timeout=5)
            if cache.get("health_check_test") != "1":
                redis_status = "error"
                status = "degraded"
        except Exception:
            redis_status = "error"
            status = "degraded"

        return {
            "status": status,
            "database": db_status,
            "redis": redis_status,
        }
