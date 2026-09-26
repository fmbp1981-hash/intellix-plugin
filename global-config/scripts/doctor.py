#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py — Linter da própria metodologia IntelliX.

Criado em 2026-09-07 (AUDITORIA-ESTRUTURA-2026-09-07.md) e ampliado em
2026-09-16 (INTELLIX_PLANO_EXECUCAO_REMEDIACAO.md, lote P0-2), depois que uma
auditoria externa mostrou que ele dava "8 verificações OK" com dezenas de
referências mortas, nomes divergentes e Vercel como deploy.

CAUSA DO FALSO VERDE DE 2026-09-16
O conjunto de skills "conhecidas" incluía TODO SKILL.md de TODO marketplace
baixado — inclusive plugins nunca habilitados. `architecture-patterns` existia
só num plugin desabilitado e passava como válida. Agora só conta o que o
runtime realmente carrega: ~/.claude/skills/<pasta>/SKILL.md (1º nível), os
plugins próprios (marketplace `directory`) e os plugins de terceiros habilitados
em settings.json, na versão registrada em installed_plugins.json.

PRINCÍPIO DE DESIGN — precisão acima de cobertura.
Só reporta o que é inequívoco. Menção solta em prosa não é referência.

Uso:
    python3 doctor.py            # relatório; sempre exit 0 (seguro para SessionStart)
    python3 doctor.py --strict   # exit 1 se houver achado (para pre-commit / CI)
    python3 doctor.py --quiet    # só imprime se houver achado

Raiz configurável (testes e validação de worktree antes do merge):
    INTELLIX_ROOT          raiz da config global (padrão: pasta-mãe de scripts/)
    INTELLIX_PLUGINS_DIR   pasta plugins/ (padrão: $INTELLIX_ROOT/plugins)
    INTELLIX_PLUGIN_DIR    fonte do intellix-plugin (padrão: marketplace)
    INTELLIX_DEVSECOPS_DIR fonte do devsecops-plugin (padrão: marketplace)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("INTELLIX_ROOT") or Path(__file__).resolve().parent.parent)
PLUGINS = Path(os.environ.get("INTELLIX_PLUGINS_DIR") or ROOT / "plugins")
STRICT = "--strict" in sys.argv
QUIET = "--quiet" in sys.argv

OWNED = ("intellix-plugin", "devsecops-plugin")
_OWNED_ENV = {"intellix-plugin": "INTELLIX_PLUGIN_DIR", "devsecops-plugin": "INTELLIX_DEVSECOPS_DIR"}

# Placeholders de documentação, não invocações reais.
PLACEHOLDERS = {"nome", "name", "skill", "x", "nome-da-skill", "skill-name", "fase", "id"}

# Extensões de arquivo autoral examinadas pelos checks de texto.
TEXT_EXT = {".md", ".sh", ".json", ".html", ".mmd", ".py", ".yaml", ".yml"}

findings: list[tuple[str, str]] = []  # (categoria, mensagem)


def add(cat: str, msg: str) -> None:
    findings.append((cat, msg))


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def load_json(p: Path):
    try:
        return json.loads(read(p))
    except (json.JSONDecodeError, ValueError):
        return None


def load_metodologia() -> dict:
    """metodologia.yaml é normativo (D1). Ausente ou inválido, os checks que
    dependem dele são pulados — nunca derrubam a sessão."""
    f = ROOT / "metodologia.yaml"
    if not f.is_file():
        return {}
    try:
        import yaml  # PyYAML

        return yaml.safe_load(read(f)) or {}
    except Exception:  # noqa: BLE001 — YAML quebrado não pode travar o SessionStart
        add("META", "metodologia.yaml ausente de PyYAML ou inválido — checks normativos pulados")
        return {}


META = load_metodologia()


def owned_dir(name: str) -> Path:
    return Path(os.environ.get(_OWNED_ENV[name]) or PLUGINS / "marketplaces" / name)


def rel(p: Path) -> str:
    """Caminho legível: relativo à raiz global ou ao plugin próprio."""
    for base, prefix in [(owned_dir(o), f"plugins/marketplaces/{o}") for o in OWNED] + [(ROOT, "")]:
        try:
            r = p.resolve().relative_to(base.resolve())
            return f"{prefix}/{r}" if prefix else str(r)
        except ValueError:
            continue
    return str(p)


def line_of(txt: str, pos: int) -> int:
    return txt[:pos].count("\n") + 1


def frontmatter(md: Path) -> dict[str, str]:
    txt = read(md)
    if not txt.startswith("---"):
        return {}
    end = txt.find("\n---", 3)
    fm = txt[3:end] if end > 0 else txt[3:2000]
    out = {}
    for m in re.finditer(r"^([A-Za-z_-]+):[ \t]*(.*?)\s*$", fm, re.MULTILINE):
        out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def iter_files(base: Path, exts=TEXT_EXT):
    """Arquivos autorais sob `base`, sem .git, bytecode, histórico e o próprio doctor.

    `global-config/` (dentro do intellix-plugin) também é pulado: é um espelho
    versionado de arquivos que vivem em ~/.claude (metodologia.yaml, hooks,
    skills globais como intellix-agent-creation), com convenção de path própria
    (ex.: `resources/references/` em vez de `references/`) — não é conteúdo
    carregado pelo Claude Code como parte do plugin, então não deve ser
    validado pelas regras de convenção do plugin. Ver global-config/README.md.
    """
    if not base.is_dir():
        return
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.suffix not in exts:
            continue
        s = str(p)
        if "/.git/" in s or "__pycache__" in s or "/docs/plans/" in s or "/node_modules/" in s or "/global-config/" in s:
            continue
        if p.name in ("doctor.py", "test_doctor.py", "metodologia.yaml"):
            continue
        yield p


