"""Tests for the ``skill_uid`` migration chain.

The migration chain must:
- add ``skill_uid`` as nullable, non-unique, no default in step 1;
- assign the committed registry UUID to matching canonical skills
  in step 2;
- generate a fresh UUIDv4 only for legitimate non-registry rows in
  step 2;
- promote the field to non-null, unique, ``editable=False``, with a
  ``default=uuid.uuid4`` for new rows in step 3.

The Django test runner cannot easily rewind migrations inside a
single test process because the test database is already at HEAD.
These tests therefore run child Python processes against an isolated
test database, migrate to a specific point, insert test rows via
raw SQL when needed, then migrate forward to the target. The user's
local development database is never touched.
"""

import json
import os
import subprocess
import sys
import textwrap
import uuid

from django.conf import settings
from django.test import SimpleTestCase

from apps.skills.services.skill_uid_registry import (
    get_skill_uid,
    has_skill_uid,
)


PROJECT_ROOT = str(settings.BASE_DIR)
TEST_DB_NAME = "test_tuniatlas_ml_migration_isolated"


BEFORE_SKILL_UID = "0001_initial"
MIGRATION_NULLABLE = "0002_skill_skill_uid_nullable"
MIGRATION_POPULATE = "0003_populate_skill_uid"
MIGRATION_FINALIZE = "0004_skill_skill_uid_finalize"


_CHILD_RUN_AND_DUMP = textwrap.dedent(
    """
    import os, sys, json, uuid, django
    PROJECT_ROOT = sys.argv[1]
    TEST_DB_NAME = sys.argv[2]
    sys.path.insert(0, PROJECT_ROOT)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    django.setup()
    from django.db import connection, connections
    payload = json.loads(sys.stdin.read())
    with connection.cursor() as cur:
        cur.execute('DROP DATABASE IF EXISTS \\"' + TEST_DB_NAME + '\\"')
        cur.execute('CREATE DATABASE \\"' + TEST_DB_NAME + '\\"')
    connection.close()
    conn = connections['default']
    conn.settings_dict['NAME'] = TEST_DB_NAME
    conn.connect()
    from django.test.utils import setup_databases, teardown_databases
    old_config = setup_databases(verbosity=0, interactive=False, keepdb=False)
    try:
        from django.core.management import call_command
        call_command('migrate', 'skills', '0001_initial', verbosity=0)
        with connection.cursor() as cur:
            for row in payload['insert_rows']:
                cur.execute(
                    "INSERT INTO skills_skill "
                    "(canonical_name, slug, category, is_active, source, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                    [row['canonical_name'], row['slug'], row.get('category', 'other'),
                     row.get('is_active', True), row.get('source', 'manual')],
                )
        target = payload['target_migration']
        if target != '0001_initial':
            call_command('migrate', 'skills', target, verbosity=0)
        from apps.skills.models import Skill
        rows = list(Skill.objects.values('id', 'canonical_name', 'skill_uid', 'is_active'))
        print('---BEGIN---')
        print(json.dumps({'rows': rows}, default=str))
        print('---END---')
    finally:
        teardown_databases(old_config, verbosity=0)
    """
).strip()


_CHILD_FIELD_META = textwrap.dedent(
    """
    import os, sys, json, django
    PROJECT_ROOT = sys.argv[1]
    TEST_DB_NAME = sys.argv[2]
    sys.path.insert(0, PROJECT_ROOT)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    django.setup()
    from django.db import connection, connections
    payload = json.loads(sys.stdin.read())
    with connection.cursor() as cur:
        cur.execute('DROP DATABASE IF EXISTS \\"' + TEST_DB_NAME + '\\"')
        cur.execute('CREATE DATABASE \\"' + TEST_DB_NAME + '\\"')
    connection.close()
    conn = connections['default']
    conn.settings_dict['NAME'] = TEST_DB_NAME
    conn.connect()
    from django.test.utils import setup_databases, teardown_databases
    old_config = setup_databases(verbosity=0, interactive=False, keepdb=False)
    try:
        from django.core.management import call_command
        target = payload['target_migration']
        if target == '0001_initial':
            call_command('migrate', 'skills', '0001_initial', verbosity=0)
        else:
            call_command('migrate', 'skills', target, verbosity=0)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT column_name, is_nullable, data_type "
                "FROM information_schema.columns "
                "WHERE table_name = 'skills_skill' AND column_name = 'skill_uid'"
            )
            col = cur.fetchone()
            cur.execute(
                "SELECT constraint_name, constraint_type "
                "FROM information_schema.table_constraints "
                "WHERE table_name = 'skills_skill'"
            )
            constraints = cur.fetchall()
        meta = {'skill_uid_column': col, 'constraints': constraints}
        print('---BEGIN---')
        print(json.dumps(meta, default=str))
        print('---END---')
    finally:
        teardown_databases(old_config, verbosity=0)
    """
).strip()


