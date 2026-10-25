"""Record directed reachability to refund/exit POIs using the real Backend planner."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from qa_inputs import digest, load_live_map, source_commits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--map-dir", type=Path)
    args = ap.parse_args()
    root = args.project_root.resolve()
    sys.path.insert(0, str(root / "oneload-backend"))
    from app.domain.routing import plan_route

    commits = source_commits(root)
    map_, metadata = load_live_map(root, args.map_dir)
    rows = []
    for poi_id in ("poi-single-use-card-refund", "poi-exit-1"):
        target = map_.poi_by_id[poi_id]
        for node in map_.nodes:
            route = plan_route(map_, node.id, target.node_id)
            rows.append(
                {
                    "start": node.id,
                    "destination_poi_id": poi_id,
                    "reachable": route is not None,
                    "path": route.path_node_ids if route else None,
                }
            )
    if (
        commits != source_commits(root)
        or metadata != load_live_map(root, args.map_dir)[1]
    ):
        raise ValueError("Route inputs changed during checks")
    report = {
        "executed_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        "commits": commits,
        "map": metadata,
        "runner_sha256": digest(Path(__file__)),
        "scope": "Registered directed graph with default RouteOptions. No field validation; identity paths included.",
        "routes": rows,
        "reachable": sum(r["reachable"] for r in rows),
        "total": len(rows),
        "field_verified": False,
        "real_model_calls": 0,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Reachable: {report['reachable']}/{report['total']}")
    return int(report["reachable"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
