#!/usr/bin/env python
"""
Strict ORM Model Verification Audit against database/migrations/001_initial_schema.sql

This script inspects Base.metadata and compares against the migration.
No database connection, no DDL execution.
"""

import re
import sys
from typing import Dict, List, Tuple, Any
from sqlalchemy import inspect
from app.db.models import Base


def parse_migration() -> Dict[str, Dict]:
    """Parse the SQL migration to extract expected schema."""
    migration_path = "../database/migrations/001_initial_schema.sql"
    with open(migration_path, "r") as f:
        sql = f.read()

    tables = {}
    current_table = None
    in_create = False

    for line in sql.split("\n"):
        line = line.strip()

        # Table start
        if line.startswith("CREATE TABLE"):
            match = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', line)
            if match:
                current_table = match.group(1)
                tables[current_table] = {
                    "columns": {},
                    "indexes": [],
                    "unique_constraints": [],
                    "foreign_keys": [],
                    "primary_key": None,
                }
                in_create = True
                continue

        if not current_table or not in_create:
            continue

        # End of table
        if line.startswith(");"):
            current_table = None
            in_create = False
            continue

        # Primary key
        if "PRIMARY KEY" in line and "id UUID PRIMARY KEY" in line:
            tables[current_table]["primary_key"] = "id"

        # Columns
        col_match = re.match(r'^(\w+)\s+(\w+(?:\([^)]+\))?)\s*(.*)$', line.rstrip(","))
        if col_match and not line.startswith("--"):
            col_name, col_type, rest = col_match.groups()
            if col_name in ("CONSTRAINT", "CREATE", "INDEX", "UNIQUE", "PRIMARY"):
                continue

            # Standardize common types for comparison
            norm_type = col_type.upper().replace("DECIMAL", "NUMERIC").replace("TIMESTAMPTZ", "DATETIME").replace("INT", "INTEGER")
            
            # PRIMARY KEY implies NOT NULL
            nullable = ("NOT NULL" not in rest) and ("PRIMARY KEY" not in rest)
            
            default = None
            if "DEFAULT" in rest:
                default_match = re.search(r"DEFAULT\s+([^,\s]+)", rest)
                if default_match:
                    default = default_match.group(1)

            unique = "UNIQUE" in rest and "PRIMARY KEY" not in rest

            tables[current_table]["columns"][col_name] = {
                "type": norm_type,
                "nullable": nullable,
                "default": default,
                "unique": unique,
            }

        # Unique constraints
        if "CONSTRAINT" in line and "UNIQUE" in line:
            match = re.search(r'CONSTRAINT\s+(\w+)\s+UNIQUE\s*\(([^)]+)\)', line)
            if match:
                constraint_name = match.group(1)
                cols = [c.strip() for c in match.group(2).split(",")]
                tables[current_table]["unique_constraints"].append({
                    "name": constraint_name,
                    "columns": cols,
                })

        # Foreign keys
        if "REFERENCES" in line:
            match = re.search(r'(\w+)\s+UUID\s+REFERENCES\s+(\w+)\(id\)\s+ON\s+DELETE\s+(SET NULL|CASCADE|RESTRICT)', line)
            if match:
                col_name, ref_table, on_delete = match.groups()
                tables[current_table]["foreign_keys"].append({
                    "column": col_name,
                    "references": f"{ref_table}.id",
                    "on_delete": on_delete,
                })

    # Parse explicit indexes
    for line in sql.split("\n"):
        line = line.strip()
        if line.startswith("CREATE INDEX"):
            match = re.search(r'CREATE INDEX\s+(\w+)\s+ON\s+(\w+)\s*\(([^)]+)\)', line)
            if match:
                idx_name, table_name, cols = match.groups()
                if table_name in tables:
                    tables[table_name]["indexes"].append({
                        "name": idx_name,
                        "columns": [c.strip().split()[0] for c in cols.split(",")],
                    })

    return tables


def inspect_orm() -> Dict[str, Dict]:
    """Inspect SQLAlchemy Base.metadata."""
    orm_data = {}
    for table_name, table in Base.metadata.tables.items():
        cols = {}
        for col in table.columns:
            # Standardize ORM types
            orm_type = str(col.type).upper().replace("DECIMAL", "NUMERIC").replace("DATETIME", "DATETIME").replace("VARCHAR", "STRING").replace("INTEGER", "INTEGER")
            if "(" in orm_type and "STRING" in orm_type:
                orm_type = orm_type.replace("STRING", "VARCHAR")

            cols[col.name] = {
                "type": orm_type,
                "nullable": col.nullable,
                "default": str(col.default) if col.default else None,
                "primary_key": col.primary_key,
                "unique": col.unique,
            }

        indexes = []
        for idx in table.indexes:
            indexes.append({
                "name": idx.name,
                "columns": [c.name for c in idx.columns],
            })

        unique_constraints = []
        for constraint in table.constraints:
            if constraint.__class__.__name__ == "UniqueConstraint":
                cols_list = [c.name for c in constraint.columns]
                unique_constraints.append({
                    "name": constraint.name,
                    "columns": cols_list,
                })

        foreign_keys = []
        for fk in table.foreign_keys:
            foreign_keys.append({
                "column": fk.parent.name,
                "references": fk.target_fullname,
                "on_delete": fk.ondelete,
            })

        orm_data[table_name] = {
            "columns": cols,
            "indexes": indexes,
            "unique_constraints": unique_constraints,
            "foreign_keys": foreign_keys,
        }

    return orm_data


