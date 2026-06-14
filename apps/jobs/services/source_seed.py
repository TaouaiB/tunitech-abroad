from apps.jobs.models import JobSource, SourceType


def seed_job_sources():
    sources = [
        {
            "slug": "france_travail",
            "name": "France Travail",
            "base_url": "https://candidat.francetravail.fr/offres/recherche",
            "source_type": SourceType.API,
            "is_active": True,
        }
    ]

    for source_data in sources:
        JobSource.objects.update_or_create(
            slug=source_data["slug"],
            defaults={
                "name": source_data["name"],
                "base_url": source_data["base_url"],
                "source_type": source_data["source_type"],
                "is_active": source_data["is_active"],
            },
        )
