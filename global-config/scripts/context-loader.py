# -*- coding: utf-8 -*-
import json, sys, os, io
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"
MAX_FILES = 8; MAX_PEND = 5; MAX_DEC = 3

def slug(cwd): return Path(cwd).name.lower().replace(" ","-").replace("_","-")
def mem_dir(cwd):
    s = "C--" + cwd.replace(":","").replace("/","-").replace("\\","-").strip("-")
    return CLAUDE_DIR / "projects" / s / "memory"
def load_session(sl):
    f = SESSIONS_DIR / f"{sl}.json"
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except: pass
    return None
def parse_file(fp):
    if not fp.exists(): return None
    txt = fp.read_text(encoding="utf-8")
    ctx = {"phase":None,"focus":None,"pending":[],"completed":[],"files":[],"decisions":[],"last_updated":None,"is_checkpoint":"checkpoint: true" in txt}
    sec = None
    for line in txt.splitlines():
        s = line.strip()
        if "**Gerado em:**" in s or (s.startswith("**") and "atualiz" in s.lower()):
            ctx["last_updated"] = s.split(":**",1)[-1].strip()
        elif "**Fase IntelliX:**" in s:
            ctx["phase"] = s.replace("**Fase IntelliX:**","").replace("`","").strip()
        elif s.startswith("##"):
            low=s.lower()
            if "pend" in low: sec="pending"
            elif "conclu" in low: sec="completed"
            elif "arquivo" in low: sec="files"
            elif "decis" in low: sec="decisions"
            elif "foco" in low: sec="focus"
            elif "como retomar" in low: sec=None
        elif sec=="focus" and s and not s.startswith("#"):
            if not ctx["focus"]: ctx["focus"]=s
        elif sec=="pending" and s.startswith("- [ ]"):
            ctx["pending"].append(s[6:].strip())
        elif sec=="completed" and s.startswith("- [x]"):
            ctx["completed"].append(s[6:].strip())
        elif sec=="files" and s.startswith("- `"):
            ctx["files"].append(s[3:].rstrip("`"))
        elif sec=="decisions" and s.startswith("- "):
            ctx["decisions"].append(s[2:].strip())
    return ctx if any([ctx["pending"],ctx["phase"],ctx["focus"]]) else None
def load_checkpoint(cwd):
    md = mem_dir(cwd)
    f = md / "context-checkpoint.md"
    if not f.exists(): return None
    ctx = parse_file(f)
    if ctx:
        ctx["is_checkpoint"] = True
        try: f.rename(md / "context-checkpoint.consumed.md")
        except:
            try: f.unlink()
            except: pass
    return ctx
def load_last(cwd): return parse_file(mem_dir(cwd) / "session-context.md")
def intellix_phase(cwd):
    p = Path(cwd)/".intellix-phase"
    return p.read_text(encoding="utf-8").strip() if p.exists() else None
def is_new(cwd):
    fl = SESSIONS_DIR / f"{slug(cwd)}.new_session"
    if fl.exists(): fl.unlink(); return True
    return False
def wants_resume(prompt):
    kws=["retom","continu","onde parei","contexto","estado do projeto","resume","continue","last session"]
    return any(k in prompt.lower() for k in kws)
def chk_msg(ctx):
    L=["\n[CHECKPOINT DE CONTEXTO -- retomada apos limpeza intencional]\n"]
    if ctx.get("phase"): L.append("Fase IntelliX: `"+ctx["phase"]+"`")
    if ctx.get("last_updated"): L.append("Gerado em: "+ctx["last_updated"])
    if ctx.get("focus"): L.append("\nFoco:\n"+ctx["focus"])
    pend=ctx.get("pending",[])
    if pend:
        L.append("\nPendencias ("+str(len(pend))+"):")
        for t in pend[:MAX_PEND]: L.append("  - [ ] "+t)
        if len(pend)>MAX_PEND: L.append("  ... +"+str(len(pend)-MAX_PEND)+" mais")
    files=ctx.get("files",[])
    if files:
        L.append("\nArquivos ("+str(len(files))+"):")
        for f in files[:MAX_FILES]: L.append("  - `"+f+"`")
    decs=ctx.get("decisions",[])
    if decs:
        L.append("\nDecisoes tecnicas:")
        for d in decs[:MAX_DEC]: L.append("  - "+d)
    L.append("\n[FIM DO CHECKPOINT -- continue de onde parou]\n")
    return "\n".join(L)
