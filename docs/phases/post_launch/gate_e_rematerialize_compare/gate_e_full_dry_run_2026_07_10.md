# Gate E Rematerialize and Compare Report

## Environment and Safety
- timestamp: 2026-07-10T17:51:04.647982+00:00
- git_commit: a13655d
- settings_module: config.settings.local
- database: engine=django.db.backends.postgresql, host=localhost, name=tunitech_abroad, port=5432
- backup_path: not_applicable_dry_run
- mode: dry-run
- processed_jobs: 171
- failures: 0

## Before Counts
- active_jobs: 171
- total_materialized_job_skills: 1680
- zero_skill_active_jobs: 5
- generic_only_active_jobs: 0
- weak_signal_count: 0
- missing_signal_count: 0
- partial_signal_count: 50
- strong_signal_count: 119
- low_confidence_materialized_skills: 10
- unmatched_candidate_total: 2625
- stale_recommendations: 181
- active_recommendations: 110
- active_cvs: 13
- cv_parse_warning_count: 11
- skill_signal_counts: {'excluded_non_it': 2, 'partial': 50, 'strong': 119}
- unmatched_candidate_counts: [{'source_type': 'cv', 'status': 'mapped', 'candidate_count': 4}, {'source_type': 'cv', 'status': 'pending', 'candidate_count': 158}, {'source_type': 'job', 'status': 'ignored', 'candidate_count': 39}, {'source_type': 'job', 'status': 'mapped', 'candidate_count': 334}, {'source_type': 'job', 'status': 'pending', 'candidate_count': 2084}, {'source_type': 'manual', 'status': 'pending', 'candidate_count': 6}]
- recommendation_counts: {'active': 110, 'expired_job': 132, 'stale': 181}
- match_result_counts: {'total': 65}

## After Counts
- active_jobs: 171
- total_materialized_job_skills: 1810
- zero_skill_active_jobs: 0
- generic_only_active_jobs: 1
- weak_signal_count: 1
- missing_signal_count: 0
- partial_signal_count: 46
- strong_signal_count: 122
- low_confidence_materialized_skills: 303
- unmatched_candidate_total: 2631
- stale_recommendations: 181
- active_recommendations: 110
- active_cvs: 13
- cv_parse_warning_count: 11
- skill_signal_counts: {'excluded_non_it': 2, 'generic_only': 1, 'partial': 46, 'strong': 122}
- unmatched_candidate_counts: [{'source_type': 'cv', 'status': 'mapped', 'candidate_count': 4}, {'source_type': 'cv', 'status': 'pending', 'candidate_count': 158}, {'source_type': 'job', 'status': 'ignored', 'candidate_count': 39}, {'source_type': 'job', 'status': 'mapped', 'candidate_count': 334}, {'source_type': 'job', 'status': 'pending', 'candidate_count': 2090}, {'source_type': 'manual', 'status': 'pending', 'candidate_count': 6}]
- recommendation_counts: {'active': 110, 'expired_job': 132, 'stale': 181}
- match_result_counts: {'total': 65}

