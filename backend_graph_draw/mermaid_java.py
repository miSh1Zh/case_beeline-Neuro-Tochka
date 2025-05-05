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
    p.add_argument(
        "--ext", default=".java", help="Source file extension (default: .java)"
    )
    return p.parse_args()


# Import the java parser from ingestion.py
from ingestion import parse_java


def extract_elements(path):
    """Extracts top-level classes and methods using ingestion.py parser."""
    elements = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        parsed_data = parse_java(content, path)
        for item in parsed_data:
            # We are interested in classes and methods defined in the target file
            if item["type"] in ["class", "method"]:
                elements.append({"name": item["name"], "type": item["type"]})
    except Exception as e:
        print(f"Error processing {path}: {e}")
    return elements


def find_mentions(root, exts, target_basename, elements, target_path):
    """
    Ищет упоминания в проекте: возвращает узлы и сырые ребра.
    Узел: {id, label, dir, is_file}
    Ребро: (from_id, to_id)
    """
    nodes = {}
    raw_edges = []
    nodes = {}  # Initialize nodes dict here
    target_abs = os.path.abspath(target_path)
    base_dir = os.path.dirname(target_path)
    valid_extensions = tuple(exts.split(","))  # Convert comma-sep string to tuple
    # Exclude patterns for test folders
    exclude_patterns = [re.compile(r"test", re.IGNORECASE)]

    for dirpath, dirnames, files in os.walk(root):
        # Exclude directories from traversal
        dirnames[:] = [
            d for d in dirnames if not any(p.search(d) for p in exclude_patterns)
        ]
        # Skip processing files within excluded folders
        if any(
            p.search(part) for part in Path(dirpath).parts for p in exclude_patterns
        ):
            continue

        for fname in files:
            # Check if the file has one of the valid extensions
            if not any(fname.lower().endswith(ext) for ext in valid_extensions):
                continue
            full = os.path.join(dirpath, fname)
            if os.path.abspath(full) == target_abs:
                continue  # Skip the target file itself

            rel_to_target = os.path.relpath(full, start=base_dir)
            # Determine if the path is relative within the project or an external dependency path
            is_file_in_proj = not rel_to_target.startswith(os.pardir)
            # Use filename for files in project, directory name for external deps/folders
            raw = fname if is_file_in_proj else os.path.basename(dirpath)
            node_id = re.sub(r"[^A-Za-z0-9_]", "_", raw)  # Sanitize ID
            dir_rel = os.path.relpath(dirpath, root)

            # Only add node if it doesn't exist
            if node_id not in nodes:
                nodes[node_id] = {
                    "id": node_id,
                    "label": raw,
                    "dir": dir_rel,
                    "is_file": is_file_in_proj,
                }

            try:
                text = Path(full).read_text(encoding="utf-8")
                # Check if the target *filename* (without extension) is mentioned
                # Use word boundaries (\b) to avoid partial matches within other words
                if re.search(r"\b" + re.escape(target_basename) + r"\b", text):
                    raw_edges.append((node_id, "Target"))
                # Check mentions for each extracted element (class/method)
                for element in elements:
                    # Use word boundary to avoid partial matches
                    # For methods, search for the full name (e.g., MyClass.myMethod)
                    search_name = element["name"]
                    if re.search(r"\b" + re.escape(search_name) + r"\b", text):
                        # Link to the specific element ID (using a prefix like Elem_)
                        raw_edges.append((node_id, f'Elem_{element["name"]}'))
            except Exception as e:
                print(f"Could not read or search in {full}: {e}")

    return nodes, raw_edges


