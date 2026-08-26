#!/usr/bin/env python3
"""Regenerate every master-DB figure into figures/output/.

    python3 analysis/master-db/figures/make_figures.py
    python3 analysis/master-db/figures/make_figures.py fig05 fig11   # a subset
    MDB_FIG_DARK=1 python3 analysis/master-db/figures/make_figures.py

Re-run `build_database.py` first if you have added a Covidence export — these
scripts read the committed `_data/master_db.json`, never the raw CSVs.
"""
import glob
import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))


def modules():
    return sorted(p for p in glob.glob(os.path.join(HERE, "fig*.py")))


def run(path):
    name = os.path.basename(path)[:-3]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def main(argv):
    paths = modules()
    if argv:
        paths = [p for p in paths if any(a in os.path.basename(p) for a in argv)]
        if not paths:
            sys.exit(f"no figure matches {argv}; available: "
                     + ", ".join(os.path.basename(p)[:-3] for p in modules()))
    ok, failed = 0, []
    for p in paths:
        name = os.path.basename(p)[:-3]
        print(f"{name} …")
        try:
            run(p)
            ok += 1
        except Exception:                      # one broken figure must not stop the rest
            failed.append(name)
            traceback.print_exc()
    print(f"\n{ok}/{len(paths)} figures written to "
          f"{os.path.relpath(os.path.join(HERE, 'output'), os.getcwd())}")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
