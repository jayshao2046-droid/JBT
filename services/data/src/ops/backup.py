"""Data backup utilities for JBT data service.

Migrated from Mini shell scripts:
- backup_to_nas.sh: rsync BotQuan_Data → NAS
- mini_data_backup.sh: daily hdf5/parquet snapshot
- mini_backup_weekly.sh: weekly full backup

In JBT Docker, backup is triggered by the scheduler and writes to the
configured BACKUP_DIR (mount volume).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("data.ops.backup")


def backup_data_dir(
    *,
    source_dir: str | Path,
    backup_dir: str | Path,
    label: str = "",
) -> Path:
    """Create a timestamped snapshot of source_dir inside backup_dir.

    Returns the path to the created snapshot directory.
    """
    source = Path(source_dir)
    dest_root = Path(backup_dir)
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"{label}_{timestamp}" if label else timestamp
    dest = dest_root / snapshot_name
    dest.mkdir(parents=True, exist_ok=True)

    logger.info("backup started: %s → %s", source, dest)
    shutil.copytree(source, dest, dirs_exist_ok=True)
    logger.info("backup completed: %s", dest)
    return dest


def rsync_to_remote(
    *,
    source_dir: str | Path,
    remote_target: str,
    dry_run: bool = False,
) -> bool:
    """rsync source_dir to a remote target (NAS or other host).

    remote_target format: user@host:/path/to/dest/
    """
    cmd = [
        "rsync", "-avz", "--delete",
        str(Path(source_dir)) + "/",
        remote_target,
    ]
    if dry_run:
        cmd.insert(2, "--dry-run")

    logger.info("rsync: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        logger.error("rsync failed: %s", result.stderr)
        return False
    logger.info("rsync completed: %s", remote_target)
    return True
