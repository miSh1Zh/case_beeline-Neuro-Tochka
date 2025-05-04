# ingestion.py

import os
import ast
from typing import List, Dict, Callable
from pathlib import Path

import esprima
import javalang


def parse_python(src: str, path: str) -> List[Dict]:
    """
    Parse a Python file and extract top-level functions, async functions, classes, and methods.
    """
    tree = ast.parse(src)
    docs: List[Dict] = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            code = ast.get_source_segment(src, node)
            docs.append(
                {
                    "path": path,
                    "name": node.name,
                    "type": "function",
                    "code": code,
                }
            )
        elif isinstance(node, ast.AsyncFunctionDef):
            code = ast.get_source_segment(src, node)
            docs.append(
                {
                    "path": path,
                    "name": node.name,
                    "type": "async_function",
                    "code": code,
                }
            )
        elif isinstance(node, ast.ClassDef):
            class_code = ast.get_source_segment(src, node)
            docs.append(
                {
                    "path": path,
                    "name": node.name,
                    "type": "class",
                    "code": class_code,
                }
            )
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_code = ast.get_source_segment(src, child)
                    docs.append(
                        {
                            "path": path,
                            "name": f"{node.name}.{child.name}",
                            "type": "method",
                            "code": method_code,
                        }
                    )
                elif isinstance(child, ast.AsyncFunctionDef):
                    method_code = ast.get_source_segment(src, child)
                    docs.append(
                        {
                            "path": path,
                            "name": f"{node.name}.{child.name}",
                            "type": "async_method",
                            "code": method_code,
                        }
                    )
    return docs


def parse_javascript(src: str, path: str) -> List[Dict]:
    """
    Parse a JavaScript/JSX file and extract top-level functions, classes, and methods.
    Enables JSX mode and rewrites <>…</> fragments.
    """
    try:
        # Enable JSX and retain character ranges
        options = {"loc": True, "range": True, "jsx": True}
        # Replace fragment shorthand so Esprima can parse it
        src_pre = src.replace("<>", "<React.Fragment>").replace(
            "</>", "</React.Fragment>"
        )
        tree = esprima.parseModule(src_pre, options)
    except Exception as e:
        print(f"Warning: skipping JS file {path!r} due to parse error: {e}")
        return []

    docs: List[Dict] = []
    for node in tree.body:
        if node.type == "FunctionDeclaration" and node.id:
            name = node.id.name
            start, end = node.range  # character offsets
            code = src[start:end]
            docs.append(
                {
                    "path": path,
                    "name": name,
                    "type": "function",
                    "code": code,
                }
            )
        elif node.type == "ClassDeclaration" and node.id:
            class_name = node.id.name
            start, end = node.range
            class_code = src[start:end]
            docs.append(
                {
                    "path": path,
                    "name": class_name,
                    "type": "class",
                    "code": class_code,
                }
            )
            # Extract methods
            for elt in node.body.body:
                if elt.type == "MethodDefinition" and elt.key:
                    mname = elt.key.name
                    ms, me = elt.range
                    mcode = src[ms:me]
                    docs.append(
                        {
                            "path": path,
                            "name": f"{class_name}.{mname}",
                            "type": "method",
                            "code": mcode,
                        }
                    )
    return docs


def parse_java(src: str, path: str) -> List[Dict]:
    """
    Parse a Java file and extract classes and their methods.
    """
    try:
        tree = javalang.parse.parse(src)
    except Exception as e:
        print(f"Warning: skipping Java file {path!r} due to parse error: {e}")
        return []

    docs: List[Dict] = []
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        # Class code extraction is approximate (by line numbers)
        class_name = node.name
        docs.append(
            {
                "path": path,
                "name": class_name,
                "type": "class",
                "code": "\n".join(
                    src.splitlines()[
                        node.position.line - 1 : node.position.line + len(node.body)
                    ]
                ),
            }
        )
        for method in node.methods:
            if method.position:
                start_line = method.position.line - 1
                # crude end detection: up to closing brace
                method_lines = src.splitlines()[start_line:]
                # gather until first line that is just '}'
                collected = []
                for line in method_lines:
                    collected.append(line)
                    if line.strip() == "}":
                        break
                docs.append(
                    {
                        "path": path,
                        "name": f"{class_name}.{method.name}",
                        "type": "method",
                        "code": "\n".join(collected),
                    }
                )
    return docs


# Map file extensions to their respective parser functions
PARSERS: Dict[str, Callable[[str, str], List[Dict]]] = {
    ".py": parse_python,
    ".js": parse_javascript,
    ".jsx": parse_javascript,
    ".ts": parse_javascript,
    ".tsx": parse_javascript,
    ".java": parse_java,
}


def parse_file(path: str) -> List[Dict]:
    """
    Dispatch to the appropriate parser based on file extension.
    """
    ext = Path(path).suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
    except Exception as e:
        print(f"Warning: could not read file {path!r}: {e}")
        return []
    return parser(src, path)


def parse_directory(root: str) -> List[Dict]:
    """
    Walk a directory recursively and parse all supported files.
    """
    docs: List[Dict] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            docs.extend(parse_file(full_path))
    return docs