if __name__ == "__main__":
    args = parse_args()
    target = args.target
    root = args.root
    exts = args.ext  # Now expects comma-separated extensions

    target_basename = Path(target).stem
    # Use the new function to get elements (classes/methods)
    elements = extract_elements(target)
    # Pass exts (plural) and elements to find_mentions
    nodes, raw_edges = find_mentions(root, exts, target_basename, elements, target)

    # Add Target node and nodes for each extracted element
    target_dir = os.path.relpath(os.path.dirname(target), root)
    nodes["Target"] = {
        "id": "Target",
        "label": Path(target).name,
        "dir": target_dir,
        "is_file": True,
    }
    for element in elements:
        # Use a consistent prefix for element nodes
        elem_id = f'Elem_{element["name"]}'
        # Indicate type in label, e.g., MyClass (class) or myMethod() (method)
        label_suffix = f" ({element['type']})" if element["type"] == "class" else "()"
        nodes[elem_id] = {
            "id": elem_id,
            "label": f'{element["name"]}{label_suffix}',
            "dir": target_dir,
            "is_file": True,
        }
        # Link each element back to the target file node (visually groups them)
        raw_edges.append((elem_id, "Target"))

    # Filter edges based on source type (file/folder) and target type (element/Target)
    edges = []
    processed_file_to_target_links = (
        set()
    )  # Track file->Target links to avoid duplicates if element link exists

    for frm, to in raw_edges:
        # Ensure source node exists (it should, as it's added in find_mentions)
        from_node = nodes.get(frm)
        if not from_node:
            print(f"Warning: Source node {frm} not found, skipping edge ({frm}, {to})")
            continue

        # Ensure target node exists (Target or Elem_ nodes added above)
        to_node = nodes.get(to)
        if not to_node:
            # This case should ideally not happen if elements are extracted correctly
            # It might occur if a mention points to something not parsed as a top-level element
            print(f"Warning: Target node {to} not found, skipping edge ({frm}, {to})")
            continue

        is_source_file = from_node["is_file"]

        if is_source_file:
            # Case 1: File mentions a specific element (class/method)
            if to.startswith("Elem_"):
                edges.append((frm, to))
                # Mark that this file links to the target indirectly via an element
                processed_file_to_target_links.add(frm)
            # Case 2: File mentions the Target file itself (e.g., import)
            elif to == "Target":
                # Add this link only if no specific element link exists from this file
                if frm not in processed_file_to_target_links:
                    edges.append((frm, to))
                    processed_file_to_target_links.add(frm)  # Mark as processed
            # Case 3: Element links back to Target (added above for grouping)
            elif frm.startswith("Elem_") and to == "Target":
                edges.append((frm, to))

        else:  # Source is a folder (representing external directory)
            # Folders should only link to the main Target node
            if to == "Target":
                edges.append((frm, to))
            # We ignore folder->element links for simplicity

    # Aggregate duplicate edges and count occurrences
    edge_counts = Counter(edges)

    # Identify active nodes from unique edges
    active = set()
    for frm, to in edge_counts:
        active.add(frm)
        active.add(to)

    # Generate Mermaid output
    # Configure Mermaid padding and spacing
    print(
        '%%{init: {"flowchart": {"diagramPadding": 30, "nodeSpacing": 150, "rankSpacing": 100}, "wrappingWidth": 30, "markdownAutoWrap": true}}%%'
    )
    print("flowchart LR")
    # Define custom classes for different node types
    print(
        "  classDef file fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,padding:10px;"
    )  # Light blue for files
    print(
        "  classDef folder fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,stroke-dasharray:5 5,padding:10px;"
    )  # Light orange for folders
    print(
        "  classDef classDefClass fill:#fce4ec,stroke:#ec407a,stroke-width:2px,padding:10px;"
    )  # Pinkish for classes
    print(
        "  classDef method fill:#e1bee7,stroke:#ab47bc,stroke-width:2px,padding:10px;"
    )  # Purplish for methods
    print()

    # Group nodes by folder path into subgraphs
    groups = {}
    for nid, data in nodes.items():
        # Only include nodes that are part of an edge (active nodes)
        if nid not in active:
            continue
        grp = data["dir"] or "."  # Use '.' for the root directory
        groups.setdefault(grp, []).append(data)

    # Output subgraphs for each folder
    for grp, group_nodes in groups.items():
        # Sanitize group ID for Mermaid (replace non-alphanumeric with underscores)
        sanitized_grp_id = re.sub(r"[^A-Za-z0-9_]", "_", grp or "root")
        subgraph_id = f"folder_{sanitized_grp_id}"
        label = (
            grp if grp != "." else "root"
        )  # Use 'root' as label for the root directory
        print(f"  subgraph {subgraph_id}[{label}]")
        # Output nodes within the subgraph
        for n in group_nodes:
            print(f'    {n["id"]}["{n["label"]}"]')
        print("  end")
        print()

    # Output connections (edges) with call counts
    for (frm, to), count in edge_counts.items():
        # Ensure source node exists (it should, as it's added in find_mentions or as Elem_ node)
        from_node = nodes.get(frm)
        if not from_node:
            # This should not happen if logic is correct, but good for debugging
            print(
                f"Warning: Source node {frm} not found for edge ({frm}, {to}), skipping edge output."
            )
            continue

        is_source_file = from_node["is_file"]

        # Determine line style: solid for file->element/target, dashed for folder->target
        line_style = "-->" if is_source_file else "-.->"
        # Add call count as label if greater than 1
        label = f"|{count} calls|" if count > 1 else ""

        # Output the edge line
        print(f"  {frm} {line_style}{label} {to}")

    # Assign classes (styling) to active nodes
    print()
    for nid, data in nodes.items():
        if nid not in active:
            continue
        # Determine base style (file/folder)
        style = "file" if data["is_file"] else "folder"
        # Assign specific styles for elements within the target file (nodes starting with Elem_)
        if nid.startswith("Elem_"):
            # Find the original element data from the list to check its type
            original_name = nid[len("Elem_") :]
            # Access elements list (passed from main) to get the original type
            # This assumes element names are unique within the target file, which parse_java ensures for top-level classes/methods.
            elem_data = next((e for e in elements if e["name"] == original_name), None)
            if elem_data:
                # Assign 'class' or 'method' style based on the parsed data type
                style = elem_data["type"]

        # Ensure the Target node is styled as a file
        elif nid == "Target":
            style = "file"

        # Output the class assignment line
        print(f"  class {nid} {style}")
