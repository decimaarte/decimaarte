"""
Reclassifica produtos de _promocoes/ em massa, lendo as palavras do título.

Uso:
  python reclassify.py relatorio   -> só mostra o que mudaria (não altera nada)
  python reclassify.py aplicar     -> altera o campo "categoria" nos arquivos

Quais produtos são mexidos:
  - categoria vazia, antiga ("componentes", "perifericos") ou qualquer valor que não esteja na lista nova
  - produtos em "monitores" cujo título é de TV  -> passam para "tvs"
  - produtos em "cadeiras-mesas" cujo título é de mesa -> passam para mesas
Produtos que já estão numa categoria válida NÃO são tocados.

Como decide: procura palavras-chave no título e escolhe a que aparece PRIMEIRO
(o tipo do produto quase sempre vem no começo: "Placa-Mãe ASRock ... Ryzen" -> placas-mae).
"""
import glob
import os
import re
import sys
import unicodedata

import yaml

APPLY = len(sys.argv) > 1 and sys.argv[1] == "aplicar"

LABELS = {
    "placas-de-video": "Placas de Vídeo",
    "processadores": "Processadores",
    "placas-mae": "Placas-Mãe",
    "memoria-ram": "Memória RAM",
    "armazenamento": "Armazenamento",
    "fontes": "Fontes",
    "gabinetes": "Gabinetes",
    "coolers": "Coolers",
    "monitores": "Monitores",
    "tvs": "TVs",
    "teclados": "Teclados",
    "mouses": "Mouses",
    "headsets": "Headsets e Fones",
    "microfones": "Microfones",
    "webcams": "Webcams",
    "mousepads": "Mousepads",
    "suportes-monitor": "Suportes de Monitor",
    "cabos-acessorios": "Cabos e Acessórios",
    "controles": "Controles",
    "cadeiras-mesas": "Cadeiras",
    "mesas-escrivaninhas": "Mesas e Escrivaninhas",
    "mesas-digitalizadoras": "Mesas Digitalizadoras",
    "notebooks": "Notebooks",
    "celulares": "Celulares",
    "consoles": "Consoles",
    "acessorios-console": "Acessórios de Console",
    "kits": "Kits Completos",
    "jogos-keys": "Jogos & Keys",
    "gift-cards": "Gift Cards",
    "pra-quem-ta-comecando": "Pra quem tá começando",
}
VALID = set(LABELS)

# Em caso de empate na posição, vale a regra que aparece primeiro nesta lista.
RULES = [
    ("kits", [r"\bpc (gamer|completo)\b", r"\bcomputador\b", r"\bkit (upgrade|xeon|ryzen|intel|amd|placa)\b"]),
    ("notebooks", [r"\bnotebook\b", r"\blaptop\b", r"\bmacbook\b"]),
    ("suportes-monitor", [r"\b(suporte|braco)\b[^,]{0,25}\bmonitor\b"]),
    ("mesas-digitalizadoras", [r"mesa digitalizadora", r"\btablet grafico\b", r"\bwacom\b", r"\bhuion\b", r"\bxp-?pen\b", r"\bgaomon\b"]),
    ("mesas-escrivaninhas", [r"\bmesa\b", r"\bescrivaninha\b", r"\bbancada\b"]),
    ("cadeiras-mesas", [r"\bcadeira\b", r"\bpoltrona\b"]),
    ("placas-mae", [r"placa[- ]mae", r"\bmotherboard\b"]),
    ("placas-de-video", [r"placa de video", r"placa grafica", r"\bgpu\b", r"\bgeforce\b", r"\bradeon\b", r"\brtx ?\d{3,4}\b", r"\bgtx ?\d{3,4}\b"]),
    ("processadores", [r"processador", r"\bryzen\b", r"\bcore i[3579]\b", r"\bcore ultra\b", r"\bxeon\b", r"\bathlon\b"]),
    ("memoria-ram", [r"memoria ram", r"\bddr[345]\b", r"\bso-?dimm\b", r"\bram\b"]),
    ("armazenamento", [r"\bssd\b", r"\bhdd?\b", r"\bnvme\b", r"pen ?drive", r"cartao de memoria", r"micro ?sd"]),
    ("fontes", [r"\bfonte\b", r"\bpsu\b"]),
    ("gabinetes", [r"\bgabinete\b"]),
    ("coolers", [r"water ?cooler", r"\bcooler\b", r"\bventilador\b", r"\bfans?\b"]),
    ("tvs", [r"\bsmart tv\b", r"\btv\b", r"\btelevisao\b"]),
    ("monitores", [r"\bmonitor\b"]),
    ("teclados", [r"\bteclado\b"]),
    ("mousepads", [r"mouse ?pad"]),
    ("mouses", [r"\bmouse\b"]),
    ("headsets", [r"\bheadset\b", r"\bheadphones?\b", r"fone de ouvido", r"\bfones?\b", r"\btws\b", r"\bearbuds?\b"]),
    ("microfones", [r"\bmicrofone\b"]),
    ("webcams", [r"\bweb ?cam\b"]),
    ("acessorios-console", [r"\bps2\b", r"\bopl\b", r"\bmx4sio\b", r"\bmemory card\b", r"base (de )?carregamento", r"\bdock\b"]),
    ("cabos-acessorios", [r"\bcabos?\b", r"\badaptador\b", r"\bhub\b", r"pasta termica", r"suporte (para|de) (controle|headset|fone)"]),
    ("controles", [r"\bcontrole\b", r"\bgamepad\b", r"\bjoystick\b", r"\bdualsense\b", r"\bdualshock\b", r"\bcontroller\b"]),
    ("consoles", [r"\bconsole\b", r"\bsteam deck\b", r"\brog ally\b"]),
    ("celulares", [r"\bcelular\b", r"\bsmartphone\b", r"\biphone\b", r"\bredmagic\b", r"\bpoco\b", r"\bredmi\b"]),
    ("gift-cards", [r"\bgift card\b", r"cartao presente"]),
    ("jogos-keys", [r"\bjogo\b", r"\bkey\b"]),
]
COMPILED = [(cat, [re.compile(p) for p in pats]) for cat, pats in RULES]