def compare_schemas(migration: Dict, orm: Dict) -> List[str]:
    """Compare migration schema with ORM metadata."""
    mismatches = []
    all_tables = set(migration.keys()) | set(orm.keys())

    for table in sorted(all_tables):
        m = migration.get(table, {})
        o = orm.get(table, {})

        if table not in migration:
            mismatches.append(f"❌ Table {table}: IN ORM but NOT in migration")
            continue
        if table not in orm:
            mismatches.append(f"❌ Table {table}: IN MIGRATION but NOT in ORM")
            continue

        # Column comparison
        m_cols = m.get("columns", {})
        o_cols = o.get("columns", {})
        all_cols_set = set(m_cols.keys()) | set(o_cols.keys())

        for col in sorted(all_cols_set):
            mc = m_cols.get(col)
            oc = o_cols.get(col)

            if mc and not oc:
                mismatches.append(f"❌ {table}.{col}: In migration but missing from ORM")
                continue
            if oc and not mc:
                mismatches.append(f"❌ {table}.{col}: In ORM but missing from migration")
                continue

            m_type = mc["type"]
            o_type = oc["type"]
            
            # Rough normalization for comparison
            if m_type == "UUID" and "UUID" in o_type:
                pass
            elif ("STRING" in o_type or "VARCHAR" in o_type) and "VARCHAR" in m_type:
                # Check length match
                m_len = re.search(r'\((\d+)\)', m_type)
                o_len = re.search(r'\((\d+)\)', o_type)
                if m_len and o_len:
                    if m_len.group(1) != o_len.group(1):
                        mismatches.append(f"⚠️  {table}.{col}: Length mismatch — migration={m_type}, orm={o_type}")
                elif m_len and not o_len:
                    mismatches.append(f"⚠️  {table}.{col}: Length missing in ORM — migration={m_type}, orm={o_type}")
            elif m_type != o_type:
                if m_type == "JSONB" and "JSONB" in o_type:
                    pass
                elif m_type == "TEXT" and "TEXT" in o_type:
                    pass
                else:
                    mismatches.append(f"⚠️  {table}.{col}: Type mismatch — migration={m_type}, orm={o_type}")

            if mc["nullable"] != oc["nullable"]:
                mismatches.append(f"⚠️  {table}.{col}: Nullable mismatch — migration={'NULL' if mc['nullable'] else 'NOT NULL'}, orm={'NULL' if oc['nullable'] else 'NOT NULL'}")

            # Check primary key
            if col == "id" and not oc.get("primary_key"):
                mismatches.append(f"❌ {table}.id: Not marked as primary key in ORM")

        # Index comparison
        m_indexes = {idx["name"]: idx for idx in m.get("indexes", [])}
        o_indexes = {idx["name"]: idx for idx in o.get("indexes", [])}

        for idx_name in sorted(set(m_indexes.keys()) | set(o_indexes.keys())):
            mi = m_indexes.get(idx_name)
            oi = o_indexes.get(idx_name)

            if mi and not oi:
                mismatches.append(f"❌ Index {idx_name} on {table}: In migration but missing from ORM")
            elif oi and not mi:
                mismatches.append(f"❌ Index {idx_name} on {table}: In ORM but missing from migration")
            else:
                m_cols_list = mi["columns"]
                o_cols_list = oi["columns"]
                if m_cols_list != o_cols_list:
                    mismatches.append(f"⚠️  Index {idx_name} on {table}: Columns mismatch — migration={m_cols_list}, orm={o_cols_list}")

        # Foreign keys
        m_fks = {(fk["column"], fk["references"]): fk for fk in m.get("foreign_keys", [])}
        o_fks = {(fk["column"], fk["references"]): fk for fk in o.get("foreign_keys", [])}

        for key in sorted(set(m_fks.keys()) | set(o_fks.keys())):
            mf = m_fks.get(key)
            of = o_fks.get(key)

            if mf and not of:
                mismatches.append(f"❌ FK {key[0]} -> {key[1]} on {table}: In migration but missing from ORM")
            elif of and not mf:
                mismatches.append(f"❌ FK {key[0]} -> {key[1]} on {table}: In ORM but missing from migration")
            else:
                m_del = mf.get("on_delete")
                o_del = of.get("on_delete")
                if m_del and o_del and m_del.upper() != o_del.upper():
                    mismatches.append(f"⚠️  FK {key[0]} -> {key[1]} on {table}: ON DELETE mismatch — migration={m_del}, orm={o_del}")

    return mismatches


def main():
    print("=" * 80)
    print("ORM MODEL VERIFICATION AUDIT")
    print("=" * 80)

    try:
        migration = parse_migration()
        orm = inspect_orm()
    except Exception as e:
        print(f"ERROR during inspection: {e}")
        import traceback
        traceback.print_exc()
        return False

    mismatches = compare_schemas(migration, orm)

    print(f"\nTables in migration: {len(migration)}")
    print(f"Tables in ORM: {len(orm)}")
    print(f"Mismatches found: {len(mismatches)}")
    print()

    if mismatches:
        print("MISMATCHES:")
        print("-" * 80)
        for m in mismatches:
            print(m)
    else:
        print("✅ ALL CHECKS PASSED — No mismatches found")

    return len(mismatches) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)