from __future__ import annotations

"""Flask API providing project structure analysis & Mermaid generation.

Key endpoints
==============
* **POST /structure**   → detects dominant language, filters out junk, returns placeholder structure.
* **POST /mermaid**     → runs language‑specific script (e.g. `mermaid_python.py`) to render Mermaid diagram for a file.
* **GET  /hierarchy**   → builds a full directory hierarchy with parsed symbols (multi‑language‑ready).

Design points
-------------
* Unified *ignore* logic for hidden dirs, VCS folders, build artefacts, etc.
* Parser registry (`LANG_PARSERS`) — easy to plug extra languages.
* Graceful error handling: user‑level issues always return HTTP 200 with a JSON payload (per requirement), programmer errors → 500.
"""

import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import ast

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

MERMAID_SCRIPT_MAP: Dict[str, str] = {
    ".py": "mermaid_python.py",
    ".js": "mermaid_js.py",
    ".jsx": "mermaid_js.py",
    ".ts": "mermaid_js.py",
    ".tsx": "mermaid_js.py",
    ".java": "mermaid_java.py",
    ".c": "mermaid_cpp.py",
    ".cpp": "mermaid_cpp.py",
    ".cc": "mermaid_cpp.py",
    ".cxx": "mermaid_cpp.py",
    ".h": "mermaid_cpp.py",
    ".hpp": "mermaid_cpp.py",
    ".hh": "mermaid_cpp.py",
    ".go": "mermaid_go.py",
}

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

DEFAULT_IGNORE_FILES: Set[str] = {
    ".gitignore",
    ".gitattributes",
    ".DS_Store",
}

# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers (language‑specific)
# ──────────────────────────────────────────────────────────────────────────────


def parse_python_file(path: str) -> Dict[str, Any]:
    """Return top‑level functions and classes/methods from a Python source file."""
    with open(path, "r", encoding="utf‑8") as f:
        tree = ast.parse(f.read(), filename=path)

    functions: List[str] = []
    classes: List[Dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes.append({"name": node.name, "methods": methods})
    return {"functions": functions, "classes": classes}


def parse_generic_file(path: str) -> Dict[str, Any]:
    """Fallback parser for unsupported languages (returns empty info)."""
    return {}


# Registry of parsers keyed by file extension
LANG_PARSERS: Dict[str, callable] = {
    ".py": parse_python_file,
    # future: add '.js': parse_js_file, '.java': parse_java_file, etc.
}

# ──────────────────────────────────────────────────────────────────────────────
# Filesystem helpers
# ──────────────────────────────────────────────────────────────────────────────


def iter_code_files(
    root: Path, extra_ignores: Set[str] | None = None
) -> Iterable[Path]:
    """Yield code files under *root* obeying ignore rules and supported suffixes."""
    ignore_dirs = DEFAULT_IGNORE_DIRS | (extra_ignores or set())
    ignore_files = DEFAULT_IGNORE_FILES | (extra_ignores or set())

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in ignore_dirs and not d.startswith(".")
        ]
        for fname in filenames:
            if fname.startswith(".") or fname in ignore_files:
                continue
            path = Path(dirpath, fname)
            if path.suffix.lower() in MERMAID_SCRIPT_MAP:
                yield path


def write_tmp(filename: str, text: str) -> None:
    """Persist small bits of cross‑endpoint state (fire‑and‑forget)."""
    try:
        Path(filename).write_text(text, encoding="utf‑8")
    except OSError:
        pass  # Non‑critical


# ──────────────────────────────────────────────────────────────────────────────
# Hierarchy builder (multi‑language)
# ──────────────────────────────────────────────────────────────────────────────


