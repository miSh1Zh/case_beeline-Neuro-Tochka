from flask import Flask, request, jsonify, abort
import os
import subprocess
import base64
from pathlib import Path
from collections import Counter
from typing import Iterable, Set, Dict, Any
import sys
from flask_cors import CORS
from structure_extractor import build_hierarchy

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Map supported languages to file extensions
LANG_EXTENSIONS: Dict[str, str] = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
}

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


def iter_code_files(
    root: Path, extra_ignores: Set[str] | None = None
) -> Iterable[Path]:
    """Yield paths of source‑code files under *root*.

    * Prunes directories listed in `DEFAULT_IGNORE_DIRS` and hidden folders.
    * Skips hidden files and those listed in `DEFAULT_IGNORE_FILES`.
    * Accepts only files whose suffix is in `MERMAID_SCRIPT_MAP`.
    """
    ignore_dirs = DEFAULT_IGNORE_DIRS.copy()
    ignore_files = DEFAULT_IGNORE_FILES.copy()
    if extra_ignores:
        ignore_dirs |= extra_ignores
        ignore_files |= extra_ignores

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in ignore_dirs and not d.startswith(".")
        ]
        for fname in filenames:
            if fname in ignore_files or fname.startswith("."):
                continue
            path = Path(dirpath, fname)
            if path.suffix.lower() in MERMAID_SCRIPT_MAP:
                yield path


def write_tmp(filename: str, text: str) -> None:
    """Best‑effort helper to persist small bits of state for sibling endpoints."""
    try:
        Path(filename).write_text(text, encoding="utf‑8")
    except OSError:
        # Non‑critical; log if needed
        pass


@app.route("/structure", methods=["POST"])
def get_structure():
    data = request.get_json()
    # Check for required fields in the request body
    if not data or "path" not in data:
        # Instead of aborting, return a JSON response with error details and 200 status
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "JSON must include 'path' and 'language'.",
                }
            ),
            200,
        )

    root = data["path"]

    # Note: Writing to language.txt and root_path.txt might not be strictly necessary
    # if this information is passed directly to the structure_extractor function, but keeping it for now.
    try:
        with open("root_path.txt", "w") as f:
            f.write(root)
    except IOError as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error writing to temporary files: {e}"}
            ),
            200,
        )

    counter = Counter()
    for dirpath, _, files in os.walk(root):
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in MERMAID_SCRIPT_MAP:
                counter[ext] += 1

    # 2) Выбираем наиболее частое расширение
    if counter:
        top_ext, count = counter.most_common(1)[0]
        main_language = top_ext.lstrip(".")  # например, "py" или "js"
        mermaid_script = MERMAID_SCRIPT_MAP[top_ext]  # имя вашего генератора
    else:
        main_language = None
        mermaid_script = None

    with open("main_lang.txt", "w") as f:
        f.write(f".{main_language}")

    # Если всё прошло успешно, возвращаем 200 и, например, пустой объект или результат
    return (
        jsonify(
            {"status": "success", "structure": {}}  # <-- сюда вставьте ваши данные
        ),
        200,
    )


@app.route("/mermaid", methods=["POST"])
def get_mermaid():
    data = request.get_json()

    if not data or "path" not in data:
        abort(
            400,
            description="JSON must include 'path' (target file) and 'root' (project root).",
        )

    target_path = f"../repo-chat-mvp/tmp/{data["path"]}".replace("//", "/")
    print(target_path)
    with open("root_path.txt", "r") as f:
        root_path = f.read()
    with open("main_lang.txt", "r") as f:
        main_language = f.read()

    if not os.path.isfile(target_path):
        abort(
            400,
            description=f"Provided target path is not a file or does not exist: {target_path}",
        )
    if not os.path.isdir(root_path):
        abort(
            400,
            description=f"Provided root path is not a directory or does not exist: {root_path}",
        )

    # Dictionary mapping file extensions to the corresponding mermaid script filenames

    # Extract extension and determine the script to use
    _, ext = os.path.splitext(target_path)
    script_name = MERMAID_SCRIPT_MAP.get(ext.lower())

    if not script_name:
        abort(
            400, description=f"Unsupported file extension for Mermaid generation: {ext}"
        )

    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        abort(500, description=f"Mermaid script not found: {script_name}")

    try:
        # Construct the command to run the selected script
        command = [
            sys.executable,  # Use the same python interpreter that is running Flask
            script_path,
            "--target",
            target_path,
            "--root",
            root_path,
            "--ext",
            ext.lower(),  # Pass the specific extension to the script
        ]

        # Run the script as a subprocess
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError if the script returns a non-zero exit code
            encoding="utf-8",  # Ensure output is correctly decoded
        )

        # The Mermaid code is in the standard output of the script
        mermaid_code = result.stdout
        print(mermaid_code)

        return jsonify({"mermaid_code": mermaid_code})

    except subprocess.CalledProcessError as e:
        # Log the error details (optional, but helpful for debugging)
        print(f"Error running mermaid_python.py: {e}")
        print(f"Stderr: {e.stderr}")
        abort(500, description=f"Error generating Mermaid diagram: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        abort(500, description=f"An unexpected error occurred: {e}")


@app.route("/hierarchy", methods=["GET"])
def get_hierarchy():
    try:
        with open("root_path.txt", "r") as f:
            root = f.read().strip()
        # Если нужно определять основной язык — можете оставить этот блок,
        # либо просто вызвать build_hierarchy(root).
        counter = Counter()
        for dirpath, _, files in os.walk(root):
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in MERMAID_SCRIPT_MAP:
                    counter[ext] += 1
        main_ext = counter.most_common(1)[0][0] if counter else None

        # Строим полную иерархию. Если build_hierarchy ожидает два аргумента — передаём ext:
        full_hierarchy = build_hierarchy(root, main_ext)

        # Возвращаем её целиком
        return jsonify({"status": "success", "hierarchy": full_hierarchy}), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Error building hierarchy: {e}"}),
            418,
        )


if __name__ == "__main__":
    # To run: python app_flask.py
    app.run(host="0.0.0.0", port=8001)
