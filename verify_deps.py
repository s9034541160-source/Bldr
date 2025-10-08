#!/usr/bin/env python3
# verify_deps.py
# Проверяет: expected deps (из sequences.json) vs реальные рёбра в Neo4j и points в Qdrant.
# Neo4j: neo4j://127.0.0.1:7687, user=neo4j, pass=neopassword
# Qdrant: http://localhost:6333, collection=enterprise_docs

import sys
import json
import argparse
import requests
from neo4j import GraphDatabase

# Конфиг — правьте при необходимости
DEFAULTS = {
    "seq_file": None,  # если None — нужно указать в аргументах
    "neo4j_uri": "neo4j://127.0.0.1:7687",
    "neo4j_user": "neo4j",
    "neo4j_pass": "neopassword",
    "qdrant_url": "http://localhost:6333",
    "qdrant_collection": "enterprise_docs",
    "tolerance_pct": 3.0,  # допустимая погрешность в процентах
}

def load_sequences(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # data is expected to be list of items; each item may have 'deps' (list)
    if isinstance(data, dict):
        # sometimes file may wrap under 'sequences'
        if "sequences" in data and isinstance(data["sequences"], list):
            data = data["sequences"]
    if not isinstance(data, list):
        raise ValueError("Не удалось распознать файл: ожидается список последовательностей (JSON).")
    return data

def compute_expected_deps(sequences):
    total_deps = 0
    total_works = len(sequences)
    for idx, item in enumerate(sequences):
        deps = item.get("deps") or item.get("dependencies") or []
        if not isinstance(deps, list):
            # если deps содержатся как строка или другое - нормализуем
            try:
                deps = list(deps)
            except:
                deps = []
        total_deps += len(deps)
    return total_works, total_deps

def check_qdrant_points(qdrant_url, collection):
    base = qdrant_url.rstrip('/')
    # prefer /collections/<c>/points/count
    try:
        r = requests.get(f"{base}/collections/{collection}/points/count", timeout=6)
        if r.ok:
            j = r.json()
            cnt = j.get("result", {}).get("count", j.get("count"))
            return int(cnt) if cnt is not None else None
    except Exception:
        pass
    # fallback: GET /collections/<c>
    try:
        r = requests.get(f"{base}/collections/{collection}", timeout=6)
        if r.ok:
            j = r.json()
            # try common fields
            cnt = None
            if isinstance(j, dict):
                cnt = j.get("result", {}).get("points_count") or j.get("result", {}).get("points") or j.get("result", {}).get("count")
            return int(cnt) if cnt is not None else None
    except Exception:
        pass
    # final fallback: scroll limit=1 and try to read collection metadata separately
    try:
        r = requests.post(f"{base}/collections/{collection}/points/scroll", json={"limit":1}, timeout=6)
        if r.ok:
            # can't infer total count reliably here
            return None
    except Exception:
        pass
    return None

def check_neo4j(neo4j_uri, user, password):
    drv = GraphDatabase.driver(neo4j_uri, auth=(user, password))
    info = {}
    try:
        with drv.session() as s:
            # total relationships
            rec = s.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()
            info["total_rels"] = int(rec["rels"]) if rec and rec["rels"] is not None else 0

            # rels by type
            recs = s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS c ORDER BY c DESC").data()
            info["rels_by_type"] = {r["t"]: int(r["c"]) for r in recs}

            # count Work nodes
            rec = s.run("MATCH (w:Work) RETURN count(w) AS works").single()
            info["work_nodes"] = int(rec["works"]) if rec and rec["works"] is not None else 0

            # count Document nodes
            rec = s.run("MATCH (d:Document) RETURN count(d) AS docs").single()
            info["doc_nodes"] = int(rec["docs"]) if rec and rec["docs"] is not None else 0

            # dependency rels explicitly (PRECEDES or DEPENDS_ON)
            rec = s.run("MATCH ()-[r:PRECEDES|DEPENDS_ON]->() RETURN count(r) AS deps").single()
            info["dependency_rels"] = int(rec["deps"]) if rec and rec["deps"] is not None else 0
    finally:
        drv.close()
    return info

def evaluate(expected_deps, neo_info, qdrant_points, tolerance_pct):
    report = {}
    report["expected_deps"] = expected_deps
    report["neo_total_rels"] = neo_info.get("total_rels", 0)
    report["neo_rels_by_type"] = neo_info.get("rels_by_type", {})
    report["neo_work_nodes"] = neo_info.get("work_nodes", 0)
    report["qdrant_points"] = qdrant_points

    # identify CONTAINS count if present (case sensitive)
    contains_count = 0
    for k,v in report["neo_rels_by_type"].items():
        if k.upper() == "CONTAINS":
            contains_count = v
            break
    report["contains_rels"] = contains_count

    # Prefer explicit dependency rel count if available
    dependency_rels = neo_info.get("dependency_rels")
    if dependency_rels is None:
        # fallback: assume deps = total - contains
        dependency_rels = report["neo_total_rels"] - contains_count
    report["dependency_rels"] = dependency_rels

    # compare expected_deps vs dependency_rels
    if expected_deps == 0 and dependency_rels == 0:
        ok = True
        msg = "Ожидаемых зависимостей и реальных зависимостей в БД — 0 (OK)."
    else:
        # relative difference
        if expected_deps == 0:
            ok = dependency_rels == 0
            diff_pct = 100.0 if dependency_rels != 0 else 0.0
        else:
            diff = abs(dependency_rels - expected_deps)
            diff_pct = (diff / expected_deps) * 100.0
            ok = diff_pct <= tolerance_pct
        msg = f"expected_deps={expected_deps}, dependency_rels_in_neo4j={dependency_rels}, diff_pct={diff_pct:.2f}% (tolerance {tolerance_pct}%)"
    report["ok"] = ok
    report["message"] = msg
    return report

def main():
    p = argparse.ArgumentParser(description="Verify dependencies from sequences.json against Neo4j and Qdrant")
    p.add_argument("--seq", "-s", default=DEFAULTS["seq_file"], help="path to sequences JSON file (required if not default)")
    p.add_argument("--neo-uri", default=DEFAULTS["neo4j_uri"])
    p.add_argument("--neo-user", default=DEFAULTS["neo4j_user"])
    p.add_argument("--neo-pass", default=DEFAULTS["neo4j_pass"])
    p.add_argument("--qdrant", default=DEFAULTS["qdrant_url"])
    p.add_argument("--qdrant-collection", default=DEFAULTS["qdrant_collection"])
    p.add_argument("--tolerance", type=float, default=DEFAULTS["tolerance_pct"])
    args = p.parse_args()

    if not args.seq:
        print("Ошибка: укажите путь к sequences JSON через --seq")
        sys.exit(2)

    try:
        sequences = load_sequences(args.seq)
    except Exception as e:
        print("Не удалось загрузить sequences JSON:", e)
        sys.exit(2)

    total_works, expected_deps = compute_expected_deps(sequences)
    print(f"Loaded sequences: works={total_works}, expected_deps(sum lengths of deps)={expected_deps}")

    # Neo4j check
    try:
        neo_info = check_neo4j(args.neo_uri, args.neo_user, args.neo_pass)
        print("Neo4j info:", neo_info)
    except Exception as e:
        print("Ошибка при обращении к Neo4j:", e)
        sys.exit(2)

    # Qdrant check
    try:
        q_cnt = check_qdrant_points(args.qdrant, args.qdrant_collection)
        print(f"Qdrant points (collection={args.qdrant_collection}): {q_cnt}")
    except Exception as e:
        print("Ошибка при обращении к Qdrant:", e)
        q_cnt = None

    report = evaluate(expected_deps, neo_info, q_cnt, args.tolerance)
    print("\n--- Summary ---")
    print(report["message"])
    print(f"Work nodes in Neo4j: {report['neo_work_nodes']}")
    print(f"Total rels in Neo4j: {report['neo_total_rels']} (contains={report['contains_rels']})")
    print(f"Dependency rels (PRECEDES|DEPENDS_ON): {report['dependency_rels']}")
    print(f"Qdrant points: {report['qdrant_points']}")

    if report["ok"]:
        print("\nRESULT: OK")
        sys.exit(0)
    else:
        print("\nRESULT: NOT OK")
        sys.exit(2)

if __name__ == "__main__":
    main()
