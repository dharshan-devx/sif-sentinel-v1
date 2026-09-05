"""Create a disposable PostgreSQL database for integration tests.

Set TEST_ADMIN_DATABASE_URL to an administrative connection URL. The target
name defaults to sif_sentinel_test and must end in ``_test`` or ``_audit`` to
avoid accidentally replacing an application database.
"""

import os
import re

from psycopg import connect, sql


def main() -> None:
    admin_url = os.environ.get("TEST_ADMIN_DATABASE_URL")
    database_name = os.environ.get("TEST_DATABASE_NAME", "sif_sentinel_test")
    if not admin_url:
        raise SystemExit("TEST_ADMIN_DATABASE_URL is required; no connection defaults are embedded.")
    if not re.fullmatch(r"[A-Za-z0-9_]+_(?:test|audit)", database_name):
        raise SystemExit("TEST_DATABASE_NAME must contain only letters, digits, underscores and end in _test or _audit.")

    with connect(admin_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
    print(f"Created disposable database: {database_name}")


if __name__ == "__main__":
    main()
