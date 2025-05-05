# ingestion.py

import os
import ast
from typing import List, Dict, Callable
from pathlib import Path

import esprima
import javalang
from clang import cindex
from clang.cindex import CursorKind


def parse_python(src: str, path: str) -> List[Dict]:
    """
    Parse a Python file and extract top-level functions, async functions, classes, and methods.
    
    This function uses the abstract syntax tree (AST) to identify and extract 
    important code elements from Python source code, including their names, types, and source.
    
    Args:
        src (str): The Python source code as a string
        path (str): The file path, used for identification in the returned data
        
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - path (str): The original file path
            - name (str): The name of the function/class/method
            - type (str): The type of the element (function, async_function, class, method, async_method)
            - code (str): The source code of the element
            
    Raises:
        SyntaxError: If the Python code contains syntax errors
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
    
    This function uses esprima to parse JavaScript code, including JSX syntax,
    and extracts important code elements with their source code.
    
    Args:
        src (str): The JavaScript/JSX source code as a string
        path (str): The file path, used for identification in the returned data
        
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - path (str): The original file path
            - name (str): The name of the function/class/method
            - type (str): The type of the element (function, class, method)
            - code (str): The source code of the element
            
    Raises:
        Exception: If parsing fails due to syntax errors
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
    
    This function uses javalang to parse Java source code and extract classes and methods
    with their source code.
    
    Args:
        src (str): The Java source code as a string
        path (str): The file path, used for identification in the returned data
        
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - path (str): The original file path
            - name (str): The name of the class/method
            - type (str): The type of the element (class, method)
            - code (str): The source code of the element
            
    Raises:
        Exception: If parsing fails due to syntax errors
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


def parse_c_cpp(src: str, path: str) -> List[Dict]:
    """
    Parse a C or C++ file and extract top-level functions, methods, classes, and structs.
    
    This function uses the clang library to parse C/C++ source code and extract 
    important elements with their source code.
    
    Args:
        src (str): The C/C++ source code as a string
        path (str): The file path, used for identification in the returned data
        
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - path (str): The original file path
            - name (str): The name of the function/class/method/struct
            - type (str): The type of the element (function, method, class, struct)
            - code (str): The source code of the element
            
    Raises:
        Exception: If parsing fails
    """
    index = cindex.Index.create()
    # you can pass in extra args (e.g. include dirs, -std=c++17) if needed:
    tu = index.parse(path, args=["-std=c++17"], unsaved_files=[(path, src)], options=0)
    docs: List[Dict] = []
    lines = src.splitlines()

    def extract(node):
        # only consider declarations in this file
        if not node.location.file or node.location.file.name != path:
            return

        if node.kind == CursorKind.FUNCTION_DECL:
            start, end = node.extent.start, node.extent.end
            code = "\n".join(lines[start.line - 1 : end.line])
            docs.append(
                {"path": path, "name": node.spelling, "type": "function", "code": code}
            )

        elif node.kind == CursorKind.CXX_METHOD:
            start, end = node.extent.start, node.extent.end
            code = "\n".join(lines[start.line - 1 : end.line])
            docs.append(
                {
                    "path": path,
                    "name": f"{node.semantic_parent.spelling}.{node.spelling}",
                    "type": "method",
                    "code": code,
                }
            )

        elif node.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
            start, end = node.extent.start, node.extent.end
            code = "\n".join(lines[start.line - 1 : end.line])
            docs.append(
                {
                    "path": path,
                    "name": node.spelling,
                    "type": "class" if node.kind == CursorKind.CLASS_DECL else "struct",
                    "code": code,
                }
            )

        # recurse
        for child in node.get_children():
            extract(child)

    extract(tu.cursor)
    return docs


# Map file extensions to their respective parser functions
PARSERS: Dict[str, Callable[[str, str], List[Dict]]] = {
    ".py": parse_python,
    ".js": parse_javascript,
    ".jsx": parse_javascript,
    ".ts": parse_javascript,
    ".tsx": parse_javascript,
    ".java": parse_java,
    ".c": parse_c_cpp,
    ".cpp": parse_c_cpp,
    ".cc": parse_c_cpp,
    ".cxx": parse_c_cpp,
    ".hpp": parse_c_cpp,
    ".hh": parse_c_cpp,
    ".h": parse_c_cpp,
}


def parse_file(path: str) -> List[Dict]:
    """
    Parse a source code file based on its extension and extract code elements.
    
    This function determines the file type by extension and dispatches to the 
    appropriate parser function to extract code elements.
    
    Args:
        path (str): The path to the source code file
        
    Returns:
        List[Dict]: A list of dictionaries containing information about code elements
            See individual parser functions for details on the returned format
            
    Raises:
        Exception: If file reading or parsing fails
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in PARSERS:
        return []  # Skip unsupported files

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            return []  # Skip empty files

        return PARSERS[ext](content, path)
    except Exception as e:
        print(f"Error parsing {path}: {e}")
        return []


def parse_directory(root: str) -> List[Dict]:
    """
    Recursively parse all source code files in a directory and its subdirectories.
    
    This function walks through a directory tree, identifies supported source code files
    by extension, and parses them to extract code elements.
    
    Args:
        root (str): The root directory to start parsing from
        
    Returns:
        List[Dict]: A concatenated list of dictionaries containing information about code elements
            from all parsed files. See individual parser functions for details on the returned format.
            
    Raises:
        Exception: If directory traversal fails
    """
    all_docs = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if not os.path.isfile(path):
                continue  # Skip non-files (e.g., symlinks)
            all_docs.extend(parse_file(path))
    return all_docs
