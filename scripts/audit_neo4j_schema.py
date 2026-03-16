#!/usr/bin/env python3
"""
Neo4j Schema & Status Audit
Connects to Neo4j, runs diagnostic Cypher, outputs docs/architecture/current_neo4j_state.md

Usage:
  python scripts/audit_neo4j_schema.py

Requires:
  - Neo4j running (docker-compose up -d)
  - neo4j Python package (pip install neo4j)

Env overrides: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "docs" / "architecture" / "current_neo4j_state.md"

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "daoistpassword")


def run_query(session, cypher, params=None):
    """Execute Cypher and return list of records (as dicts)."""
    result = session.run(cypher, params or {})
    keys = result.keys()
    return [dict(zip(keys, record.values())) for record in result]


def audit(driver):
    sections = []
    with driver.session() as session:
        # --- Schema visualization ---
        sections.append("## 1. Schema Visualization")
        sections.append("")
        try:
            result = run_query(session, "CALL db.schema.visualization()")
            if result:
                r = result[0]
                nodes = r.get("nodes", [])
                relationships = r.get("relationships", [])
                if nodes:
                    sections.append("**Schema nodes (from db.schema.visualization):**")
                    for n in nodes:
                        sections.append(f"- `{n}`")
                    sections.append("")
                if relationships:
                    sections.append("**Schema relationships:**")
                    for rel in relationships:
                        sections.append(f"- `{rel}`")
                else:
                    sections.append("_No relationships in schema visualization._")
            else:
                sections.append("_No schema data returned._")
        except Exception as e:
            sections.append(f"_Error: {e}_")
        sections.append("")

        # --- Node labels ---
        sections.append("## 2. Node Labels")
        sections.append("")
        try:
            result = run_query(session, "CALL db.labels()")
            if result:
                labels = [r.get("label", r.get(list(r.keys())[0])) for r in result]
            else:
                result = run_query(session, "MATCH (n) UNWIND labels(n) AS lbl RETURN DISTINCT lbl")
                labels = [r["lbl"] for r in result]
            sections.append("| Label |")
            sections.append("|-------|")
            for lbl in sorted(labels):
                sections.append(f"| `{lbl}` |")
        except Exception as e:
            sections.append(f"_Error: {e}_")
        sections.append("")

        # --- Relationship types ---
        sections.append("## 3. Relationship Types")
        sections.append("")
        try:
            result = run_query(session, "CALL db.relationshipTypes()")
            if result:
                rel_types = [r.get("relationshipType", r.get(list(r.keys())[0])) for r in result]
            else:
                result = run_query(session, "MATCH ()-[r]->() RETURN DISTINCT type(r) AS rt")
                rel_types = [r["rt"] for r in result]
            sections.append("| Relationship Type |")
            sections.append("|-------------------|")
            for rt in sorted(rel_types):
                sections.append(f"| `{rt}` |")
        except Exception as e:
            sections.append(f"_Error: {e}_")
        sections.append("")

        # --- Property mapping (sample node per label) ---
        sections.append("## 4. Property Mapping (Sample Node per Label)")
        sections.append("")
        labels = []
        try:
            r = run_query(session, "CALL db.labels()")
            labels = [x.get("label", list(x.values())[0]) for x in r] if r else []
        except Exception:
            r = run_query(session, "MATCH (n) UNWIND labels(n) AS lbl RETURN DISTINCT lbl")
            labels = [x["lbl"] for x in r]

        for label in sorted(labels):
            try:
                result = run_query(
                    session,
                    f"MATCH (n:`{label}`) RETURN n LIMIT 1"
                )
                if result and "n" in result[0]:
                    node = result[0]["n"]
                    props = dict(node)
                    prop_list = ", ".join(f"`{k}`" for k in sorted(props.keys()))
                    sections.append(f"### {label}")
                    sections.append(f"- **Properties:** {prop_list}")
                    if props:
                        sections.append("- **Sample values:**")
                        for k, v in sorted(props.items()):
                            vstr = repr(v)[:80] + ("..." if len(repr(v)) > 80 else "")
                            sections.append(f"  - `{k}`: {vstr}")
                    sections.append("")
            except Exception as e:
                sections.append(f"### {label}")
                sections.append(f"_Error: {e}_")
                sections.append("")

        # --- Constraints ---
        sections.append("## 5. Constraints")
        sections.append("")
        try:
            result = run_query(session, "SHOW CONSTRAINTS YIELD *")
            if result:
                sections.append("| Name | Type | Entity | Labels/Type | Properties |")
                sections.append("|------|------|--------|--------------|------------|")
                for r in result:
                    name = r.get("name", r.get("id", ""))
                    ctype = r.get("type", "")
                    entity = r.get("entityType", "")
                    labels_or_type = r.get("labelsOrTypes", "")
                    props = r.get("properties", "")
                    sections.append(f"| {name} | {ctype} | {entity} | {labels_or_type} | {props} |")
            else:
                sections.append("_No constraints defined._")
        except Exception as e:
            sections.append(f"_Error: {e}_")
        sections.append("")

        # --- Indexes ---
        sections.append("## 6. Indexes")
        sections.append("")
        try:
            result = run_query(session, "SHOW INDEXES YIELD *")
            if result:
                sections.append("| Name | State | Type | Entity | Labels/Type | Properties |")
                sections.append("|------|-------|------|--------|--------------|------------|")
                for r in result:
                    name = r.get("name", r.get("id", ""))
                    state = r.get("state", "")
                    idx_type = r.get("type", "")
                    entity = r.get("entityType", "")
                    labels_or_type = r.get("labelsOrTypes", "")
                    props = r.get("properties", "")
                    sections.append(f"| {name} | {state} | {idx_type} | {entity} | {labels_or_type} | {props} |")
            else:
                sections.append("_No indexes defined (or none beyond constraints)._")
        except Exception as e:
            sections.append(f"_Error: {e}_")
        sections.append("")

        # --- Volume audit ---
        sections.append("## 7. Volume Audit")
        sections.append("")
        sections.append("### Nodes per Label")
        sections.append("")
        sections.append("| Label | Count |")
        sections.append("|-------|-------|")
        for label in sorted(labels):
            try:
                r = run_query(session, f"MATCH (n:`{label}`) RETURN count(n) AS c")
                count = r[0]["c"] if r else 0
                sections.append(f"| `{label}` | {count} |")
            except Exception as e:
                sections.append(f"| `{label}` | _Error: {e}_ |")

        sections.append("")
        sections.append("### Relationships per Type")
        sections.append("")
        rel_types = []
        try:
            r = run_query(session, "CALL db.relationshipTypes()")
            rel_types = [x.get("relationshipType", list(x.values())[0]) for x in r] if r else []
        except Exception:
            r = run_query(session, "MATCH ()-[r]->() RETURN DISTINCT type(r) AS rt")
            rel_types = [x["rt"] for x in r]

        sections.append("| Relationship Type | Count |")
        sections.append("|-------------------|-------|")
        for rt in sorted(rel_types):
            try:
                r = run_query(session, f"MATCH ()-[r:`{rt}`]->() RETURN count(r) AS c")
                count = r[0]["c"] if r else 0
                sections.append(f"| `{rt}` | {count} |")
            except Exception as e:
                sections.append(f"| `{rt}` | _Error: {e}_ |")

    return "\n".join(sections)


def main():
    header = """# Neo4j Schema & Status — Current State

**Generated by:** `scripts/audit_neo4j_schema.py`  
**Last run:** {date}  
**Purpose:** Structural blueprint for CTO/LLM context — exact graph topology of the database.

**Connection:** `{uri}` (use `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` to override)

---

""".format(uri=URI, date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"Cannot connect to Neo4j at {URI}: {e}")
        print("Ensure Docker is running and run: docker-compose up -d")
        # Write placeholder so CTO knows the audit exists but needs Neo4j
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        placeholder = header + """
## ⚠️ Neo4j Unavailable

This audit could not be completed because Neo4j was not reachable.

**To generate the full audit:**
```bash
docker-compose up -d   # Start Neo4j
python scripts/audit_neo4j_schema.py
```

Expected schema (from `08_build_graph.py`): **Herb**, **Formula**, **Meridian** nodes; **ENTERS**, **INCLUDED_IN** relationships.
"""
        OUTPUT_PATH.write_text(placeholder, encoding="utf-8")
        print(f"Wrote placeholder to {OUTPUT_PATH}")
        return 1

    try:
        body = audit(driver)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(header + body, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH}")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