def authored_files(exts=TEXT_EXT) -> list[Path]:
    files: list[Path] = []
    for o in OWNED:
        files += list(iter_files(owned_dir(o), exts))
    files += list(iter_files(ROOT / "modules", exts))
    files += [p for p in iter_files(ROOT / "scripts", exts) if "/tests/" not in str(p)]
    for s in META.get("skills_autorais_globais", []) or []:
        files += list(iter_files(ROOT / "skills" / s, exts))
    if (ROOT / "CLAUDE.md").is_file():
        files.append(ROOT / "CLAUDE.md")
    return files


# ─────────────────────────────────────────────────────────────────────────────
# Coleta: o que o runtime realmente carrega
# ─────────────────────────────────────────────────────────────────────────────
class Plugin:
    def __init__(self, ns: str, root: Path, owned: bool):
        self.ns, self.root, self.owned = ns, root, owned
        self.skills: dict[str, Path] = {}      # id (pasta) -> SKILL.md
        self.commands: dict[str, Path] = {}    # id (arquivo) -> .md
        self.agents: dict[str, Path] = {}
        manifest = load_json(root / ".claude-plugin" / "plugin.json") or {}
        self.version = str(manifest.get("version", ""))
        # Campos do manifest aceitam string ou lista de caminhos. Skills
        # declaradas explicitamente substituem a pasta padrão (ex.:
        # mattpocock-skills lista só as publicadas, não deprecated/in-progress).
        for p in self._paths(manifest.get("skills"), "skills"):
            mds = [p / "SKILL.md"] if (p / "SKILL.md").is_file() else (p.rglob("SKILL.md") if p.is_dir() else [])
            for md in mds:
                if "node_modules" not in md.parts:
                    self.skills.setdefault(md.parent.name, md)
        for field, target in (("commands", self.commands), ("agents", self.agents)):
            paths = self._paths(manifest.get(field), None) + [root / field]
            for p in paths:
                mds = [p] if p.is_file() else (p.rglob("*.md") if p.is_dir() else [])
                for md in mds:
                    if md.suffix == ".md":
                        target.setdefault(md.stem, md)

    def _paths(self, value, default: str | None) -> list[Path]:
        if value is None:
            return [self.root / default] if default else []
        items = value if isinstance(value, list) else [value]
        return [self.root / str(v).removeprefix("./") for v in items]

    def ids(self) -> set[str]:
        return set(self.skills) | set(self.commands) | set(self.agents)


def enabled_ids() -> set[str] | None:
    s = load_json(ROOT / "settings.json")
    if not isinstance(s, dict) or "enabledPlugins" not in s:
        return None
    return {k for k, v in s["enabledPlugins"].items() if v}


def load_plugins() -> dict[str, Plugin]:
    plugins: dict[str, Plugin] = {}
    enabled = enabled_ids()
    for o in OWNED:
        d = owned_dir(o)
        m = load_json(d / ".claude-plugin" / "plugin.json")
        if isinstance(m, dict) and m.get("name"):
            plugins[m["name"]] = Plugin(m["name"], d, owned=True)
    inst = load_json(PLUGINS / "installed_plugins.json") or {}
    for pid, entries in (inst.get("plugins") or {}).items():
        ns, _, mkt = pid.partition("@")
        if mkt in OWNED or ns in plugins:
            continue
        if enabled is not None and pid not in enabled:
            continue
        for e in entries or []:
            p = Path(str(e.get("installPath", "")))
            if p.is_dir():
                plugins[ns] = Plugin(ns, p, owned=False)
                break
    return plugins


def load_global_skills() -> dict[str, Path]:
    """~/.claude/skills/<pasta>/SKILL.md — só o 1º nível é carregado pelo runtime.
    iterdir() enxerga symlinks de topo (instalação via `npx skills add`)."""
    out: dict[str, Path] = {}
    base = ROOT / "skills"
    if not base.is_dir():
        return out
    for child in base.iterdir():
        md = child / "SKILL.md"
        if child.is_dir() and md.is_file():
            out[child.name] = md
            name = frontmatter(md).get("name")
            if name:
                out.setdefault(name, md)
    return out


PLUGINS_LOADED = load_plugins()
GLOBAL_SKILLS = load_global_skills()
NAMESPACES = set(PLUGINS_LOADED)
KNOWN_NS = {(p.ns, i) for p in PLUGINS_LOADED.values() for i in p.ids()}
KNOWN_BARE = set(GLOBAL_SKILLS) | {i for p in PLUGINS_LOADED.values() for i in p.ids()}
NO_MODEL = {
    (p.ns, i)
    for p in PLUGINS_LOADED.values()
    for i, md in list(p.skills.items()) + list(p.commands.items())
    if frontmatter(md).get("disable-model-invocation", "").lower() == "true"
}
INTELLIX = PLUGINS_LOADED.get("intellix")


def ref_exists(ref: str) -> bool:
    ns, sep, name = ref.partition(":")
    if sep:
        return (ns, name) in KNOWN_NS if ns in NAMESPACES else name in KNOWN_BARE
    return ref in KNOWN_BARE


