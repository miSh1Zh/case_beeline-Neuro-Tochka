#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path
from collections import Counter


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Mermaid dependency diagram with folder-based subgraphs (excluding test dirs)"
    )
    p.add_argument("--target", required=True, help="Path to the target file")
    p.add_argument("--root", required=True, help="Root directory of the project")
    p.add_argument("--ext", default=".py", help="Source file extension (default: .py)")
    return p.parse_args()


def extract_functions(path):
    """Возвращает список имён функций, объявленных в файле."""
    funcs = []
    pattern = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(")
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                funcs.append(m.group(1))
    return funcs


def extract_imports(path, root, ext, target_dir):
    """Возвращает список импортов из целевого модуля: (абсолютный путь, метка, is_file, относительный dir)"""
    imports = []
    text = Path(path).read_text(encoding="utf-8")

    for line in text.splitlines():
        m1 = re.match(r"^\s*import\s+([\w\.]+)", line)
        m2 = re.match(r"^\s*from\s+([\w\.]+)\s+import", line)
        mod = m1.group(1) if m1 else (m2.group(1) if m2 else None)
        if not mod:
            continue

        rel_path = mod.replace(".", os.sep) + ext
        full_path = os.path.join(root, rel_path)
        if not os.path.exists(full_path):
            continue

        imp_dir = os.path.dirname(full_path)
        same_folder = os.path.abspath(imp_dir) == os.path.abspath(
            os.path.join(root, target_dir)
        )

        label = (
            os.path.basename(full_path) if same_folder else os.path.basename(imp_dir)
        )
        rel_dir = os.path.relpath(imp_dir, root)

        imports.append((full_path, label, same_folder, rel_dir))
    return imports


def find_mentions(root, ext, target_basename, funcs, target_path):
    nodes = {}
    edges_raw = []
    target_abs = os.path.abspath(target_path)
    base_dir = os.path.dirname(target_path)
    exclude_patterns = [re.compile(r"test", re.IGNORECASE)]

    # Ищем, кто ссылается на target и его функции
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if not any(p.search(d) for p in exclude_patterns)
        ]
        if any(
            p.search(part) for part in Path(dirpath).parts for p in exclude_patterns
        ):
            continue

        for fname in files:
            if not fname.endswith(ext):
                continue
            full = os.path.join(dirpath, fname)
            if os.path.abspath(full) == target_abs:
                continue

            rel = os.path.relpath(full, start=base_dir)
            is_file = not rel.startswith(os.pardir)
            raw = fname if is_file else os.path.basename(dirpath)
            nid = re.sub(r"[^A-Za-z0-9_]", "_", raw)
            dir_rel = os.path.relpath(dirpath, root)

            nodes[nid] = {"id": nid, "label": raw, "dir": dir_rel, "is_file": is_file}
            text = Path(full).read_text(encoding="utf-8")

            if re.search(r"\b" + re.escape(target_basename) + r"\b", text):
                edges_raw.append((nid, "Target"))
            for fn in funcs:
                if re.search(r"\b" + re.escape(fn) + r"\b", text):
                    edges_raw.append((nid, f"Func_{fn}"))

    return nodes, edges_raw


if __name__ == "__main__":
    args = parse_args()
    target = args.target
    root = args.root
    ext = args.ext

    basename = Path(target).stem
    funcs = extract_functions(target)

    # Находим ссылки на target и его функции
    nodes, edges_raw = find_mentions(root, ext, basename, funcs, target)

    # Добавляем целевой узел и функции
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

    # Добавляем возможные models.py и другие файлы через импорт из target
    imports = extract_imports(target, root, ext, target_dir)
    # явная проверка на media.models
    text = Path(target).read_text(encoding="utf-8")
    if "media.models" in text and not any(
        label == "models.py" for _, label, *_ in imports
    ):
        full = os.path.join(root, target_dir, "models.py")
        imports.append((full, "models.py", True, target_dir))
    for full, label, is_file, dir_rel in imports:
        nid = re.sub(r"[^A-Za-z0-9_]", "_", label)
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "dir": dir_rel, "is_file": is_file}
        edges_raw.append(("Target", nid))

    # Фильтрация: файлы->функции/импорты, папки->Target
    edges = []
    for frm, to in edges_raw:
        node = nodes.get(frm)
        if not node:
            continue
        if node["is_file"]:
            if to.startswith("Func_") or frm == "Target":
                edges.append((frm, to))
        else:
            if to == "Target":
                edges.append((frm, to))

    counts = Counter(edges)
    active = {n for e in counts for n in e}

    # Вывод в формате Mermaid
    print(
        '%%{init: {"flowchart": {"diagramPadding": 30, "nodeSpacing": 150, "rankSpacing": 100}, "wrappingWidth": 30, "markdownAutoWrap": true}}%%'
    )
    print("flowchart LR")
    print("  classDef file fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,padding:10px;")
    print(
        "  classDef folder fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,stroke-dasharray:5 5,padding:10px;"
    )
    print()

    # Группировка по директориям
    groups = {}
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

    # Рисуем ребра с учётом количества
    for (frm, to), cnt in counts.items():
        if nodes[frm]["is_file"]:
            if cnt > 1:
                print(f"  {frm} -- {cnt} calls --> {to}")
            else:
                print(f"  {frm} --> {to}")
        else:
            if cnt > 1:
                print(f"  {frm} -. {cnt} calls .-> {to}")
            else:
                print(f"  {frm} -.-> {to}")

    # Задаём классы
    print()
    for nid, data in nodes.items():
        if nid not in active:
            continue
        cls = "file" if data["is_file"] else "folder"
        print(f"  class {nid} {cls}")
