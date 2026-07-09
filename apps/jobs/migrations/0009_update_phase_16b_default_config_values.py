from django.db import migrations


def update_phase_16b_defaults(apps, schema_editor):
    JobIngestionConfig = apps.get_model("jobs", "JobIngestionConfig")

    JobIngestionConfig.objects.filter(max_jobs_per_run=200).update(max_jobs_per_run=1000)
    JobIngestionConfig.objects.filter(page_size=50).update(page_size=100)
    JobIngestionConfig.objects.filter(stale_after_hours=24).update(stale_after_hours=48)
    JobIngestionConfig.objects.filter(removed_after_hours=72).update(removed_after_hours=168)


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0008_jobingestionqueryrun_and_more"),
    ]

    operations = [
        migrations.RunPython(update_phase_16b_defaults, migrations.RunPython.noop),
    ]
