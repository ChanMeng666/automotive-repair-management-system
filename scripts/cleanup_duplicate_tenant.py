"""
One-time cleanup script for Neon production database.
Truncates ALL tables (all data is test data) and resets sequences to 1.

Usage:
    DATABASE_URL=<neon_url> python scripts/cleanup_duplicate_tenant.py

Or set DATABASE_URL in your environment / .env file.
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    return psycopg2.connect(url)


# Delete order: children first, parents last (respects foreign keys)
ALL_TABLES = [
    "inventory_transaction",
    "inventory",
    "job_service",
    "job_part",
    "job",
    "service",
    "part",
    "customer",
    "subscription",
    "tenant_membership",
    "tenant",
    '"user"',  # quoted — "user" is a reserved word in PostgreSQL
]

def main():
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print("=== Full Database Cleanup (all test data) ===\n")

        # 1. Show current state
        print("Current row counts:")
        for table in ALL_TABLES:
            cur.execute(f"SELECT count(*) FROM {table}")
            label = table.strip('"')
            print(f"  {label}: {cur.fetchone()[0]} rows")
        print()

        # 2. Delete all rows (child tables first)
        print("Deleting all rows...")
        for table in ALL_TABLES:
            cur.execute(f"DELETE FROM {table}")
            label = table.strip('"')
            print(f"  {label}: deleted {cur.rowcount} rows")

        # 3. Reset serial/identity columns to 1
        print("\nResetting ID counters...")
        serial_tables = [
            ("tenant", "tenant_id"),
            ("tenant_membership", "id"),
            ("subscription", "id"),
            ("user", "user_id"),
            ("customer", "customer_id"),
            ("job", "job_id"),
            ("service", "service_id"),
            ("part", "part_id"),
            ("inventory", "inventory_id"),
            ("inventory_transaction", "transaction_id"),
        ]
        for table, col in serial_tables:
            # Find the sequence backing this column
            label = table.strip('"')
            cur.execute(
                f"SELECT pg_get_serial_sequence('{label}', '{col}')"
            )
            row = cur.fetchone()
            if row and row[0]:
                cur.execute(f"SELECT setval('{row[0]}', 1, false)")
                print(f"  {label}.{col} -> next value = 1")
            else:
                print(f"  {label}.{col} -> no sequence found (skipped)")

        # 5. Verify
        print("\n=== Final State ===")
        for table in ALL_TABLES:
            cur.execute(f"SELECT count(*) FROM {table}")
            label = table.strip('"')
            print(f"  {label}: {cur.fetchone()[0]} rows")

        # Confirm
        response = input("\nCommit? This will DELETE ALL DATA. [y/N]: ").strip().lower()
        if response == "y":
            conn.commit()
            print("Done. Database is clean.")
        else:
            conn.rollback()
            print("Rolled back — no changes made.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
