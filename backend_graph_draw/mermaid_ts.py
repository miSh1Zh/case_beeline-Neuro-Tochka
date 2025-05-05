#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from tree_sitter import Language, Parser

# Загрузим собранную библиотеку грамматики TypeScript
TS_LANGUAGE = Language('path/to/ts.so', 'typescript')
parser = Parser()
parser.set_language(TS_LANGUAGE)

def parse_ts(src: str):
    """
    Парсим текст .ts/.tsx в дерево и возвращаем корневую ноду.
    """
    return parser.parse(bytes(src, 'utf8')).root_node

def extract_entities(path):
    """
    Извлекает из целевого .ts/.tsx-файла:
      - funcs   (function_declaration, method_definition)
      - classes (class_declaration)
    """
    src = Path(path).read_text(encoding='utf-8')
    tree = parse_ts(src)

    funcs = []
    classes = []

    # обходим AST в поисках нужных узлов
    def walk(node):
        if node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                funcs.append(src[name_node.start_byte:name_node.end_byte])
        elif node.type == 'method_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                funcs.append(src[name_node.start_byte:name_node.end_byte])
        elif node.type == 'class_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                classes.append(src[name_node.start_byte:name_node.end_byte])
        for child in node.children:
            walk(child)

    walk(tree)
    return funcs, classes

def resolve_module(spec, current, root, ext):
    """То же, что и раньше — для относительных импортов .ts/.tsx."""
    if not spec.startswith('.'):
        return None
    base = os.path.dirname(current)
    cands = [spec]
    if not spec.endswith(ext):
        cands.append(spec + ext)
    cands.append(os.path.join(spec, 'index' + ext))
    for cand in cands:
        full = os.path.normpath(os.path.join(base, cand))
        if os.path.commonpath([os.path.abspath(full), root]) != root:
            continue
        if os.path.isfile(full):
            return os.path.relpath(full, root)
    return None

def extract_imports_for_file(path, root, ext):
    """
    Ищем все import/require из TypeScript-файла
    (ES6 import и dynamic import())
    """
    deps = []
    src = Path(path).read_text(encoding='utf-8')
    tree = parse_ts(src)

    # рекурсивный обход AST в поисках ImportDeclaration и call_expression(import)
    def walk(node):
        if node.type == 'import_statement':
            # импорт вида: import X from "..."
            lit = node.child_by_field_name('source')
            if lit and lit.type == 'string':
                spec = src[lit.start_byte+1:lit.end_byte-1]
                rel = resolve_module(spec, path, root, ext)
                if rel:
                    deps.append(rel)
        elif node.type == 'call_expression':
            fn = node.child_by_field_name('function')
            if fn and fn.type == 'identifier' and src[fn.start_byte:fn.end_byte] in ('require','import'):
                arg = node.child_by_field_name('arguments').child(0)
                if arg and arg.type == 'string':
                    spec = src[arg.start_byte+1:arg.end_byte-1]
                    rel = resolve_module(spec, path, root, ext)
                    if rel:
                        deps.append(rel)
        for c in node.children:
            walk(c)

    walk(tree.root_node)
    return deps

def find_mentions(root, ext, base, funcs, classes, target_path):
    nodes = {}
    raw_edges = []
    target_abs = os.path.abspath(target_path)
    base_dir   = os.path.dirname(target_path)
    exclude    = re.compile(r'test', re.IGNORECASE)

    for dp, dns, files in os.walk(root):
        dns[:] = [d for d in dns if not exclude.search(d)]
        if any(exclude.search(p) for p in Path(dp).parts):
            continue
        for fn in files:
            if not fn.endswith(ext):
                continue
            full = os.path.join(dp, fn)
            if os.path.abspath(full) == target_abs:
                continue
            rel_to_t = os.path.relpath(full, base_dir)
            is_file  = not rel_to_t.startswith(os.pardir)
            raw      = fn if is_file else os.path.basename(dp)
            nid      = re.sub(r'[^A-Za-z0-9_]', '_', raw)
            dir_rel  = os.path.relpath(dp, root)
            nodes[nid] = {'id':nid,'label':raw,'dir':dir_rel,'is_file':is_file}
            txt = Path(full).read_text(encoding='utf-8')
            if re.search(rf'\\b{re.escape(base)}\\b', txt):
                raw_edges.append((nid,'Target'))
            for f in funcs:
                if re.search(rf'\\b{re.escape(f)}\\b', txt):
                    raw_edges.append((nid,f'Func_{f}'))
            for c in classes:
                if re.search(rf'\\b{re.escape(c)}\\b', txt):
                    raw_edges.append((nid,f'Class_{c}'))
    return nodes, raw_edges

