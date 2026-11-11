#!/usr/bin/env python3
"""Build a feature ledger: every screen and backend operation found in the code, grouped
into candidate features, as a Markdown checklist the analysis must fully resolve.

Usage: feature_ledger.py <root> [<root> ...] [--out FILE] [--force]
  Pass both frontend and backend repos when they are separate.
  Without --out, prints the ledger. With --out, refuses to overwrite an existing ledger
  (it holds progress) unless --force is given, and prints a short summary.
Read-only on the analyzed code. Standard library only.
"""
import os
import re
import sys
from collections import OrderedDict

SKIP_DIRS = {"node_modules", "vendor", ".git", "dist", "build", ".next", ".nuxt", ".output", "out",
             "target", "bin", "obj", "coverage", "__pycache__", ".venv", "venv", ".vercel", ".idea",
             ".turbo", ".cache", "storage", "public", ".dart_tool", "docs", ".claude", ".agents"}
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".php", ".py", ".java", ".kt", ".cs",
            ".rb", ".go", ".dart", ".graphql", ".gql"}
TEST_RE = re.compile(r"(\.test\.|\.spec\.|/tests?/|/__tests__/|/e2e/)")

# Sub-screens and actions that belong to the same business feature as their parent path.
ACTION_SEGMENTS = {"create", "new", "add-new", "edit", "update", "view", "show", "details", "detail", "list",
                   "items", "report", "reports", "timeline", "workflowlog", "workflow-log", "log", "logs",
                   "history", "print", "preview", "index", "form", "page"}
VERB_PREFIX = re.compile(
    r"^(create|update|upsert|delete|remove|add|edit|set|get|list|find|fetch|search|approve|reject|cancel|"
    r"submit|confirm|close|open|reopen|post|unpost|send|import|export|generate|assign|unassign|activate|"
    r"deactivate|enable|disable|restore|archive|toggle|change|reset|verify|register|login|logout|refresh|"
    r"bulk|clear|duplicate|copy|move|transfer|upload|download|calculate|validate|check|mark|attach|detach|"
    r"link|unlink|start|finish|complete|issue|receive|return|count|all|my|one|many)(?=[A-Z_]|$)")

FRONT_ROUTE_PATTERNS = [
    re.compile(r"""\bpath\s*:\s*["'`]([^"'`]*)["'`]"""),            # react-router objects, vue-router, angular
    re.compile(r"""<Route\b[^>]*\bpath\s*=\s*["'{`]+([^"'`}]*)"""),  # <Route path="...">
]
BACK_ROUTE_PATTERNS = [
    (re.compile(r"""Route::(get|post|put|patch|delete|resource|apiResource|any|match)\(\s*["']([^"']+)"""), "Laravel"),
    (re.compile(r"""\b(?:router|app|route|r|e|api)\.(get|post|put|patch|delete)\(\s*["'`]([^"'`]+)"""), "HTTP"),
    (re.compile(r"""@(Get|Post|Put|Patch|Delete)(?:Mapping)?\(\s*(?:value\s*=\s*)?["']([^"']*)"""), "HTTP"),
    (re.compile(r"""\[Http(Get|Post|Put|Patch|Delete)\(\s*"([^"]*)"""), "ASP.NET"),
    (re.compile(r"""@(?:app|router|bp|blueprint)\.(get|post|put|patch|delete|route)\(\s*["']([^"']+)"""), "Python"),
    (re.compile(r"""\b(re_)?path\(\s*r?["']([^"']+)["']\s*,"""), "Django"),
]
# A file must look like a router definition before its `path:` keys count as screens
# (table-column configs and tool configs also use `path:`).
ROUTER_FILE = re.compile(r"(createBrowserRouter|createRouter|RouteObject|Routes\b|<Route\b|loadChildren|loadComponent|"
                         r"\b(element|component|load|lazy|redirect)\s*:)")
GQL_ROOT = re.compile(r"(?:extend\s+)?type\s+(Mutation|Query)\s*\{")
GQL_FIELD = re.compile(r"^\s*([A-Za-z_]\w*)\s*[(:]", re.M)
GQL_DECORATOR = re.compile(r"@(Mutation|Query)\([^)]*\)\s*(?:async\s+)?([A-Za-z_]\w*)\s*\(")
GQL_DOC = re.compile(r"\b(mutation|query)\s+([A-Za-z_]\w*)\s*[({]")


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext in CODE_EXT and ".min." not in name:
                path = os.path.join(dirpath, name)
                if not TEST_RE.search(path.replace(os.sep, "/")):
                    yield path