# ─────────────────────────────────────────────────────────────────────────────
# 1. Referências Skill("x") e `ns:skill` inexistentes (13 amplia para todo namespace)
# ─────────────────────────────────────────────────────────────────────────────
def check_dangling_refs() -> None:
    pat_call = re.compile(r'Skill\(\s*["\']([A-Za-z0-9:_-]+)["\']')
    ns_alt = "|".join(sorted((re.escape(n) for n in NAMESPACES), key=len, reverse=True))
    pat_ns = re.compile(rf"(?<![\w/@.-])({ns_alt}):([a-z0-9][a-z0-9_-]*)") if ns_alt else None
    seen: set[tuple[str, str]] = set()
    for f in authored_files():
        txt = read(f)
        hits = [(m.start(), m.group(1)) for m in pat_call.finditer(txt)]
        if pat_ns:
            hits += [(m.start(), f"{m.group(1)}:{m.group(2)}") for m in pat_ns.finditer(txt)]
        lines = txt.splitlines()
        for pos, ref in hits:
            if ref.split(":")[-1] in PLACEHOLDERS or ref_exists(ref):
                continue
            n = line_of(txt, pos)
            if n <= len(lines) and re.search(r"legad|alias", lines[n - 1], re.IGNORECASE):
                continue  # citação explícita de nome antigo (tabela/nota de compatibilidade)
            if (ref, str(f)) in seen:
                continue
            seen.add((ref, str(f)))
            add("REF", f"`{ref}` não existe no runtime — {rel(f)}:{n}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Symlinks quebrados
# ─────────────────────────────────────────────────────────────────────────────
def check_broken_symlinks() -> None:
    bases = [ROOT / "skills", ROOT / "agents"] + [owned_dir(o) for o in OWNED]
    seen: set[Path] = set()
    for base in bases:
        if not base.is_dir():
            continue
        for p in list(base.iterdir()) + list(base.rglob("*")):
            try:
                if p in seen or not p.is_symlink() or p.exists():
                    continue
                seen.add(p)
                add("LINK", f"symlink quebrado: {rel(p)} -> {os.readlink(p)}")
            except OSError:
                continue


# ─────────────────────────────────────────────────────────────────────────────
# 3. Skill global com o mesmo nome de skill de plugin carregado (sombra)
# ─────────────────────────────────────────────────────────────────────────────
def check_duplicate_names() -> None:
    for p in PLUGINS_LOADED.values():
        for sid in p.skills:
            if sid in GLOBAL_SKILLS and GLOBAL_SKILLS[sid].parent.name == sid:
                add(
                    "DUP",
                    f'"{sid}" existe solta em skills/ e em {p.ns}:{sid} — '
                    f'Skill("{sid}") fica ambíguo (use o nome com namespace e arquive a solta)',
                )


# ─────────────────────────────────────────────────────────────────────────────
# 4 / 16. Stack descontinuada (Vercel como alvo de deploy — D6)
# ─────────────────────────────────────────────────────────────────────────────
VERCEL_PATS = [
    re.compile(r"Deploy\**\s*[:|]\s*\**\s*Vercel", re.IGNORECASE),
    re.compile(r"Hospedagem\**\s*[:|]\s*\**\s*Vercel", re.IGNORECASE),
    re.compile(r"\bvercel\s+(deploy|env|logs|rollback|ls|--prod)\b", re.IGNORECASE),
    re.compile(r"\bnpx\s+vercel\b", re.IGNORECASE),
    re.compile(r"Vercel\s+(Production|Preview)\b"),
    re.compile(r"Vercel\s*\+\s*(CI|Cloudflare|DNS)", re.IGNORECASE),
    re.compile(r"deploy\w*\s+Vercel\b", re.IGNORECASE),
    re.compile(r"Vercel\s+Environment\s+Variables", re.IGNORECASE),
    re.compile(r"Vari[aá]veis\s+(de\s+ambiente\s+)?(configuradas\s+no\s+)?Vercel", re.IGNORECASE),
    re.compile(r"Produ[cç][aã]o\s*\(?Vercel\)?", re.IGNORECASE),
    re.compile(r"Acesso\s+ao\s+(cliente\s+configurado\s+\()?Vercel", re.IGNORECASE),
    re.compile(r"cname\.vercel-dns|76\.76\.21\.21|VERCEL_TOKEN|vercelProjectId|Vercel project ID"),
    re.compile(r"Preview Deployments no Vercel|Vercel garante", re.IGNORECASE),
    re.compile(r"\|\s*Supabase\s*\|\s*Vercel\b"),
    re.compile(r"deploy\\nVercel", re.IGNORECASE),  # nó Mermaid "intellix:deploy\nVercel"
    re.compile(r"\*\.vercel\.app"),
    re.compile(r"\+\s*Vercel\s*$", re.MULTILINE),
]
VERCEL_ALLOW = re.compile(
    r"vercel-react-best-practices|react-best-practices|não Vercel|no lugar de Vercel|em vez de Vercel"
    r"|exce[cç][aã]o|legado|descontinuad|n[aã]o use"
    r"|grep\s+-q",  # regex de roteamento que só reconhece a palavra no prompt
    re.IGNORECASE,
)


def check_stale_stack() -> None:
    for f in authored_files({".md", ".mmd", ".html", ".json", ".sh"}):
        txt = read(f)
        lines = txt.splitlines()
        reported: set[int] = set()
        for pat in VERCEL_PATS:
            for m in pat.finditer(txt):
                n = line_of(txt, m.start())
                line = lines[n - 1] if n <= len(lines) else ""
                if n in reported or VERCEL_ALLOW.search(line):
                    continue
                reported.add(n)
                add("STACK", f"Vercel como deploy: {rel(f)}:{n}: {line.strip()[:80]}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Cache vestigial de plugin próprio (marketplace `directory` carrega do fonte)
# ─────────────────────────────────────────────────────────────────────────────
def _conteudo_carregavel(root: Path) -> dict[str, bytes]:
    """Arquivos que o runtime usa: manifests, skills, agents, commands, hooks,
    references e templates. Ignora .git, docs gerados e lixo de sistema."""
    pastas = (".claude-plugin", "skills", "agents", "commands", "hooks", "references", "intellix-templates")
    out: dict[str, bytes] = {}
    for pasta in pastas:
        base = root / pasta
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.name != ".DS_Store" and "__pycache__" not in p.parts:
                try:
                    out[str(p.relative_to(root))] = p.read_bytes()
                except OSError:
                    continue
    return out


def check_plugin_cache_drift() -> None:
    """Achado de 2026-09-16 (P1-5): `claude plugin update` em marketplace do tipo
    `directory` cria uma cópia em plugins/cache/<mkt>/<plugin>/<versão> e aponta o
    installPath para ela. A conclusão de 2026-09-07 ("carrega do fonte") valia
    quando o installPath não existia. Com a cópia presente, editar o fonte sem
    rodar `claude plugin update` deixa a edição inerte — então o check compara a
    cópia registrada com o fonte e acusa divergência."""
    inst = (load_json(PLUGINS / "installed_plugins.json") or {}).get("plugins") or {}
    for o in OWNED:
        fonte = owned_dir(o)
        man = load_json(fonte / ".claude-plugin" / "plugin.json") or {}
        name = man.get("name")
        if not name:
            continue
        for e in inst.get(f"{name}@{o}") or []:
            cache = Path(str(e.get("installPath", "")))
            if not cache.is_dir() or cache.resolve() == fonte.resolve():
                continue
            a, b = _conteudo_carregavel(fonte), _conteudo_carregavel(cache)
            dif = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            if dif:
                amostra = ", ".join(dif[:4]) + (f" (+{len(dif) - 4})" if len(dif) > 4 else "")
                add("PLUGIN", f"{name}: cópia instalada em {cache} difere do fonte em {len(dif)} arquivo(s) "
                              f"[{amostra}] — suba a versão e rode `claude plugin update {name}@{o}` + reinício")
        cdir = PLUGINS / "cache" / o / name
        if cdir.is_dir():
            registradas = {Path(str(e.get("installPath", ""))).name for e in inst.get(f"{name}@{o}") or []}
            velhas = sorted(d.name for d in cdir.iterdir() if d.is_dir() and d.name not in registradas)
            if velhas:
                add("PLUGIN", f"{name}: versões antigas sem registro em plugins/cache ({', '.join(velhas)}) — podem ser removidas")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Numeração de fases divergente entre MASTER-ARCHITECTURE e master-workflow
# ─────────────────────────────────────────────────────────────────────────────
def _normalize_phase_label(label: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", label.lower())
    return re.sub(r"[^a-z]", "", s.encode("ascii", "ignore").decode())


def _same_phase(a: str, b: str) -> bool:
    from difflib import SequenceMatcher

    if a == b or a in b or b in a:
        return True
    if SequenceMatcher(None, a, b).ratio() >= 0.6:
        return True
    for size in range(min(len(a), len(b)), 5, -1):
        if any(a[i : i + size] in b for i in range(len(a) - size + 1)):
            return True
    return False


def check_phase_numbering() -> None:
    root = owned_dir("intellix-plugin")
    arch, flow = root / "MASTER-ARCHITECTURE.md", root / "skills/master-workflow/SKILL.md"
    if not (arch.is_file() and flow.is_file()):
        return
    pats = [
        re.compile(r"\[FASE\s*(\d{2}[a-z]?)\]\s+([A-Za-z][A-Za-z -]{3,}?)\s{2,}", re.MULTILINE),
        re.compile(r"###\s*FASE\s*(\d{2}[a-z]?)\s*[—\-–]\s*([A-Za-z][A-Za-z -]{3,})"),
        re.compile(r"\[(\d{2}[a-z]?)\]\s+([a-z][a-z-]{3,})"),
    ]

    def phases(p: Path) -> dict[str, str]:
        txt, out = read(p), {}
        for pat in pats:
            for m in pat.finditer(txt):
                out.setdefault(m.group(1), _normalize_phase_label(m.group(2)))
        return out

    a, f = phases(arch), phases(flow)
    for num in sorted(set(a) & set(f)):
        if not _same_phase(a[num], f[num]):
            add("FASE", f"fase {num}: MASTER-ARCHITECTURE='{a[num]}' vs master-workflow='{f[num]}'")


# ─────────────────────────────────────────────────────────────────────────────
# 7 / 13. Gatilhos e listas de skills apontando para o que não carrega
# ─────────────────────────────────────────────────────────────────────────────
def check_trigger_skills() -> None:
    f = ROOT / "modules" / "new-skills-triggers.md"
    if f.is_file():
        txt = read(f)
        for m in re.finditer(r"^####\s+`([a-z0-9:_-]+)`", txt, re.MULTILINE):
            if not ref_exists(m.group(1)):
                add("TRIGGER", f"gatilho para skill que não carrega `{m.group(1)}` — "
                               f"new-skills-triggers.md:{line_of(txt, m.start())}")
        for m in re.finditer(r"^####\s+`[a-z0-9:_*-]+`\s*\(\+?\s*([^)]+)\)", txt, re.MULTILINE):
            for n in re.split(r",\s*", m.group(1)):
                n = n.strip().strip("`")
                if re.fullmatch(r"[a-z0-9:_-]+", n) and not ref_exists(n):
                    add("TRIGGER", f"gatilho para skill que não carrega `{n}` — "
                                   f"new-skills-triggers.md:{line_of(txt, m.start())}")
        # avisos manuais: "rode /xxx"
        for m in re.finditer(r"\brode\s+`?/([a-z0-9][a-z0-9:_-]*)", txt):
            if not ref_exists(m.group(1)):
                add("TRIGGER", f"aviso manda rodar `/{m.group(1)}`, que não carrega — "
                               f"new-skills-triggers.md:{line_of(txt, m.start())}")
        # nomes citados como skills paralelas/redundantes: "- `nome` →"
        for m in re.finditer(r"^-\s+`([a-z0-9][a-z0-9:_-]*)`\s+→", txt, re.MULTILINE):
            if not ref_exists(m.group(1)):
                add("TRIGGER", f"skill citada que não carrega `{m.group(1)}` — "
                               f"new-skills-triggers.md:{line_of(txt, m.start())}")

    # Lista <complementary-skills> injetada pelo SessionStart do IntelliX.
    ss = owned_dir("intellix-plugin") / "hooks/scripts/session-start.sh"
    txt = read(ss)
    blk = re.search(r"<complementary-skills>(.*?)</complementary-skills>", txt, re.DOTALL)
    if blk:
        for m in re.finditer(r"^\s*-\s+(.+?)\s+→", blk.group(1), re.MULTILINE):
            name = m.group(1).strip()
            if not ref_exists(name):
                add("TRIGGER", f"session-start.sh lista skill que não carrega `{name}` — "
                               f"{rel(ss)}:{line_of(txt, blk.start(1) + m.start())}")

    # Router global: sugestão a skill com disable-model-invocation é inexequível.
    router = ROOT / "scripts" / "intellix-skill-router.py"
    rtxt = read(router)
    for m in re.finditer(r'\(\s*\d+\s*,\s*"([a-z0-9:_-]+)"', rtxt):
        ref = m.group(1)
        ns, _, name = ref.partition(":")
        if not ref_exists(ref):
            add("TRIGGER", f"router sugere `{ref}`, que não carrega — {rel(router)}:{line_of(rtxt, m.start())}")
        elif (ns, name) in NO_MODEL:
            add("TRIGGER", f"router sugere `{ref}`, mas ela tem disable-model-invocation "
                           f"(o modelo não consegue invocar) — {rel(router)}:{line_of(rtxt, m.start())}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Conformidade com metodologia.yaml
# ─────────────────────────────────────────────────────────────────────────────
def check_metodologia() -> None:
    if not META:
        return
    intellix_ids = INTELLIX.ids() if INTELLIX else set()
    for fase in (META.get("fases") or []) + (META.get("modulos_opcionais") or []):
        skill = fase.get("skill")
        fid = fase.get("id", fase.get("nome", "?"))
        if skill and skill not in intellix_ids:
            add("META", f"fase {fid} aponta para skill inexistente no plugin intellix: '{skill}'")
        for par in fase.get("skills_paralelas") or []:
            if not ref_exists(par):
                add("META", f"fase {fid} referencia skill paralela que não carrega: '{par}'")

    arch = owned_dir("intellix-plugin") / "MASTER-ARCHITECTURE.md"
    if arch.is_file():
        txt = read(arch)
        declaradas = {
            m.group(1): _normalize_phase_label(m.group(2))
            for m in re.finditer(r"\[FASE\s*(\d{2}[a-z]?)\]\s+([A-Za-z][A-Za-z /-]{3,}?)\s{2,}", txt)
        }
        for fase in META.get("fases") or []:
            fid, nome = fase.get("id"), _normalize_phase_label(fase.get("nome", ""))
            if fid in declaradas and not _same_phase(declaradas[fid], nome):
                add("META", f"fase {fid}: metodologia.yaml='{nome}' vs MASTER-ARCHITECTURE='{declaradas[fid]}'")

    deploy = str((META.get("stack") or {}).get("deploy", ""))
    dev_rules = ROOT / "modules" / "dev-rules.md"
    if deploy and dev_rules.is_file() and deploy.split()[0].lower() not in read(dev_rules).lower():
        add("META", f"stack.deploy='{deploy}' não aparece em modules/dev-rules.md")

    contrato = META.get("agentes") or {}
    esperados = [n for grupo in contrato.values() for n in (grupo or [])]
    if esperados and INTELLIX:
        for nome in esperados:
            if nome not in INTELLIX.agents:
                add("META", f"agente '{nome}' do contrato (metodologia.yaml → agentes) não existe em intellix-plugin/agents/")

    for perfil in META.get("auditorias") or []:
        for chave in ("skill", "comando"):
            ref = str(perfil.get(chave) or "").lstrip("/")
            if ref and not ref_exists(ref):
                add("META", f"auditoria '{perfil.get('perfil')}' aponta para {chave} que não carrega: '{ref}'")

    for p in META.get("plugins_proprios") or []:
        if not owned_dir(str(p.get("diretorio", ""))).is_dir():
            add("META", f"plugin próprio '{p.get('diretorio')}' declarado no YAML mas não existe")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Paths locais citados em arquivos autorais precisam resolver
# ─────────────────────────────────────────────────────────────────────────────
def _artefatos() -> set[str]:
    a = META.get("artefatos_projeto") or {}
    return {str(x).rstrip("/") for grupo in a.values() for x in (grupo or [])}


def _deps() -> set[str]:
    return {str(x) for x in (META.get("dependencias_globais") or [])}


def check_local_paths() -> None:
    artefatos, deps = _artefatos(), _deps()
    pat_link = re.compile(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")
    pat_refs = re.compile(r"(?<![\w/.-])references/([A-Za-z0-9_.-]+\.md)")
    pat_mod = re.compile(r"(?<![\w/.-])(?:~/\.claude/)?modules/([A-Za-z0-9_.-]+\.md)")
    pat_tpl = re.compile(r"(?<![\w/.-])(intellix-templates/[A-Za-z0-9_./-]*[A-Za-z0-9_])")
    pat_hook = re.compile(r"(?<![\w/.-])(hooks/scripts/[A-Za-z0-9_.-]+\.(?:sh|py))")
    pat_spine = re.compile(r"WORKFLOW-SPINE-VS-ORBIT\.md")
    for o in OWNED:
        root = owned_dir(o)
        for f in iter_files(root, {".md", ".sh", ".json", ".html"}):
            txt = read(f)

            def bad(pos: int, msg: str) -> None:
                add("PATH", f"{msg} — {rel(f)}:{line_of(txt, pos)}")

            for m in pat_link.finditer(txt):
                target = m.group(1)
                if target.startswith(("http", "mailto:")):
                    continue
                if not ((f.parent / target).exists() or (root / target).exists()):
                    bad(m.start(), f"link para arquivo inexistente `{target}`")
            for m in pat_refs.finditer(txt):
                name = m.group(1)
                ok = (root / "references" / name).is_file() or (f.parent / "references" / name).is_file() \
                    or f"references/{name}" in artefatos
                if not ok:
                    bad(m.start(), f"`references/{name}` não existe no plugin nem em artefatos_projeto")
            for m in pat_mod.finditer(txt):
                dep = f"modules/{m.group(1)}"
                if not (ROOT / dep).is_file():
                    bad(m.start(), f"`{dep}` não existe em ~/.claude")
                elif dep not in deps:
                    bad(m.start(), f"`{dep}` usado pelo plugin mas não declarado em dependencias_globais")
            for m in pat_spine.finditer(txt):
                if "WORKFLOW-SPINE-VS-ORBIT.md" not in deps:
                    bad(m.start(), "WORKFLOW-SPINE-VS-ORBIT.md usado mas não declarado em dependencias_globais")
            for m in pat_tpl.finditer(txt):
                if not (root / m.group(1)).exists():
                    bad(m.start(), f"`{m.group(1)}` não existe no plugin")
            for m in pat_hook.finditer(txt):
                if not (root / m.group(1)).exists():
                    bad(m.start(), f"`{m.group(1)}` não existe no plugin")


# ─────────────────────────────────────────────────────────────────────────────
# 10. `name:` do frontmatter igual à pasta (ID real do runtime)
# ─────────────────────────────────────────────────────────────────────────────
def check_frontmatter_ids() -> None:
    for p in PLUGINS_LOADED.values():
        if not p.owned:
            continue
        for sid, md in sorted(p.skills.items()):
            name = frontmatter(md).get("name")
            if name != sid:
                add("ID", f"{p.ns}: pasta `{sid}` declara name: `{name}` — o runtime usa "
                          f"`{p.ns}:{sid}`; alinhe o frontmatter ({rel(md)})")


# ─────────────────────────────────────────────────────────────────────────────
# 11. Versões dos plugins próprios
# ─────────────────────────────────────────────────────────────────────────────
PAT_VER_HEADER = re.compile(r"(?:Plugin|Hook|Engineering Plugin|IntelliX)[^\n]{0,40}?\bv(\d+\.\d+)(?:\.\d+)?\b")
PAT_VER_DOC = re.compile(r"\*\*Vers[aã]o:\*\*\s*(\d+\.\d+)")


def check_versions() -> None:
    esperadas = META.get("versoes") or {}
    inst = (load_json(PLUGINS / "installed_plugins.json") or {}).get("plugins") or {}
    for o in OWNED:
        root = owned_dir(o)
        man = load_json(root / ".claude-plugin" / "plugin.json")
        mkt = load_json(root / ".claude-plugin" / "marketplace.json")
        if not isinstance(man, dict):
            add("VERSAO", f"{o}: plugin.json ausente ou inválido")
            continue
        name, ver = man.get("name"), str(man.get("version", ""))
        if name in esperadas and str(esperadas[name]) != ver:
            add("VERSAO", f"{name}: plugin.json={ver} vs metodologia.yaml versoes={esperadas[name]}")
        if isinstance(mkt, dict):
            for e in mkt.get("plugins") or []:
                if e.get("name") == name and str(e.get("version", ver)) != ver:
                    add("VERSAO", f"{name}: marketplace.json={e.get('version')} vs plugin.json={ver}")
        for e in inst.get(f"{name}@{o}") or []:
            if str(e.get("version")) != ver:
                add("VERSAO", f"{name}@{o}: registro de instalação diz {e.get('version')}, "
                              f"plugin.json diz {ver} — reinstale pela CLI (`claude plugin update`)")
            if e.get("installPath") and not Path(str(e["installPath"])).exists():
                add("VERSAO", f"{name}@{o}: installPath inexistente no registro ({e['installPath']})")
        mm = ".".join(ver.split(".")[:2])
        for f in iter_files(root, {".md", ".sh"}):
            txt = read(f)
            # Só documentos que descrevem o PLUGIN; formulários e playbooks têm versão própria.
            pats = []
            if f.name in ("README.md", "WORKFLOW-DOCUMENTATION.md"):
                pats.append(PAT_VER_DOC)
            if f.suffix == ".sh" or f.name == "README.md":
                pats.append(PAT_VER_HEADER)
            for pat in pats:
                for m in pat.finditer(txt):
                    if m.group(1) != mm:
                        n = line_of(txt, m.start())
                        if f.name == "README.md" and n > 3:
                            continue
                        add("VERSAO", f"{name}: {rel(f)}:{n} cita v{m.group(1)}, plugin é {ver}")


# ─────────────────────────────────────────────────────────────────────────────
# 12. Nomes legados fora da tabela de compatibilidade
# ─────────────────────────────────────────────────────────────────────────────
def check_legacy_aliases() -> None:
    aliases = META.get("aliases_legados") or []
    if not aliases:
        return
    compiled = [
        (a["antigo"], a.get("canonico", "?"),
         re.compile(r"(?<![\w-])" + re.escape(str(a["antigo"])) + r"(?![\w-])"))
        for a in aliases if a.get("antigo")
    ]
    allow = re.compile(r"legad|alias", re.IGNORECASE)
    for f in authored_files():
        txt = read(f)
        lines = txt.splitlines()
        for antigo, canon, pat in compiled:
            for m in pat.finditer(txt):
                n = line_of(txt, m.start())
                if n <= len(lines) and allow.search(lines[n - 1]):
                    continue
                add("ALIAS", f"nome legado `{antigo}` (use {canon}) — {rel(f)}:{n}")


# ─────────────────────────────────────────────────────────────────────────────
# 14. Gates só exigem artefatos declarados
# ─────────────────────────────────────────────────────────────────────────────
def check_gate_artifacts() -> None:
    artefatos = _artefatos()
    if not artefatos:
        return
    gate = owned_dir("intellix-plugin") / "hooks/scripts/phase-gate.sh"
    txt = read(gate)
    for m in re.finditer(r'exigir_(?:arquivo|dir_nao_vazio)\s+"([^"]+)"', txt):
        if m.group(1).rstrip("/") not in artefatos:
            add("GATE", f"phase-gate exige `{m.group(1)}`, ausente de artefatos_projeto — "
                        f"{rel(gate)}:{line_of(txt, m.start())}")


# ─────────────────────────────────────────────────────────────────────────────
# 15. Dependências globais existem
# ─────────────────────────────────────────────────────────────────────────────
def check_global_deps() -> None:
    for dep in sorted(_deps()):
        if not (ROOT / dep).exists():
            add("DEP", f"dependência global declarada não existe: {dep}")


# ─────────────────────────────────────────────────────────────────────────────
# 17. Arquivos/pastas acidentais nas áreas autorais
# ─────────────────────────────────────────────────────────────────────────────
def check_accidental_files() -> None:
    bases = [owned_dir(o) for o in OWNED] + [ROOT / "modules", ROOT / "scripts"]
    bases += [ROOT / "skills" / s for s in (META.get("skills_autorais_globais") or [])]
    for base in bases:
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if "/.git/" in str(p) or p.name == ".git":
                continue
            if "{" in p.name or "}" in p.name:
                add("LIXO", f"nome acidental (brace expansion?): {rel(p)}")
            elif re.search(r"\.(bak|orig|rej)$|\.bak-|~$", p.name):
                add("LIXO", f"backup solto em área autoral: {rel(p)}")


# ─────────────────────────────────────────────────────────────────────────────
# 18. Skill e comando com o mesmo ID no mesmo plugin
# ─────────────────────────────────────────────────────────────────────────────
def check_id_collisions() -> None:
    for p in PLUGINS_LOADED.values():
        if p.owned:
            for dup in sorted(set(p.skills) & set(p.commands)):
                add("ID", f"{p.ns}:{dup} é ao mesmo tempo skill e comando — IDs colidem no runtime")


# ─────────────────────────────────────────────────────────────────────────────
# 19. Fases anunciadas no banner de sessão × metodologia.yaml
# ─────────────────────────────────────────────────────────────────────────────
def check_banner_phases() -> None:
    fases = {str(f.get("id")): f.get("skill") for f in META.get("fases") or []}
    if not fases:
        return
    ss = owned_dir("intellix-plugin") / "hooks/scripts/session-start.sh"
    txt = read(ss)
    for m in re.finditer(r"intellix:([a-z0-9-]+)\s+→\s+fase\s+(\d{2}[a-z]?)", txt):
        skill, fid = m.group(1), m.group(2)
        if fases.get(fid) != skill:
            esperado = fases.get(fid, "fase inexistente no YAML")
            add("FASE", f"banner diz fase {fid}={skill}, metodologia.yaml diz {esperado} — "
                        f"{rel(ss)}:{line_of(txt, m.start())}")


# ─────────────────────────────────────────────────────────────────────────────
# 20. Hooks que injetam contexto não podem ser async (contrato em metodologia.yaml)
# ─────────────────────────────────────────────────────────────────────────────
EVENTOS_DE_CONTEXTO = ("SessionStart", "UserPromptSubmit")


def check_async_context_hooks() -> None:
    for o in OWNED:
        f = owned_dir(o) / "hooks" / "hooks.json"
        data = load_json(f)
        if not isinstance(data, dict):
            if f.is_file():
                add("HOOK", f"hooks.json inválido: {rel(f)}")
            continue
        for evento in EVENTOS_DE_CONTEXTO:
            for grupo in (data.get("hooks") or {}).get(evento) or []:
                for h in grupo.get("hooks") or []:
                    if h.get("type") == "command" and h.get("async") is True:
                        add("HOOK", f"{rel(f)}: hook de {evento} com async:true — a saída não chega ao "
                                    f"modelo; use async:false ({h.get('command', '')[:60]})")


# ─────────────────────────────────────────────────────────────────────────────
# 21. Hook que BLOQUEIA ferramenta não pode ser julgado por LLM
# ─────────────────────────────────────────────────────────────────────────────
EVENTOS_BLOQUEANTES = ("PreToolUse", "PostToolUse")


def check_prompt_blocking_hooks() -> None:
    """Achado de 2026-09-18/20: o gate de qualidade TS era `type: prompt`.

    Num hook bloqueante, o harness trata qualquer resposta que não seja o
    literal esperado como bloqueio. Como o juiz é um LLM, ele erra: um
    arquivo .py foi barrado por "estar fora do escopo de validação", e o
    Write/Edit parou em TODO arquivo não-TS/JS, em todo projeto.

    Regra: o que bloqueia é código determinístico (`type: command`), que
    falha aberto. Julgamento de conteúdo por LLM pertence à revisão
    (code-quality-reviewer, gate de pré-deploy), não ao caminho crítico de
    cada escrita. Ver docstring de hooks/scripts/ts-quality-gate.py.
    """
    for o in OWNED:
        f = owned_dir(o) / "hooks" / "hooks.json"
        data = load_json(f)
        if not isinstance(data, dict):
            continue
        for evento in EVENTOS_BLOQUEANTES:
            for grupo in (data.get("hooks") or {}).get(evento) or []:
                for h in grupo.get("hooks") or []:
                    if h.get("type") == "prompt":
                        add("HOOK", f"{rel(f)}: hook de {evento} com type:prompt — um LLM no caminho "
                                    f"crítico de cada escrita bloqueia por engano; use type:command "
                                    f"com script determinístico que falha aberto")


# ─────────────────────────────────────────────────────────────────────────────
# Execução — nunca deixa exceção escapar (roda em todo SessionStart)
# ─────────────────────────────────────────────────────────────────────────────
CHECKS = [
    ("referências", check_dangling_refs),
    ("symlinks", check_broken_symlinks),
    ("duplicatas", check_duplicate_names),
    ("stack", check_stale_stack),
    ("cache de plugin", check_plugin_cache_drift),
    ("numeração de fases", check_phase_numbering),
    ("gatilhos e listas de skills", check_trigger_skills),
    ("metodologia.yaml", check_metodologia),
    ("paths locais", check_local_paths),
    ("IDs de frontmatter", check_frontmatter_ids),
    ("versões", check_versions),
    ("nomes legados", check_legacy_aliases),
    ("artefatos dos gates", check_gate_artifacts),
    ("dependências globais", check_global_deps),
    ("arquivos acidentais", check_accidental_files),
    ("colisão de IDs", check_id_collisions),
    ("fases do banner", check_banner_phases),
    ("hooks de contexto", check_async_context_hooks),
    ("hooks bloqueantes", check_prompt_blocking_hooks),
]


def main() -> int:
    for label, fn in CHECKS:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — hook nunca pode derrubar a sessão
            add("ERRO", f"check '{label}' falhou: {type(e).__name__}: {e}")

    if not findings:
        if not QUIET:
            print(f"[DOCTOR] Metodologia consistente — {len(KNOWN_BARE)} skills carregáveis, "
                  f"{len(CHECKS)} verificações OK.")
        return 0

    by_cat: dict[str, list[str]] = {}
    for cat, msg in findings:
        by_cat.setdefault(cat, []).append(msg)

    limit = 10_000 if STRICT else 12
    print(f"[DOCTOR] {len(findings)} achado(s) de consistência:")
    for cat in sorted(by_cat):
        print(f"  {cat} ({len(by_cat[cat])}):")
        for msg in by_cat[cat][:limit]:
            print(f"    - {msg}")
        if len(by_cat[cat]) > limit:
            print(f"    ... +{len(by_cat[cat]) - limit} adicional(is) (rode com --strict para ver todos)")
    print("[DOCTOR] Contexto de cada check: docstrings de scripts/doctor.py")
    return 1 if STRICT else 0


if __name__ == "__main__":
    sys.exit(main())