def main():
    args   = parse_args()
    root   = os.path.abspath(args.root)
    tgt    = os.path.abspath(args.target)
    ext    = args.ext
    if not tgt.startswith(root):
        raise SystemExit('Error: target must lie inside root')

    funcs, classes = extract_entities(tgt)
    base = Path(tgt).stem

    nodes, raw_edges = find_mentions(root, ext, base, funcs, classes, tgt)

    # добавляем Target
    tgt_dir = os.path.relpath(os.path.dirname(tgt), root)
    nodes['Target'] = {'id':'Target','label':Path(tgt).name,'dir':tgt_dir,'is_file':True}

    # парсим импорты из самого Target → рёбра Target→dep
    for dep in extract_imports_for_file(tgt, root, ext):
        did = re.sub(r'[^A-Za-z0-9_]','_',dep)
        nodes.setdefault(did, {'id':did,'label':os.path.basename(dep),'dir':os.path.dirname(dep),'is_file':True})
        raw_edges.append(('Target',did))

    # узлы для функций/классов Target
    for f in funcs:
        fid = f'Func_{f}'
        nodes[fid] = {'id':fid,'label':f'{f}()','dir':tgt_dir,'is_file':True}
        raw_edges.append((fid,'Target'))
    for c in classes:
        cid = f'Class_{c}'
        nodes[cid] = {'id':cid,'label':c,'dir':tgt_dir,'is_file':True}
        raw_edges.append((cid,'Target'))

    # фильтрация, счёт и отбор active
    valid_to = {'Target'}|{f'Func_{x}' for x in funcs}|{f'Class_{x}' for x in classes}
    edges = [(f,t) for f,t in raw_edges if nodes.get(f) and ((nodes[f]['is_file'] and t in valid_to) or (not nodes[f]['is_file'] and t=='Target'))]
    cnts  = Counter(edges)
    active = {n for e in cnts for n in e}

    # вывод Mermaid
    print("%%{init:{\"flowchart\":{\"diagramPadding\":30,\"nodeSpacing\":150,\"rankSpacing\":100},\"wrappingWidth\":30,\"markdownAutoWrap\":true}}%%")
    print("flowchart LR")
    print("  classDef file   fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,padding:10px;")
    print("  classDef folder fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,stroke-dasharray:5 5,padding:10px;")
    print()
    # группы + узлы
    groups = defaultdict(list)
    for nid, dat in nodes.items():
        if nid in active:
            groups[dat['dir'] or '.'].append(dat)
    for grp, items in groups.items():
        sid = re.sub(r'[^A-Za-z0-9_]','_',grp)
        lbl = grp if grp!='.' else 'root'
        print(f"  subgraph {sid}[{lbl}]")
        for it in sorted(items, key=lambda x: x['label']):
            print(f"    {it['id']}[\"{it['label']}\"]")
        print("  end\n")
    # рёбра
    for (f,t),n in cnts.items():
        arrow = "-->" if nodes[f]['is_file'] else ".->"
        label = f" -- {n} calls --> " if n>1 else f" {arrow} "
        print(f"  {f}{label}{t}")
    # стили
    print()
    for nid in active:
        print(f"  class {nid} {'file' if nodes[nid]['is_file'] else 'folder'}")

if __name__ == '__main__':
    main()