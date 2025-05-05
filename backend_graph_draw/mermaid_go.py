#!/usr/bin/env python3
"""Generate a Mermaid dependency diagram for a Go project.

The script mirrors the behaviour of *mermaid_python.py* but understands Go syntax.
Key differences:
* **Functions** – captured via ``func <Name>(`` or ``func (recv) <Name>(``.
* **Imports**   – handles single‑line ``import "pkg/path"`` and multi‑line ``import ( ... )`` blocks.
* **Internal packages** – only imports that resolve *within* the given project root are visualised.

Run example:
    python mermaid_go.py --target ./cmd/server/main.go --root . --ext .go
"""
import os
import re
import argparse
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Dict, Any

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Mermaid dependency diagram with folder-based subgraphs (excluding test dirs) for Go sources"
    )
    p.add_argument("--target", required=True, help="Path to the target .go file")
    p.add_argument("--root", required=True, help="Root directory of the project")
    p.add_argument("--ext", default=".go", help="Source file extension (default: .go)")
    return p.parse_args()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def extract_functions(path: str) -> List[str]:
    """Return names of top‑level functions / methods declared in *path*."""
    funcs: List[str] = []
    # Matches:   func Name(     OR   func (r Receiver) Name(
    pattern = re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                funcs.append(m.group(1))
    return funcs


def _iter_import_paths(text: str) -> List[str]:
    """Yield import strings from Go source (single & multi‑line)."""
    paths: List[str] = []
    single_re = re.compile(r"^\s*import\s+\"([^\"]+)\"")
    block_start_re = re.compile(r"^\s*import\s*\(\s*")

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m_single = single_re.match(line)
        if m_single:
            paths.append(m_single.group(1))
            i += 1
            continue
        # multi‑line block
        if re.match(r"^\s*import\s*\(\s*$", line):
            i += 1
            while i < len(lines) and not re.match(r"^\s*\)\s*$", lines[i]):
                m_path = re.search(r"\"([^\"]+)\"", lines[i])
                if m_path:
                    paths.append(m_path.group(1))
                i += 1
        i += 1
    return paths


def extract_imports(
    path: str, root: str, target_dir: str
) -> List[Tuple[str, str, bool, str]]:
    """Return list of tuples: (full_path, label, is_file, rel_dir).

    For Go, imports refer to *package directories*; we map only those located under *root*.
    """
    imports: List[Tuple[str, str, bool, str]] = []
    text = Path(path).read_text(encoding="utf-8")

    for pkg in _iter_import_paths(text):
        # Turn import path into directory under root, if exists.
        dir_path = os.path.join(root, pkg.replace("/", os.sep))
        if not os.path.isdir(dir_path):
            continue  # external dependency
        label = os.path.basename(dir_path)
        rel_dir = os.path.relpath(dir_path, root)
        same_folder = os.path.abspath(dir_path) == os.path.abspath(
            os.path.join(root, target_dir)
        )
        # In Go, we treat imported package as *folder* node
        imports.append((dir_path, label, False, rel_dir))
    return imports