def build_hierarchy(
    root: str, exts: Tuple[str, ...] | None = None, *, exclude_tests: bool = True
) -> Dict[str, Any]:
    """Return nested dict representing directory/file hierarchy.

    * **root** — project root directory.
    * **exts** — tuple of extensions to parse (default: all keys from `MERMAID_SCRIPT_MAP`).
    * **exclude_tests** — skip files/dirs whose name contains 'test'.
    """
    exts = exts or tuple(MERMAID_SCRIPT_MAP.keys())

    def should_skip(name: str) -> bool:
        return exclude_tests and "test" in name.lower()

    def recurse(path: Path) -> Dict[str, Any]:
        name = path.name or str(path)
        if path.is_dir():
            children = []
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                if should_skip(child.name):
                    continue
                if child.name in DEFAULT_IGNORE_DIRS or child.name.startswith("."):
                    continue
                children.append(recurse(child))
            return {"type": "directory", "name": name, "children": children}
        else:
            node: Dict[str, Any] = {"type": "file", "name": name}
            suffix = path.suffix.lower()
            if suffix in exts:
                parser = LANG_PARSERS.get(suffix, parse_generic_file)
                node.update(parser(str(path)))
            return node

    return recurse(Path(root))


# ──────────────────────────────────────────────────────────────────────────────
# API routes
# ──────────────────────────────────────────────────────────────────────────────


@app.route("/structure", methods=["POST"])
def get_structure():
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    root_arg = data.get("path")

    if not root_arg:
        return (
            jsonify(
                {"status": "error", "message": "Request JSON must include 'path'."}
            ),
            200,
        )

    root = Path(root_arg).expanduser().resolve()
    if not root.exists():
        return (
            jsonify({"status": "error", "message": f"Path '{root}' does not exist."}),
            200,
        )

    write_tmp("root_path.txt", str(root))

    counter = Counter(p.suffix.lower() for p in iter_code_files(root))
    if not counter:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No source code files found under the given path.",
                }
            ),
            200,
        )

    top_ext, _ = counter.most_common(1)[0]
    write_tmp("main_lang.txt", top_ext)
    main_language = top_ext.lstrip(".")

    # Placeholder structure — could call build_hierarchy here if needed
    structure: Dict[str, Any] = {}

    return (
        jsonify(
            {
                "status": "success",
                "structure": structure,
            }
        ),
        200,
    )


@app.route("/mermaid", methods=["POST"])
def get_mermaid():
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    rel_path = data.get("path")

    if not rel_path:
        abort(400, description="JSON must include 'path' (file relative to repo root).")

    target_path = Path("../repo-chat-mvp/tmp", rel_path).as_posix().replace("//", "/")

    try:
        root_path = Path("root_path.txt").read_text().strip()
    except FileNotFoundError:
        abort(400, description="/structure must be called first to set up context.")

    if not Path(target_path).is_file():
        abort(400, description=f"Provided target path is not a file: {target_path}")
    if not Path(root_path).is_dir():
        abort(400, description=f"Project root is invalid or missing: {root_path}")

    ext = Path(target_path).suffix.lower()
    script_name = MERMAID_SCRIPT_MAP.get(ext)
    if not script_name:
        abort(
            400, description=f"Unsupported file extension for Mermaid generation: {ext}"
        )

    script_path = Path(__file__).with_name(script_name)
    if not script_path.exists():
        abort(500, description=f"Mermaid script not found: {script_name}")

    command = [
        sys.executable,
        str(script_path),
        "--target",
        target_path,
        "--root",
        root_path,
        "--ext",
        ext,
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding="utf‑8"
        )
        return jsonify({"mermaid_code": result.stdout})
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}\nStderr: {e.stderr}")
        abort(500, description=f"Error generating Mermaid diagram: {e.stderr}")
    except Exception as e:  # noqa: BLE001
        print(f"Unexpected error: {e}")
        abort(500, description=f"Unexpected error: {e}")


@app.route("/hierarchy", methods=["GET"])
def get_hierarchy():
    try:
        root = Path("root_path.txt").read_text().strip()
    except FileNotFoundError:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Project not initialised. Call /structure first.",
                }
            ),
            200,
        )

    # Derive list of interesting extensions found in project
    exts = tuple({p.suffix.lower() for p in iter_code_files(Path(root))}) or tuple(
        MERMAID_SCRIPT_MAP.keys()
    )

    try:
        full_hierarchy = build_hierarchy(root, exts)
        return jsonify({"status": "success", "hierarchy": full_hierarchy}), 200
    except Exception as e:  # noqa: BLE001
        return (
            jsonify({"status": "error", "message": f"Error building hierarchy: {e}"}),
            200,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # To run: python app.py
    app.run(host="0.0.0.0", port=8001, debug=False)
