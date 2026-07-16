import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Step 1: add ``skill_uid`` as nullable, non-unique, no default.

    The field is intentionally added without a creation default so the
    framework does not auto-rewrite every existing row with a random
    UUIDv4. The data migration ``0003_populate_skill_uid`` assigns the
    committed registry UUIDs and a generated UUIDv4 to legacy rows
    outside the registry, and ``0004_skill_skill_uid_finalize`` then
    makes the field non-null, unique, and ``editable=False``.
    """

    dependencies = [
        ("skills", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="skill",
            name="skill_uid",
            field=models.UUIDField(
                null=True,
                blank=True,
                editable=False,
                help_text=(
                    "Cross-environment UUIDv4 identity for this canonical "
                    "skill. Assigned once from the committed skill UID "
                    "registry and is immutable."
                ),
            ),
        ),
    ]