def find_mentions(
    root: str, ext: str, target_pkg: str, funcs: List[str], target_path: str
):
    nodes: Dict[str, Dict[str, str | bool]] = {}
    edges_raw: List[Tuple[str, str]] = []
    target_abs = os.path.abspath(target_path)
    base_dir = os.path.dirname(target_path)
    exclude_patterns = [re.compile(r"test", re.IGNORECASE), re.compile(r"_test\.go$")]

    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if not any(p.search(d) for p in exclude_patterns)
        ]
        if any(
            p.search(part) for part in Path(dirpath).parts for p in exclude_patterns
        ):
            continue

        for fname in files:
            if not fname.endswith(ext) or fname.endswith("_test.go"):
                continue
            full = os.path.join(dirpath, fname)
            if os.path.abspath(full) == target_abs:
                continue

            raw_label = os.path.basename(dirpath)  # package label (dir name)
            nid = re.sub(r"[^A-Za-z0-9_]", "_", raw_label)
            dir_rel = os.path.relpath(dirpath, root)
            nodes[nid] = {
                "id": nid,
                "label": raw_label,
                "dir": dir_rel,
                "is_file": False,
            }

            text = Path(full).read_text(encoding="utf-8")
            if re.search(r"\b" + re.escape(target_pkg) + r"\.", text):
                edges_raw.append((nid, "Target"))
            for fn in funcs:
                # match pkg.Func or just Func (same package)
                pattern_pkg = (
                    r"\b" + re.escape(target_pkg) + r"\." + re.escape(fn) + r"\b"
                )
                pattern_local = r"\b" + re.escape(fn) + r"\b"
                if re.search(pattern_pkg, text) or re.search(pattern_local, text):
                    edges_raw.append((nid, f"Func_{fn}"))

    return nodes, edges_raw


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    target = args.target
    root = args.root
    ext = args.ext

    if not target.endswith(ext):
        raise SystemExit(f"--target must be a {ext} file")

    # Determine package name from file path (dir name)
    target_pkg = Path(target).parent.name

    funcs = extract_functions(target)

    # Build nodes & edges from mentions across project
    nodes, edges_raw = find_mentions(root, ext, target_pkg, funcs, target)

    # Add target node & its functions
    target_dir = os.path.relpath(os.path.dirname(target), root)
    nodes["Target"] = {
        "id": "Target",
        "label": Path(target).name,
        "dir": target_dir,
        "is_file": True,
    }
    for fn in funcs:
        fid = f"Func_{fn}"
        nodes[fid] = {"id": fid, "label": f"{fn}()", "dir": target_dir, "is_file": True}
        edges_raw.append((fid, "Target"))

    # Add imported packages as folder nodes
    imports = extract_imports(target, root, target_dir)
    for full, label, is_file, dir_rel in imports:
        nid = re.sub(r"[^A-Za-z0-9_]", "_", label)
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "dir": dir_rel, "is_file": is_file}
        edges_raw.append(("Target", nid))

    # Edge filtering rules (similar semantics as Python version)
    edges: List[Tuple[str, str]] = []
    for frm, to in edges_raw:
        node = nodes.get(frm)
        if not node:
            continue
        if node["is_file"]:  # file (Target or Func)
            if to.startswith("Func_") or frm == "Target":
                edges.append((frm, to))
        else:  # folder package
            if to == "Target":
                edges.append((frm, to))

    counts = Counter(edges)
    active = {n for e in counts for n in e}

    # ── Output Mermaid diagram ───────────────────────────────────────────────
    print(
        '%%{init: {"flowchart": {"diagramPadding": 30, "nodeSpacing": 150, "rankSpacing": 100}, "wrappingWidth": 30, "markdownAutoWrap": true}}%%'
    )
    print("flowchart LR")
    print("  classDef file fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,padding:10px;")
    print(
        "  classDef folder fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,stroke-dasharray:5 5,padding:10px;\n"
    )

    # Group nodes by directory
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for nid, data in nodes.items():
        if nid not in active:
            continue
        grp = data["dir"] or "."
        groups.setdefault(grp, []).append(data)

    for grp, items in groups.items():
        sid = re.sub(r"[^A-Za-z0-9_]", "_", grp or "root")
        lbl = grp if grp != "." else "root"
        print(f"  subgraph folder_{sid}[{lbl}]")
        for it in items:
            print(f'    {it["id"]}["{it["label"]}"]')
        print("  end\n")

    # Draw edges
    for (frm, to), cnt in counts.items():
        if nodes[frm]["is_file"]:
            connector = "--" if cnt > 1 else "-"  # multiple calls emphasised
            suffix = f" {cnt} calls " if cnt > 1 else ""
            print(f"  {frm} {connector}>{suffix}> {to}")
        else:
            connector = "-." if cnt == 1 else "-."  # same for folder
            suffix = f" {cnt} calls " if cnt > 1 else ""
            print(f"  {frm} {connector}{suffix}.-> {to}")

    # Assign classes
    print()
    for nid, data in nodes.items():
        if nid not in active:
            continue
        cls = "file" if data["is_file"] else "folder"
        print(f"  class {nid} {cls}")
