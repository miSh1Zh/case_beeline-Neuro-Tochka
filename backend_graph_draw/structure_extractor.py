import os
import ast
import json


def parse_python_file(path: str):
    """
    Parse a Python file to extract top-level functions and classes with their methods.
    Returns a dict with "functions" and "classes".
    """
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=path)

    functions = []
    classes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes.append({"name": node.name, "methods": methods})

    return {"functions": functions, "classes": classes}


def build_hierarchy(root: str, ext: str, exclude_tests: bool = True):
    """
    Recursively build a nested hierarchy of directories and files for given extension.
    Skip directories containing 'test' if exclude_tests is True.
    """
    def should_skip(name: str) -> bool:
        return exclude_tests and 'test' in name.lower()

    def recurse(path: str):
        name = os.path.basename(path) or path
        if os.path.isdir(path):
            children = []
            for entry in sorted(os.listdir(path)):
                if should_skip(entry):
                    continue
                full = os.path.join(path, entry)
                children.append(recurse(full))
            return {"type": "directory", "name": name, "children": children}
        else:
            # File node
            node = {"type": "file", "name": name}
            if path.endswith(ext):
                parsed = parse_python_file(path)
                node.update({
                    "functions": parsed["functions"],
                    "classes": parsed["classes"]
                })
            return node

    return recurse(root)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract project hierarchy, functions, classes, and methods as JSON'
    )
    parser.add_argument('--root', required=True, help='Root directory of the project')
    parser.add_argument('--ext', default='.py', help='Source file extension (default: .py)')
    parser.add_argument('--exclude-tests', action='store_true', help='Skip directories containing "test"')
    parser.add_argument('--output', default='structure.json', help='Output JSON file')
    args = parser.parse_args()

    hierarchy = build_hierarchy(args.root, args.ext, exclude_tests=args.exclude_tests)
    with open(args.output, 'w', encoding='utf-8') as out:
        json.dump(hierarchy, out, ensure_ascii=False, indent=2)

    print(f"Hierarchy written to {args.output}")