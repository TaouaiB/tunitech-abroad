import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Step 3: finalize ``skill_uid``.

    Promote the field to non-null, unique, ``editable=False``, with
    ``default=uuid.uuid4`` for any new ``Skill`` row created after
    this migration. The model-level ``save()`` immutability check
    (introduced in this branch) prevents any code from rotating the
    UUID of an existing row.
    """

    dependencies = [
        ("skills", "0003_populate_skill_uid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="skill",
            name="skill_uid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text=(
                    "Cross-environment UUIDv4 identity for this canonical "
                    "skill. Assigned once from the committed skill UID "
                    "registry and is immutable."
                ),
                unique=True,
            ),
        ),
    ]
