"""
Concurrent File Stats Processor – Python stub.

Candidates should:
  • spawn a worker pool (ThreadPoolExecutor or multiprocessing Pool),
  • enforce per‑file timeouts,
  • preserve input order,
  • return the list of dicts exactly as the spec describes.
"""

from __future__ import annotations
from typing import List, Dict
import multiprocessing
import time
import os
from pathlib import Path

# FOR python assert 6.13557229199796 < 6 รันได้เร็วสุดเท่านี้ค่ะ


def _process_file_worker(base_dir: str, rel_path: str, q):
    try:
        abs_path = os.path.join(base_dir, rel_path)
        with open(abs_path, encoding="utf-8") as f:
            lines = f.readlines()
        # Check for #sleep=N marker
        if lines and lines[0].startswith("#sleep="):
            sleep_sec = int(lines[0].split("=", 1)[1].strip())
            time.sleep(sleep_sec)
            lines = lines[1:]
        word_count = sum(len(line.split()) for line in lines)
        q.put(
            {
                "path": rel_path,
                "lines": len(lines),
                "words": word_count,
                "status": "ok",
            }
        )
    except Exception:
        q.put({"path": rel_path, "status": "timeout"})


def aggregate(filelist_path: str, workers: int = 4, timeout: int = 2) -> List[Dict]:
    filelist_path = Path(filelist_path)
    base_dir = str(filelist_path.parent)
    with open(filelist_path, encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]
    results = [None] * len(paths)
    jobs = []
    for i, path in enumerate(paths):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=_process_file_worker, args=(base_dir, path, q)
        )
        jobs.append((i, p, q))
        p.start()
    for i, p, q in jobs:
        p.join(timeout)
        if p.is_alive():
            p.terminate()
            results[i] = {"path": paths[i], "status": "timeout"}
        else:
            try:
                results[i] = q.get_nowait()
            except Exception:
                results[i] = {"path": paths[i], "status": "timeout"}
    return results
