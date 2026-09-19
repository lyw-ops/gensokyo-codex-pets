"""Verify the optional static task_3 native package and its fail-safe fallback."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


binary = Path(sys.argv[1]).resolve()
source = binary.parent.parent / "Resources/WorkEatingTier3"
checks = []


def validate(root=source):
    run = subprocess.run(
        [str(binary), "--validate-assets", "--work-tier-3-root", str(root)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(run.stdout)


result = validate()
assert result["work_tier_3_frames"] == 1
assert abs(result["work_tier_3_duration"] - 0.125) < 1e-9
assert result["work_tier_3_reason"] == "none"
checks.append("native loader accepts the pinned one-frame task_3 package")

with tempfile.TemporaryDirectory(prefix="reimu-work-tier3-qa-") as temp:
    root = Path(temp) / "WorkEatingTier3"
    shutil.copytree(source, root)
    (root / "frames/frame_000.png").write_bytes(b"damaged frame")
    result = validate(root)
    assert result["work_tier_3_frames"] == 1 and result["work_tier_3_reason"] != "none"
    assert result["work_tier_2_frames"] == 16
    assert result["standing_frames"] == 140 and result["frames"] == 40
    checks.append("damaged exact frame degrades only tier 3 to standing")

    shutil.rmtree(root)
    shutil.copytree(source, root)
    (root / "source.json").write_text("{}")
    result = validate(root)
    assert result["work_tier_3_frames"] == 1 and result["work_tier_3_reason"] != "none"
    checks.append("manifest identity or digest mismatch degrades only tier 3 to standing")

    shutil.rmtree(root)
    shutil.copytree(source, root)
    (root / "base.png").unlink()
    result = validate(root)
    assert result["work_tier_3_frames"] == 1 and result["work_tier_3_reason"] != "none"
    checks.append("missing task_3 base degrades only tier 3 to standing")

print(json.dumps({"status": "pass", "count": len(checks), "checks": checks}, indent=2))