def kebab(name):
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    return name.replace("_", "-").lower().strip("-")


def route_group(path):
    segments = []
    for seg in path.strip().strip("/").split("/"):
        s = seg.strip().lower()
        if not s or s[0] in ":{[*<(" or s.startswith("$") or s in ACTION_SEGMENTS:
            continue
        segments.append(s)
    return "/".join(segments) or "(root)"


def operation_group(name):
    stripped = name[:1].lower() + name[1:]
    while True:
        new = VERB_PREFIX.sub("", stripped, count=1)
        if new == stripped or not new:
            break
        stripped = new[0].lower() + new[1:]
    group = kebab(stripped) or kebab(name)
    for suffix in ("-by-id", "-list", "-items", "-details", "-paginated", "-count", "-input", "-statuses", "-status"):
        if group.endswith(suffix) and len(group) > len(suffix):
            group = group[: -len(suffix)]
    if group.endswith("ies"):
        group = group[:-3] + "y"
    elif group.endswith("s") and not group.endswith(("ss", "us", "is")):
        group = group[:-1]
    return group


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def scan(roots):
    screens = OrderedDict()   # group -> {paths:set, sources:set}
    http = OrderedDict()      # group -> list of "METHOD path"
    gql = OrderedDict()       # group -> {"Mutation": set, "Query": set}
    file_screens = []
    for root in roots:
        root = os.path.abspath(root)
        for path in iter_files(root):
            rel = os.path.relpath(path, os.path.dirname(root)) if len(roots) > 1 else os.path.relpath(path, root)
            rel = rel.replace(os.sep, "/")
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            ext = os.path.splitext(path)[1]

            # File-based routing (Next.js, Nuxt, SvelteKit)
            m = re.search(r"/(app|pages)/(.+?)/?(page\.(?:t|j)sx?|\+page\.svelte|index\.vue|[^/]+\.vue)$", "/" + rel)
            if m and "/api/" not in rel and not re.search(r"/_(app|document)\.", rel) and "/components/" not in rel:
                route = re.sub(r"\([^)]*\)/?", "", m.group(2))
                if m.group(3).endswith(".vue") and not m.group(3).startswith("index"):
                    route = route + "/" + m.group(3)[:-4]
                file_screens.append((route_group(route), "/" + route, rel))

            if ext == ".graphql" or ext == ".gql":
                for root_match in GQL_ROOT.finditer(text):
                    kind = root_match.group(1)
                    depth, i = 1, root_match.end()
                    while i < len(text) and depth:
                        depth += {"{": 1, "}": -1}.get(text[i], 0)
                        i += 1
                    body = re.sub(r'"""[\s\S]*?"""|"[^"\n]*"|#.*', "", text[root_match.end(): i - 1])
                    depth_body, names = 0, []
                    for line in body.splitlines():
                        if depth_body == 0:
                            fm = GQL_FIELD.match(line)
                            if fm:
                                names.append(fm.group(1))
                        depth_body += line.count("(") - line.count(")")
                    for n in names:
                        gql.setdefault(operation_group(n), {"Mutation": set(), "Query": set()})[kind].add(n)
                continue

            for fm in GQL_DECORATOR.finditer(text):
                gql.setdefault(operation_group(fm.group(2)), {"Mutation": set(), "Query": set()})[fm.group(1)].add(fm.group(2))

            if ext in {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".dart"}:
                is_router = bool(ROUTER_FILE.search(text))
                for pat in FRONT_ROUTE_PATTERNS:
                    if pat is FRONT_ROUTE_PATTERNS[0] and not is_router:
                        continue
                    for rm in pat.finditer(text):
                        p = rm.group(1)
                        if p.startswith("http") or "${" in p or "." in p or " " in p or len(p) > 120:
                            continue
                        g = route_group(p)
                        entry = screens.setdefault(g, {"paths": set(), "sources": set()})
                        entry["paths"].add(p or "/")
                        entry["sources"].add("%s:%d" % (rel, line_of(text, rm.start())))

            for pat, _kind in BACK_ROUTE_PATTERNS:
                for rm in pat.finditer(text):
                    method, p = rm.group(1), rm.group(2)
                    if _kind == "Django" and ext != ".py":
                        continue
                    if _kind == "HTTP" and ext in {".tsx", ".jsx", ".vue", ".svelte"}:
                        continue  # client-side fetch helpers, not server routes
                    g = route_group(p)
                    http.setdefault(g, []).append("%s %s  (%s:%d)" % ((method or "path").upper(), p or "/", rel, line_of(text, rm.start())))

    for g, p, rel in file_screens:
        entry = screens.setdefault(g, {"paths": set(), "sources": set()})
        entry["paths"].add(p)
        entry["sources"].add(rel)
    return screens, http, gql


