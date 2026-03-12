#!/usr/bin/env python3
"""
Phase 6: Graph Database Foundation.
Ingest seed_herbs.json and seed_formulas.json into Neo4j.
"""

import json
from pathlib import Path

from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HERBS_PATH = PROJECT_ROOT / "data" / "output" / "seed_herbs.json"
FORMULAS_PATH = PROJECT_ROOT / "data" / "output" / "seed_formulas.json"
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "daoistpassword")


def _normalize_pinyin(s: str) -> str:
    """Remove spaces and lowercase for matching (Bai Shao -> baishao)."""
    if not s:
        return ""
    return "".join(s.lower().split())


def run(driver):
    with driver.session() as session:
        # Constraints
        for stmt in [
            "CREATE CONSTRAINT herb_id_unique IF NOT EXISTS FOR (h:Herb) REQUIRE h.id IS UNIQUE",
            "CREATE CONSTRAINT formula_id_unique IF NOT EXISTS FOR (f:Formula) REQUIRE f.id IS UNIQUE",
        ]:
            try:
                session.run(stmt)
            except Exception:
                pass  # Constraint may already exist

        # Ingest herbs
        with open(HERBS_PATH, encoding="utf-8") as f:
            herbs = json.load(f)
        for h in herbs:
            pid = h.get("id", "")
            pinyin = h.get("pinyin_name", "")
            english = h.get("english_name", "")
            tier = h.get("safety_tier", 1)
            norm = _normalize_pinyin(pinyin)
            session.run(
                """
                MERGE (h:Herb {id: $id})
                SET h.pinyin = $pinyin, h.english = $english, h.safety_tier = $tier, h.pinyin_normalized = $norm
                """,
                id=pid,
                pinyin=pinyin,
                english=english,
                tier=int(tier),
                norm=norm,
            )
            for m_name in h.get("meridians", []):
                if m_name:
                    session.run(
                        """
                        MERGE (m:Meridian {name: $name})
                        WITH m
                        MATCH (h:Herb {id: $herb_id})
                        MERGE (h)-[:ENTERS]->(m)
                        """,
                        name=m_name.strip(),
                        herb_id=pid,
                    )

        # Ingest formulas
        with open(FORMULAS_PATH, encoding="utf-8") as f:
            formulas = json.load(f)
        for f in formulas:
            fid = f.get("id", "")
            pinyin = f.get("pinyin_name", "")
            english = f.get("english_name", "")
            pattern = f.get("primary_pattern", "")
            session.run(
                """
                MERGE (f:Formula {id: $id})
                SET f.pinyin = $pinyin, f.english = $english, f.pattern = $pattern
                """,
                id=fid,
                pinyin=pinyin,
                english=english,
                pattern=pattern,
            )
            for arch in f.get("architecture", []):
                herb_pinyin = arch.get("herb_pinyin", "")
                role = arch.get("role", "")
                dosage = arch.get("classical_dosage", "")
                norm = _normalize_pinyin(herb_pinyin)
                if not norm:
                    continue
                result = session.run(
                    """
                    MATCH (h:Herb {pinyin_normalized: $norm})
                    MATCH (f:Formula {id: $formula_id})
                    MERGE (h)-[r:INCLUDED_IN]->(f)
                    SET r.role = $role, r.dosage = $dosage
                    """,
                    norm=norm,
                    formula_id=fid,
                    role=role,
                    dosage=dosage,
                )
                result.consume()


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"Cannot connect to Neo4j at {URI}: {e}")
        print("Ensure Docker is running and run: docker-compose up -d")
        return 1
    try:
        run(driver)
        print("Phase 6 complete. Open http://localhost:7474 to view the graph.")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