## Top Changes
### removed_noisy_soft_or_process_skills
- Teamwork: 39
- Agile: 35
- Communication: 26
- Scrum: 12
- Performance Optimization: 4
- Code Review: 3
- Leadership: 2
- UML: 2
- Kanban: 1
- Root Cause Analysis: 1
### added_hard_technical_skills
- CI/CD: 46
- Network Security: 41
- Cybersecurity: 28
- Data Modeling: 8
- System and Network Administration: 7
- Embedded Systems: 3
- Cloud Security: 3
- TCP/IP: 3
- Docker Compose: 2
- Vulnerability Management: 2
- Object-Oriented Programming: 2
- C: 2
- Software Deployment: 1
- Application Security: 1
- GitLab CI/CD: 1
- Preventive Maintenance: 1
- OPC-UA: 1
- RAG: 1
- Data Warehouse: 1
- Embedded Linux: 1
### added_broad_non_scoring_signals
- Software Development: 114
- Software Testing: 1
### retained_hard_technical_skills
- SQL: 48
- Python: 43
- Git: 42
- DevOps: 42
- Java: 40
- Docker: 34
- GitLab: 30
- Azure: 28
- JavaScript: 27
- Kubernetes: 25
- Linux: 25
- PostgreSQL: 22
- Angular: 21
- Jenkins: 21
- AWS: 20
- REST API: 19
- Google Cloud: 19
- Spring Boot: 17
- TypeScript: 16
- GitLab CI/CD: 16
### unexpected_noisy_canonical_additions
- none
### top_unmatched_phrases_after
- normalized_text=concevoir une application web, source_type=job, status=pending, occurrence_count=624
- normalized_text=application web, source_type=job, status=pending, occurrence_count=500
- normalized_text=rediger un cahier des charges des specifications techniques, source_type=job, status=pending, occurrence_count=414
- normalized_text=analyser exploiter structurer des donnees, source_type=job, status=pending, occurrence_count=292
- normalized_text=determiner des mesures correctives, source_type=job, status=pending, occurrence_count=229
- normalized_text=configurer et optimiser des systemes devops, source_type=job, status=pending, occurrence_count=206
- normalized_text=concevoir et gerer un projet, source_type=job, status=pending, occurrence_count=108
- normalized_text=analyser les besoins informatiques, source_type=job, status=pending, occurrence_count=106
- normalized_text=optimiser les processus de qualite pour assurer la fiabilite des logiciels, source_type=job, status=pending, occurrence_count=99
- normalized_text=configurer le poste de travail aux besoins de l utilisateur, source_type=job, status=pending, occurrence_count=87
- normalized_text=administrer un systeme d informations, source_type=job, status=pending, occurrence_count=79
- normalized_text=concevoir et developper une solution digitale, source_type=job, status=pending, occurrence_count=77
- normalized_text=analyser resoudre un probleme courant ou complexe, source_type=job, status=pending, occurrence_count=76
- normalized_text=concevoir un logiciel un systeme d informations une application, source_type=job, status=pending, occurrence_count=75
- normalized_text=evaluer le resultat de ses actions, source_type=job, status=pending, occurrence_count=75
- normalized_text=apporter une assistance technique aux equipes, source_type=job, status=pending, occurrence_count=66
- normalized_text=developper une application en lien avec une base de donnees, source_type=job, status=pending, occurrence_count=61
- normalized_text=agile methodologies, source_type=job, status=mapped, occurrence_count=60
- normalized_text=communiquer aupres de ses interlocuteurs internes et externes, source_type=job, status=pending, occurrence_count=57
- normalized_text=coder des donnees, source_type=job, status=pending, occurrence_count=56
### before_after_transitions
- zero_skill_to_nonzero: 5
- nonzero_to_zero_skill: 0
- generic_weak_to_useful: 0
- useful_to_weak_generic: 1
- unchanged: 165
### jobs_changing_to_useful_signals
- none
### jobs_becoming_hidden_or_weak
- after=generic_only, before=partial, public_id=c4203a6e-f3c9-4b25-be55-b724b7fbd6e6, source_job_id=209HGLC, title=Ingénieur Logiciel (H/F)
### failures_or_skipped_rows
- reason=include_matches_not_requested, scope=matches

## Refresh Counts
- rematerialized_jobs: 171
- search_vectors_rebuilt: 166
- recommendations_marked_stale: 0
- recommendations_refreshed: 0
- matches_refreshed: 0
- cvs_reparsed: 0

## Regression Cases
- chef de projet rejects Chef: pass
- DevOps/Chef cookbook context accepts canonical Chef: pass
- SQL Server does not add SQL duplicate: pass
- PostgreSQL, MySQL, SQLite aliases map to distinct canonicals: pass
- source metadata phrases reject materialization: pass
- Teamwork, Communication, Agile, Scrum are not required technical skills: pass
- API and Monitoring are not required hard skills: pass
- REST API, OpenAPI, GraphQL retain specific behavior where supported: pass
- CV-origin noisy phrases are not ProfileSkill rows: pass
- recommendation/match score consistency uses actual current scores: not_run (comparable_pairs=0, mismatches=0)

## Quality Gate Explanation
- broad_materialized_rows: 303
- broad_required_rows: 0
- broad_optional_rows: 43
- broad_detected_rows: 260
- soft_or_process_materialized_rows: 0
- unexpected_noisy_added_rows: 0
- broad_signal_scoring_check: pass

## Safety Confirmations
- stored local job data only
- no France Travail calls
- no OpenRouter calls
- no canonical Skill auto-creation
- no raw CV text or private CV paths included
- dry-run uses one database transaction and does not enqueue tasks, send email, call external APIs, call LLM, or reparse CVs