def _run_child(script_body, payload):
    proc = subprocess.run(
        [sys.executable, "-c", script_body, PROJECT_ROOT, TEST_DB_NAME],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Child migration test failed (rc={proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    out = proc.stdout
    begin = out.find("---BEGIN---")
    end = out.find("---END---")
    if begin < 0 or end < 0:
        raise RuntimeError(f"Child did not emit state markers:\n{out}")
    return json.loads(out[begin + len("---BEGIN---"):end].strip())


class SkillUidMigrationStep1Tests(SimpleTestCase):
    def test_step1_column_is_nullable_uuid(self):
        state = _run_child(_CHILD_FIELD_META, {"target_migration": MIGRATION_NULLABLE})
        col = state["skill_uid_column"]
        self.assertIsNotNone(col, "skill_uid column missing at step 1")
        col_name, is_nullable, data_type = col
        self.assertEqual(col_name, "skill_uid")
        self.assertEqual(is_nullable, "YES")
        self.assertEqual(data_type, "uuid")

    def test_step1_field_is_not_unique(self):
        state = _run_child(_CHILD_FIELD_META, {"target_migration": MIGRATION_NULLABLE})
        for c in state["constraints"]:
            self.assertNotIn("skill_uid", str(c).lower(),
                             f"Unexpected unique constraint at step 1: {c}")


class SkillUidMigrationStep2Tests(SimpleTestCase):
    def test_step2_assigns_registry_uuid_to_python(self):
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": "Python", "slug": "python",
                     "category": "programming_language"}
                ],
            },
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(str(rows[0]["skill_uid"]), str(get_skill_uid("Python")))

    def test_step2_generates_uuid_for_orphan_row(self):
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": "Legacy Orphan Skill",
                     "slug": "legacy-orphan-skill", "category": "other"}
                ],
            },
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 1)
        self.assertFalse(has_skill_uid("Legacy Orphan Skill"))
        u = uuid.UUID(rows[0]["skill_uid"])
        self.assertEqual(u.version, 4)

    def test_step2_assigns_unique_uuids_to_mixed_rows(self):
        rows_to_insert = [
            {"canonical_name": n, "slug": n.lower().replace(" ", "-"),
             "category": "other"}
            for n in ["Python", "PostgreSQL", "Legacy Orphan A", "Legacy Orphan B"]
        ]
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {"target_migration": MIGRATION_POPULATE, "insert_rows": rows_to_insert},
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 4)
        uuids = [str(r["skill_uid"]) for r in rows]
        self.assertEqual(len(set(uuids)), 4)
        for r in rows:
            u = uuid.UUID(r["skill_uid"])
            self.assertEqual(u.version, 4)


class SkillUidMigrationStep3Tests(SimpleTestCase):
    def test_step3_column_is_non_null_unique(self):
        state = _run_child(_CHILD_FIELD_META, {"target_migration": MIGRATION_FINALIZE})
        col = state["skill_uid_column"]
        col_name, is_nullable, data_type = col
        self.assertEqual(col_name, "skill_uid")
        self.assertEqual(is_nullable, "NO")
        self.assertEqual(data_type, "uuid")
        unique_constraints = [
            c for c in state["constraints"]
            if "UNIQUE" in str(c).upper() and "skill_uid" in str(c).lower()
        ]
        self.assertGreater(
            len(unique_constraints), 0,
            f"No UNIQUE constraint found on skill_uid at step 3: {state['constraints']}",
        )

    def test_step3_field_has_default(self):
        from apps.skills.models import Skill
        field = Skill._meta.get_field("skill_uid")
        self.assertIsNotNone(field.default)
        self.assertFalse(field.editable)
        self.assertTrue(field.unique)
        self.assertFalse(field.null)
