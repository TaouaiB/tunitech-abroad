class UserIdentityService:
    @staticmethod
    def update_names(user, *, first_name: str, last_name: str):
        user.first_name = (first_name or "").strip()
        user.last_name = (last_name or "").strip()
        user.save(update_fields=["first_name", "last_name"])
        return user

    @staticmethod
    def initialize_social_names(user, extra_data: dict):
        data = extra_data if isinstance(extra_data, dict) else {}
        first_name = (data.get("given_name") or data.get("first_name") or "").strip()
        last_name = (data.get("family_name") or data.get("last_name") or "").strip()
        full_name = (data.get("name") or data.get("full_name") or "").strip()
        if full_name and not first_name and not last_name:
            parts = full_name.split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        update_fields = []
        if first_name and not user.first_name:
            user.first_name = first_name
            update_fields.append("first_name")
        if last_name and not user.last_name:
            user.last_name = last_name
            update_fields.append("last_name")
        if update_fields:
            user.save(update_fields=update_fields)
        return user
