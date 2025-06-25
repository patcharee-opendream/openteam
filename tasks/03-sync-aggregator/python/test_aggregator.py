import pathlib, time
from aggregator import aggregate

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
_FILELIST = _DATA_DIR / "filelist.txt"

_EXPECTED = [
    {"path": "texts/01_lorem.txt",     "lines": 5, "words": 69, "status": "ok"},
    {"path": "texts/02_zen.txt",       "lines": 8, "words": 39, "status": "ok"},
    {"path": "texts/03_bacon.txt",     "lines": 3, "words": 38, "status": "ok"},
    {"path": "texts/04_proverbs.txt",  "lines": 5, "words": 25, "status": "ok"},
    {"path": "texts/05_poem.txt",      "lines": 5, "words": 37, "status": "ok"},
    {"path": "texts/06_quote.txt",     "lines": 2, "words": 12, "status": "ok"},
    {"path": "texts/07_sleep5.txt",                     "status": "timeout"},
    {"path": "texts/08_sleep10.txt",                    "status": "timeout"},
    {"path": "texts/09_scifi.txt",     "lines": 4, "words": 47, "status": "ok"},
    {"path": "texts/10_short.txt",     "lines": 1, "words":  2, "status": "ok"},
    {"path": "texts/11_manifesto.txt", "lines": 4, "words": 49, "status": "ok"},
    {"path": "texts/12_jokes.txt",     "lines": 3, "words": 45, "status": "ok"},
    {"path": "texts/13_ai_ghosts.txt", "lines": 6, "words": 83, "status": "ok"},
    {"path": "texts/14_funfacts.txt",  "lines": 3, "words": 52, "status": "ok"},
    {"path": "texts/15_trivia.txt",    "lines": 3, "words": 58, "status": "ok"},
]

def test_aggregate_parallel_exact():
    start = time.perf_counter()
    out = aggregate(str(_FILELIST), workers=8, timeout=2)
    duration = time.perf_counter() - start

    # 1 – array order exactly matches source filelist
    want_paths = [l.strip() for l in _FILELIST.read_text().splitlines()]
    got_paths  = [rec["path"] for rec in out]
    assert got_paths == want_paths, "result order must follow filelist order"

    # 2 – every record matches EXPECTED (lines/words omitted on timeout)
    assert out == _EXPECTED, "results differ from expected ground truth"

    # 3 – basic concurrency sanity‑check (serial run would take >15 s)
    assert duration < 6, f"processing too slow ({duration:.2f}s); did you parallelise?"
