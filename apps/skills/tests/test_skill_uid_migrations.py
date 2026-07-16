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
from django.db import connection
from django.test import SimpleTestCase, TransactionTestCase

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

    def test_step2_assigns_unique_uuids_to_mixed_rows(self):
        rows_to_insert = [
            {"canonical_name": n, "slug": n.lower().replace(" ", "-"),
             "category": "other"}
            for n in ["Python", "PostgreSQL"]
        ]
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {"target_migration": MIGRATION_POPULATE, "insert_rows": rows_to_insert},
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 2)
        uuids = [str(r["skill_uid"]) for r in rows]
        self.assertEqual(len(set(uuids)), 2)
        for r in rows:
            u = uuid.UUID(r["skill_uid"])
            self.assertEqual(u.version, 4)

    def test_step2_legacy_dotnet_old_only_receives_target_uuid(self):
        # Legacy ``.NET Core`` row exists, registry target ``.NET``
        # does not: the old row gets the target registry UUID. A
        # later in-place rename preserves that UUID.
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": ".NET Core", "slug": "dotnet-core",
                     "category": "backend"},
                ],
            },
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["canonical_name"], ".NET Core")
        self.assertEqual(
            str(rows[0]["skill_uid"]), str(get_skill_uid(".NET"))
        )

    def test_step2_legacy_dotnet_both_rows_get_distinct_uuids(self):
        # Both ``.NET Core`` and ``.NET`` exist: the target gets the
        # registry UUID, the legacy old row gets the fixed tombstone
        # UUID. No random generation.
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": ".NET Core", "slug": "dotnet-core",
                     "category": "backend"},
                    {"canonical_name": ".NET", "slug": "dotnet",
                     "category": "backend"},
                ],
            },
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 2)
        by_name = {r["canonical_name"]: r for r in rows}
        self.assertEqual(
            str(by_name[".NET"]["skill_uid"]),
            str(get_skill_uid(".NET")),
        )
        self.assertEqual(
            str(by_name[".NET Core"]["skill_uid"]),
            "23b14296-d0ce-4897-a7fc-1489331f86de",
        )
        # The two UUIDs are distinct
        self.assertNotEqual(
            by_name[".NET"]["skill_uid"], by_name[".NET Core"]["skill_uid"]
        )

    def test_step2_legacy_aspnet_old_only_receives_target_uuid(self):
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": "ASP.NET", "slug": "aspdotnet",
                     "category": "backend"},
                ],
            },
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["canonical_name"], "ASP.NET")
        self.assertEqual(
            str(rows[0]["skill_uid"]), str(get_skill_uid("ASP.NET Core"))
        )

    def test_step2_aborts_on_unknown_active_row(self):
        # An unknown active row must abort the migration with a
        # concise ``RuntimeError`` listing canonical names and
        # active/inactive state. No random UUIDv4 generation.
        result = subprocess.run(
            [sys.executable, "-c", _CHILD_RUN_AND_DUMP, PROJECT_ROOT, TEST_DB_NAME],
            input=json.dumps({
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": "Python", "slug": "python",
                     "category": "programming_language"},
                    {"canonical_name": "Unknown Active Skill",
                     "slug": "unknown-active", "category": "other"},
                ],
            }),
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        # The migration aborted with a non-zero return code
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Migration aborted", result.stderr)
        self.assertIn("Unknown Active Skill", result.stderr)
        self.assertIn("active", result.stderr)

    def test_step2_aborts_on_unknown_inactive_row(self):
        result = subprocess.run(
            [sys.executable, "-c", _CHILD_RUN_AND_DUMP, PROJECT_ROOT, TEST_DB_NAME],
            input=json.dumps({
                "target_migration": MIGRATION_POPULATE,
                "insert_rows": [
                    {"canonical_name": "Python", "slug": "python",
                     "category": "programming_language"},
                    {"canonical_name": "Unknown Inactive Skill",
                     "slug": "unknown-inactive", "category": "other",
                     "is_active": False},
                ],
            }),
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Migration aborted", result.stderr)
        self.assertIn("Unknown Inactive Skill", result.stderr)
        self.assertIn("inactive", result.stderr)

    def test_step2_all_finalized_uuids_are_unique_and_v4(self):
        # A realistic mix: two registry rows, two legacy-old rows
        # with the target absent, and one legacy-both scenario.
        # All resulting UUIDs must be unique and UUIDv4.
        rows_to_insert = [
            {"canonical_name": "Python", "slug": "python",
             "category": "programming_language"},
            {"canonical_name": "PostgreSQL", "slug": "postgresql",
             "category": "database"},
            {"canonical_name": ".NET Core", "slug": "dotnet-core",
             "category": "backend"},
            {"canonical_name": "ASP.NET", "slug": "aspdotnet",
             "category": "backend"},
            {"canonical_name": ".NET", "slug": "dotnet",
             "category": "backend"},
        ]
        state = _run_child(
            _CHILD_RUN_AND_DUMP,
            {"target_migration": MIGRATION_POPULATE, "insert_rows": rows_to_insert},
        )
        rows = state["rows"]
        self.assertEqual(len(rows), 5)
        uuids = [str(r["skill_uid"]) for r in rows]
        self.assertEqual(len(set(uuids)), 5)
        for u in uuids:
            self.assertEqual(uuid.UUID(u).version, 4)


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


class SkillUidMigrationReverseTests(SimpleTestCase):
    """Reverse migration must restore the prior schema."""

    def test_reverse_from_finalize_to_initial_removes_field(self):
        # Apply all four migrations on an isolated DB, then reverse
        # back to 0001_initial and verify the field is gone.
        script = textwrap.dedent("""
            import os, sys, json, django
            sys.path.insert(0, '__PROJ__')
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
            django.setup()
            from django.db import connection, connections
            DB = '__TEST_DB__'
            with connection.cursor() as cur:
                cur.execute('DROP DATABASE IF EXISTS "' + DB + '"')
                cur.execute('CREATE DATABASE "' + DB + '"')
            connection.close()
            conn = connections['default']
            conn.settings_dict['NAME'] = DB
            conn.connect()
            from django.test.utils import setup_databases, teardown_databases
            old = setup_databases(verbosity=0, interactive=False, keepdb=False)
            try:
                from django.core.management import call_command
                call_command('migrate', 'skills', '0004_skill_skill_uid_finalize', verbosity=0)
                with connection.cursor() as cur:
                    cur.execute(
                        "INSERT INTO skills_skill "
                        "(canonical_name, slug, category, is_active, source, skill_uid, created_at, updated_at) "
                        "VALUES (%s, %s, %s, %s, %s, gen_random_uuid(), NOW(), NOW())",
                        ['Python', 'python', 'programming_language', True, 'seed'],
                    )
                call_command('migrate', 'skills', '0001_initial', verbosity=0)
                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'skills_skill' AND column_name = 'skill_uid'"
                    )
                    cols = cur.fetchall()
                print('---BEGIN---')
                print(json.dumps({'skill_uid_columns': [c[0] for c in cols]}))
                print('---END---')
            finally:
                teardown_databases(old, verbosity=0)
        """).strip().replace("__PROJ__", PROJECT_ROOT).replace("__TEST_DB__", TEST_DB_NAME)
        result = subprocess.run(
            [sys.executable, "-c", script, PROJECT_ROOT, TEST_DB_NAME],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=300,
        )
        self.assertEqual(
            result.returncode, 0,
            f"Reverse migration child failed: stdout={result.stdout} stderr={result.stderr}",
        )
        out = result.stdout
        begin = out.find("---BEGIN---")
        end = out.find("---END---")
        self.assertGreaterEqual(begin, 0)
        self.assertGreater(end, begin)
        state = json.loads(out[begin + len("---BEGIN---"):end].strip())
        self.assertEqual(
            state["skill_uid_columns"], [],
            "Reverse migration must remove the skill_uid column",
        )

    def test_local_database_not_modified(self):
        # Verify the normal local development database still has no
        # skill_uid column and only the 0001 migration applied.
        # This test needs the real default database; promote it to
        # ``TransactionTestCase`` via the sibling class below.
        pass


class SkillUidMigrationLocalDatabaseChecks(TransactionTestCase):
    """Verify the normal local database is unchanged.

    The Django test runner points ``connection`` at the test
    database. We open a separate ``psycopg`` connection to the
    normal local development database to inspect its state without
    touching the test database.
    """

    def _open_local_connection(self):
        import os
        import psycopg
        from django.conf import settings as dj_settings
        db = dj_settings.DATABASES["default"]
        # Resolve the local DB name (the same one used for dev), not
        # the test DB name. ``test_tunitech_abroad`` is the test DB.
        target_name = db["NAME"]
        # If running inside a test context, the NAME is overridden
        # to test_<name>; in that case derive the local name.
        if target_name.startswith("test_"):
            target_name = target_name[len("test_"):]
        # Allow override via env for safety
        target_name = os.environ.get("TUNIATLAS_LOCAL_DB_NAME", target_name)
        conn = psycopg.connect(
            dbname=target_name,
            user=db.get("USER"),
            password=db.get("PASSWORD"),
            host=db.get("HOST", "localhost"),
            port=db.get("PORT", "5432"),
        )
        return conn, target_name

    def test_local_database_has_no_skill_uid_column(self):
        conn, _ = self._open_local_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'skills_skill' AND column_name = 'skill_uid'
                """)
                self.assertIsNone(
                    cur.fetchone(),
                    "Normal local database must not have skill_uid column",
                )
        finally:
            conn.close()

    def test_local_database_only_has_initial_migration(self):
        conn, _ = self._open_local_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name FROM django_migrations
                    WHERE app = 'skills'
                    ORDER BY id
                """)
                applied = [r[0] for r in cur.fetchall()]
            self.assertEqual(applied, ["0001_initial"])
        finally:
            conn.close()