def render(roots, screens, http, gql):
    out = []
    w = out.append
    n_paths = sum(len(v["paths"]) for v in screens.values())
    n_ops = sum(len(v["Mutation"]) + len(v["Query"]) for v in gql.values())
    n_http = sum(len(v) for v in http.values())
    w("# Feature ledger")
    w("")
    w("Generated by feature_ledger.py from: " + ", ".join(os.path.basename(os.path.abspath(r)) for r in roots))
    w("")
    w("**This ledger defines \"complete\".** Every row must end with one of these statuses:")
    w("- `✅ F07` — covered by feature card F07")
    w("- `➖ F07` — part of feature F07 (sub-screen, log, timeline, report, lookup)")
    w("- `⛔ reason` — not a business feature (technical, dev-only, dead code); the reason is required")
    w("")
    w("Rows still marked `⬜` mean the report is **incomplete**. Groups are a heuristic: split a group that holds")
    w("several business documents, and merge groups that are one feature.")
    w("")
    w("| Totals | Screen groups | Screen paths | GraphQL groups | GraphQL operations | HTTP groups | HTTP endpoints |")
    w("|---|---|---|---|---|---|---|")
    w("| | %d | %d | %d | %d | %d | %d |" % (len(screens), n_paths, len(gql), n_ops, len(http), n_http))
    w("")
    if screens:
        w("## Screens (frontend routes)")
        w("")
        w("| # | Group | Screens | Source | Status |")
        w("|---|---|---|---|---|")
        for i, (g, v) in enumerate(sorted(screens.items()), 1):
            paths = "<br>".join(sorted(v["paths"]))
            src = "<br>".join(sorted(v["sources"])[:3]) + (" …" if len(v["sources"]) > 3 else "")
            w("| S%d | %s | %s | %s | ⬜ |" % (i, g, paths, src))
        w("")
    if gql:
        w("## Backend operations (GraphQL)")
        w("")
        w("| # | Group | Mutations (actions) | Queries (reads) | Status |")
        w("|---|---|---|---|---|")
        for i, (g, v) in enumerate(sorted(gql.items()), 1):
            w("| G%d | %s | %s | %s | ⬜ |" % (i, g, ", ".join(sorted(v["Mutation"])) or "—", ", ".join(sorted(v["Query"])) or "—"))
        w("")
    if http:
        w("## Backend endpoints (HTTP)")
        w("")
        w("| # | Group | Endpoints | Status |")
        w("|---|---|---|---|")
        for i, (g, v) in enumerate(sorted(http.items()), 1):
            w("| H%d | %s | %s | ⬜ |" % (i, g, "<br>".join(sorted(set(v)))))
        w("")
    if not (screens or gql or http):
        w("No routes or operations detected automatically — build the ledger by hand from the router, menu and API files.")
    return "\n".join(out) + "\n", (len(screens), n_paths, len(gql), n_ops, len(http), n_http)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    out_file, force = None, "--force" in argv
    if "--out" in argv:
        idx = argv.index("--out")
        out_file = argv[idx + 1] if idx + 1 < len(argv) else None
        args = [a for a in args if a != out_file]
    roots = args or ["."]
    for r in roots:
        if not os.path.isdir(r):
            sys.stderr.write("Not a directory: %s\n" % r)
            return 1
    text, counts = render(roots, *scan(roots))
    if not out_file:
        sys.stdout.write(text)
        return 0
    if os.path.exists(out_file) and not force:
        print("Ledger already exists: %s — resume from its unfinished (⬜) rows; pass --force to rebuild." % out_file)
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("Ledger written: %s" % out_file)
    print("Screen groups: %d (%d paths) · GraphQL groups: %d (%d operations) · HTTP groups: %d (%d endpoints)" % counts)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
