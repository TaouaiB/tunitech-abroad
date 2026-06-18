from django.db import migrations


def set_default_site_brand(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=1,
        defaults={"domain": "localhost:8000", "name": "TuniTech Abroad"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(set_default_site_brand, migrations.RunPython.noop),
    ]
