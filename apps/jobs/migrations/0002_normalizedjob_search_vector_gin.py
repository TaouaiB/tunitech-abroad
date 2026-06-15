from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="normalizedjob",
            index=GinIndex(fields=["search_vector"], name="jobs_normal_search_vector_gin"),
        ),
    ]