FRONT_RE = re.compile(r"\A(---[ \t]*\r?\n)(.*?)(\r?\n---)", re.DOTALL)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def classify(title):
    t = norm(title)
    best = None  # (posição, índice da regra, categoria)
    for idx, (cat, pats) in enumerate(COMPILED):
        for p in pats:
            m = p.search(t)
            if m:
                cand = (m.start(), idx, cat)
                if best is None or cand < best:
                    best = cand
    return best[2] if best else None


def read_product(path):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    m = FRONT_RE.match(text)
    if not m:
        return text, None, {}
    try:
        data = yaml.safe_load(m.group(2)) or {}
    except yaml.YAMLError:
        return text, None, {}
    return text, m, data if isinstance(data, dict) else {}


def set_categoria(text, m, new):
    front = m.group(2)
    if re.search(r"^categoria:", front, re.M):
        front2 = re.sub(r"^categoria:[^\r\n]*", "categoria: " + new, front, count=1, flags=re.M)
    else:
        front2 = front + "\ncategoria: " + new
    return text[: m.start(2)] + front2 + text[m.end(2):]


def short(s, n=110):
    s = s.replace("|", "/").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    files = sorted(glob.glob("_promocoes/*.md"))
    changes = []     # (arquivo, título, categoria antiga, categoria nova)
    sem_regra = []   # (arquivo, título, categoria antiga)

    for path in files:
        text, m, data = read_product(path)
        if m is None:
            continue
        title = str(data.get("title") or "").strip()
        old = str(data.get("categoria") or "").strip()

        in_scope = (old not in VALID) or old in ("monitores", "cadeiras-mesas")
        if not in_scope:
            continue

        found = classify(title)
        if old == "monitores":
            target = found if found == "tvs" else None
        elif old == "cadeiras-mesas":
            target = found if found in ("mesas-escrivaninhas", "mesas-digitalizadoras") else None
        else:
            target = found

        if target and target != old:
            changes.append((path, title, old or "(vazia)", target))
            if APPLY:
                new_text = set_categoria(text, m, target)
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)
        elif old not in VALID:
            sem_regra.append((path, title, old or "(vazia)"))

    lines = [
        "# Reclassificação de produtos",
        "",
        "Modo: **APLICADO — arquivos alterados**" if APPLY else "Modo: **RELATÓRIO — nada foi alterado**",
        "",
        f"Produtos lidos: **{len(files)}** · "
        f"{'alterados' if APPLY else 'seriam alterados'}: **{len(changes)}** · "
        f"sem regra, ficam como estão (revisar à mão): **{len(sem_regra)}**",
    ]

    by_cat = {}
    for path, title, old, new in changes:
        by_cat.setdefault(new, []).append((title, old))
    for cat in sorted(by_cat, key=lambda c: LABELS.get(c, c)):
        items = by_cat[cat]
        lines += ["", f"## {LABELS.get(cat, cat)} ({len(items)})", ""]
        lines += [f"- {short(t)} _(era: {o})_" for t, o in items]

    if sem_regra:
        lines += ["", f"## ⚠️ Sem regra — revisar manualmente ({len(sem_regra)})", ""]
        lines += [f"- {short(t)} _(categoria atual: {o})_" for _, t, o in sem_regra]

    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