def ctx_msg(ctx,active,pf):
    L=["\n[CONTEXTO DO PROJETO -- carregado automaticamente]\n"]
    phase=pf or ctx.get("phase") or "--"
    L.append("Fase IntelliX: `"+phase+"`")
    if ctx.get("last_updated"): L.append("Ultima sessao: "+ctx["last_updated"])
    if ctx.get("focus"): L.append("Foco anterior: "+ctx["focus"])
    pend=ctx.get("pending",[])
    if pend:
        L.append("\nPendencias ("+str(len(pend))+"):")
        for t in pend[:MAX_PEND]: L.append("  - [ ] "+t)
        if len(pend)>MAX_PEND: L.append("  ... +"+str(len(pend)-MAX_PEND)+" mais")
    files=[]
    if active:
        recent=active.get("files_created",[])+active.get("files_modified",[])
        files=[f["file"] for f in recent[-MAX_FILES:]]
    elif ctx.get("files"): files=ctx["files"][:MAX_FILES]
    if files:
        L.append("\nArquivos recentes:")
        for f in files: L.append("  - `"+f+"`")
    decs=ctx.get("decisions",[])
    if decs:
        L.append("\nDecisoes tecnicas:")
        for d in decs[:MAX_DEC]: L.append("  - "+d)
    L.append("\n[FIM DO CONTEXTO]\n")
    return "\n".join(L)
def detect_crash(sl,cwd):
    sf=SESSIONS_DIR/f"{sl}.json"
    if not sf.exists(): return False
    try: sess=json.loads(sf.read_text(encoding="utf-8"))
    except: return False
    last=sess.get("last_activity","")
    if not last: return False
    cf=mem_dir(cwd)/"session-context.md"
    if not cf.exists():
        return (len(sess.get("files_created",[]))+len(sess.get("files_modified",[])))>0
    try:
        mtime=datetime.fromtimestamp(cf.stat().st_mtime)
        dt=datetime.fromisoformat(last.replace("Z","+00:00").replace("+00:00",""))
        return dt>mtime
    except: return False
def crash_msg(sess):
    L=["\n[RECUPERACAO DE CRASH -- sessao anterior encerrada abruptamente]\n"]
    if sess.get("current_focus"): L.append("Trabalhando em: "+sess["current_focus"])
    if sess.get("intellix_phase"): L.append("Fase: "+sess["intellix_phase"])
    last=sess.get("last_activity","")[:16].replace("T"," ")
    if last: L.append("Ultima atividade: "+last)
    for t in sess.get("tasks_pending",[])[:5]: L.append("  - [ ] "+t)
    all_f=sess.get("files_created",[])+sess.get("files_modified",[])
    for f in all_f[-MAX_FILES:]: L.append("  - `"+f["file"]+"` as "+f.get("at","?"))
    for d in sess.get("key_decisions",[])[-MAX_DEC:]: L.append("  - "+d)
    L.append("\n[FIM DA RECUPERACAO]\n")
    return "\n".join(L)
def main():
    try: data=json.load(sys.stdin)
    except: sys.exit(0)
    prompt=data.get("prompt","")
    cwd=os.getcwd()
    sl=slug(cwd)
    new=is_new(cwd)
    resume=wants_resume(prompt)
    chk=load_checkpoint(cwd)
    if chk: print(chk_msg(chk)); return
    if not new and not resume: sys.exit(0)
    active=load_session(sl)
    if detect_crash(sl,cwd) and active: print(crash_msg(active)); return
    last=load_last(cwd)
    pf=intellix_phase(cwd)
    if not last and not active and not pf: sys.exit(0)
    ctx=last or {}
    if active and active.get("intellix_phase"): ctx["phase"]=active["intellix_phase"]
    print(ctx_msg(ctx,active,pf))
if __name__=="__main__":
    main()
