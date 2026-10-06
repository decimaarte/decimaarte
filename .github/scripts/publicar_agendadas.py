"""
Publica matérias agendadas.

O Jekyll NÃO coloca no ar post com data futura, e o GitHub Pages só reconstrói o site quando
alguém faz um commit. Este script roda de tempos em tempos (veja publicar_agendadas.yml) e:

  1. lê a data de cada matéria em _posts/;
  2. descobre quando foi o último build do site que deu certo;
  3. se existe matéria cuja data caiu DEPOIS desse build e já passou, pede um build novo ao GitHub Pages.

Se não tem nada vencido, não faz nada (não gasta os ~10 builds/hora que o Pages permite).

Uso manual (botão "Run workflow"): marque "forcar" pra pedir um build mesmo sem matéria pendente.
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")   # data sem fuso é lida como horário de Brasília (igual ao _config.yml)
UTC = timezone.utc

DATE_RE = re.compile(
    r"^\s*(\d{4})-(\d{2})-(\d{2})"
    r"(?:[T\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(Z|UTC|[+-]\d{2}:?\d{2}|[+-]\d{2})?)?\s*$",
    re.I,
)
FRONT_RE = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.(?:md|markdown|html)$", re.I)


def parse_date(text):
    """Converte o texto do campo date: em datetime com fuso. None se não entender."""
    m = DATE_RE.match(text.strip().strip("'\""))
    if not m:
        return None
    y, mo, d, hh, mm, ss, off = m.groups()
    hh, mm, ss = int(hh or 0), int(mm or 0), int(ss or 0)
    if off is None:
        tz = BRT
    elif off.upper() in ("Z", "UTC"):
        tz = UTC
    else:
        sign = -1 if off[0] == "-" else 1
        digits = off[1:].replace(":", "")
        oh = int(digits[:2])
        om = int(digits[2:4]) if len(digits) >= 4 else 0
        tz = timezone(sign * timedelta(hours=oh, minutes=om))
    return datetime(int(y), int(mo), int(d), hh, mm, ss, tzinfo=tz).astimezone(UTC)


def read_post(path):
    """Devolve (título, data UTC) ou None se a matéria não vai ao ar (published: false) / sem data."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    fm = FRONT_RE.match(text)
    front = fm.group(1) if fm else ""
    if re.search(r"^published:\s*false\s*$", front, re.I | re.M):
        return None
    title = ""
    mt = re.search(r"^title:\s*(.+?)\s*$", front, re.M)
    if mt:
        title = mt.group(1).strip().strip("'\"")
    md = re.search(r"^date:\s*(.+?)\s*$", front, re.M)
    dt = parse_date(md.group(1)) if md else None
    if dt is None:
        mn = NAME_RE.match(os.path.basename(path))
        if not mn:
            return None
        dt = parse_date("-".join(mn.groups()[:3]))
    return (title or os.path.basename(path), dt)


def load_posts(folder="_posts"):
    posts = []
    for path in sorted(glob.glob(os.path.join(folder, "**", "*.*"), recursive=True)):
        if not NAME_RE.match(os.path.basename(path)):
            continue
        r = read_post(path)
        if r:
            posts.append((r[0], r[1], path))
    return posts


def pick_due(posts, last_build_start, now):
    """Matérias que já passaram da hora e que o último build não pegou."""
    return sorted([p for p in posts if last_build_start < p[1] <= now], key=lambda p: p[1])


def pick_upcoming(posts, now):
    return sorted([p for p in posts if p[1] > now], key=lambda p: p[1])


def gh(*args):
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True)


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def fmt(dt):
    return dt.astimezone(BRT).strftime("%d/%m %H:%M")


def main():
    repo = os.environ["REPO"]
    force = os.environ.get("FORCAR", "").strip().lower() == "true"
    now = datetime.now(UTC)
    posts = load_posts()
    lines = ["## Matérias agendadas", ""]

    last_ok, pending_after = None, False
    r = gh(f"repos/{repo}/pages/builds?per_page=30")
    if r.returncode == 0:
        builds = json.loads(r.stdout or "[]")
        oks = [parse_ts(b["created_at"]) for b in builds if b.get("status") == "built" and b.get("created_at")]
        last_ok = max(oks) if oks else None
        if last_ok:
            pending_after = any(
                b.get("status") in ("queued", "building") and parse_ts(b["created_at"]) >= last_ok
                for b in builds if b.get("created_at")
            )
    else:
        print("Aviso: não consegui listar os builds do Pages:", r.stderr.strip())
    if last_ok is None:
        last_ok = now - timedelta(minutes=45)   # plano B: olha a última meia hora e pouco
        lines.append("_Não achei o último build; usando janela de 45 min._")

    due = pick_due(posts, last_ok, now)
    lines.append(f"Último build ok (início): **{fmt(last_ok)}** (Brasília) · agora: **{fmt(now)}**")
    lines.append("")

    trigger = bool(due) or force
    if due:
        lines.append(f"**Vencidas e fora do ar ({len(due)}):**")
        lines += [f"- {fmt(p[1])} — {p[0]}" for p in due]
    elif force:
        lines.append("Pedido manual: sem matéria pendente, mas vou pedir o build mesmo assim.")
    else:
        lines.append("Nada pendente.")

    if trigger and pending_after and not force:
        lines.append("")
        lines.append("Já existe um build na fila/rodando depois do último ok. Aguardando.")
        trigger = False

    code = 0
    if trigger:
        rr = gh("-X", "POST", f"repos/{repo}/pages/builds")
        lines.append("")
        if rr.returncode == 0:
            lines.append("✅ Build pedido ao GitHub Pages.")
        else:
            code = 1
            lines.append("❌ Não consegui pedir o build: " + (rr.stderr.strip() or rr.stdout.strip()))
            lines.append("Se for erro de permissão (403), crie o segredo PAGES_TOKEN (veja instruções).")

    up = pick_upcoming(posts, now)
    lines += ["", f"**Na fila ({len(up)}):**"]
    lines += [f"- {fmt(p[1])} — {p[0]}" for p in up[:25]] or ["- (nenhuma)"]

    out = "\n".join(lines)
    print(out)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(out + "\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
