"""
Preenche o campo "marcas" dos produtos de _promocoes/ lendo o título.

Uso:
  python tag_brands.py relatorio   -> só mostra o que seria preenchido (não altera nada)
  python tag_brands.py aplicar     -> grava o campo "marcas" nos arquivos

Regras:
  - Um produto pode ter VÁRIAS marcas (ex.: "Placa-Mãe ASRock ... Ryzen" -> ASRock + AMD).
  - Só preenche produtos que estão SEM marcas. O que você já preencheu à mão não é tocado.
  - NVIDIA / AMD / Intel só contam em placa de vídeo, processador, placa-mãe, notebook e kit
    (em cooler ou fonte, "AMD e Intel" é só compatibilidade, não marca).
  - Jogos e gift cards ficam sem marca (o nome da plataforma não é marca do produto).
"""
import glob
import os
import re
import sys
import unicodedata

import yaml

APPLY = len(sys.argv) > 1 and sys.argv[1] == "aplicar"

# (nome que aparece, [padrões no título sem acento e em minúsculas])
BRANDS = [
    ("NVIDIA", [r"\bnvidia\b", r"\bgeforce\b", r"\brtx ?\d{3,4}\b", r"\bgtx ?\d{3,4}\b"]),
    ("AMD", [r"\bamd\b", r"\bryzen\b", r"\bradeon\b", r"\brx ?\d{3,4}\b", r"\bathlon\b", r"\bthreadripper\b", r"\bepyc\b"]),
    ("Intel", [r"\bintel\b", r"\bcore i[3579]\b", r"\bcore ultra\b", r"\bxeon\b", r"\bceleron\b", r"\bpentium\b"]),
    ("ASUS", [r"\basus\b", r"\brog\b", r"\btuf gaming\b", r"\bstrix\b"]),
    ("MSI", [r"\bmsi\b"]),
    ("Gigabyte", [r"\bgigabyte\b", r"\baorus\b"]),
    ("ASRock", [r"\basrock\b"]),
    ("Palit", [r"\bpalit\b"]),
    ("INNO3D", [r"\binno3d\b"]),
    ("Galax", [r"\bgalax\b"]),
    ("Zotac", [r"\bzotac\b"]),
    ("PNY", [r"\bpny\b"]),
    ("Colorful", [r"\bcolorful\b"]),
    ("Sapphire", [r"\bsapphire\b"]),
    ("PowerColor", [r"\bpower ?color\b"]),
    ("XFX", [r"\bxfx\b"]),
    ("Gainward", [r"\bgainward\b"]),
    ("Afox", [r"\bafox\b"]),
    ("Maxsun", [r"\bmaxsun\b"]),
    ("Biostar", [r"\bbiostar\b"]),
    ("EVGA", [r"\bevga\b"]),
    ("Cooler Master", [r"cooler master"]),
    ("Corsair", [r"\bcorsair\b"]),
    ("NZXT", [r"\bnzxt\b"]),
    ("Thermaltake", [r"\bthermaltake\b"]),
    ("DeepCool", [r"\bdeep ?cool\b"]),
    ("Gamemax", [r"\bgamemax\b"]),
    ("Husky", [r"\bhusky\b"]),
    ("Pichau", [r"\bpichau\b"]),
    ("Mancer", [r"\bmancer\b"]),
    ("Kingston", [r"\bkingston\b"]),
    ("Crucial", [r"\bcrucial\b"]),
    ("WD", [r"\bwd\b", r"western digital"]),
    ("Seagate", [r"\bseagate\b"]),
    ("SanDisk", [r"\bsan ?disk\b"]),
    ("Samsung", [r"\bsamsung\b"]),
    ("Lexar", [r"\blexar\b"]),
    ("ADATA", [r"\badata\b"]),
    ("XPG", [r"\bxpg\b"]),
    ("Patriot", [r"\bpatriot\b"]),
    ("Netac", [r"\bnetac\b"]),
    ("Logitech", [r"\blogitech\b"]),
    ("Razer", [r"\brazer\b"]),
    ("SteelSeries", [r"\bsteel ?series\b"]),
    ("HyperX", [r"\bhyperx\b"]),
    ("Redragon", [r"\bredragon\b"]),
    ("Attack Shark", [r"\battack ?shark\b"]),
    ("Clanm", [r"\bclanm\b"]),
    ("Basike", [r"\bbasike\b"]),
    ("Fortrek", [r"\bfortrek\b"]),
    ("Multilaser", [r"\bmultilaser\b"]),
    ("Fantech", [r"\bfantech\b"]),
    ("8BitDo", [r"\b8 ?bit ?do\b"]),
    ("Ipega", [r"\bipega\b"]),
    ("GameSir", [r"\bgame ?sir\b"]),
    ("Kalkan", [r"\bkalkan\b"]),
    ("Mach1", [r"\bmach ?1\b"]),
    ("JBR", [r"\bjbr\b"]),
    ("Elgato", [r"\belgato\b"]),
    ("Edifier", [r"\bedifier\b"]),
    ("Wacom", [r"\bwacom\b"]),
    ("Huion", [r"\bhuion\b"]),
    ("XP-Pen", [r"\bxp-?pen\b"]),
    ("Gaomon", [r"\bgaomon\b"]),
    ("ThunderX3", [r"\bthunderx3\b"]),
    ("DT3 Sports", [r"\bdt3\b"]),
    ("Acer", [r"\bacer\b", r"\bpredator\b"]),
    ("Dell", [r"\bdell\b", r"\balienware\b"]),
    ("Lenovo", [r"\blenovo\b", r"\blegion\b"]),
    ("HP", [r"\bhp\b", r"\bomen\b", r"\bvictus\b"]),
    ("VAIO", [r"\bvaio\b"]),
    ("LG", [r"\blg\b", r"\bultragear\b"]),
    ("AOC", [r"\baoc\b", r"\bagon\b"]),
    ("Philips", [r"\bphilips\b"]),
    ("TCL", [r"\btcl\b"]),
    ("Sony", [r"\bsony\b", r"\bdualsense\b", r"\bdualshock\b"]),
    ("Microsoft", [r"\bmicrosoft\b"]),
    ("Nintendo", [r"\bnintendo\b"]),
    ("Xiaomi", [r"\bxiaomi\b", r"\bredmi\b", r"\bpoco\b"]),
    ("Red Magic", [r"\bred ?magic\b"]),
    ("Apple", [r"\bapple\b", r"\biphone\b", r"\bmacbook\b", r"\bairpods\b"]),
    ("Motorola", [r"\bmotorola\b", r"\bmoto g\b"]),
    ("JBL", [r"\bjbl\b"]),
    ("Amazon", [r"\balexa\b", r"\becho dot\b", r"\becho show\b", r"\bkindle\b", r"\bfire tv\b"]),
]
COMPILED = [(name, [re.compile(p) for p in pats]) for name, pats in BRANDS]

CHIP_BRANDS = {"NVIDIA", "AMD", "Intel"}
CHIP_CATS = {"placas-de-video", "processadores", "placas-mae", "notebooks", "kits"}
SKIP_CATS = {"jogos-keys", "gift-cards"}

FRONT_RE = re.compile(r"\A(---[ \t]*\r?\n)(.*?)(\r?\n---)", re.DOTALL)
MARCAS_RE = re.compile(r"^marcas:[^\r\n]*(?:\r?\n[ \t]+-[^\r\n]*)*", re.M)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def detect(title, categoria):
    if categoria in SKIP_CATS:
        return []
    t = norm(title)
    found = []  # (posição do primeiro aparecimento, marca)
    for name, pats in COMPILED:
        if name in CHIP_BRANDS and categoria not in CHIP_CATS:
            continue
        pos = [m.start() for p in pats for m in [p.search(t)] if m]
        if pos:
            found.append((min(pos), name))
    return [name for _, name in sorted(found)]


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


def set_marcas(text, m, marcas):
    nl = "\r\n" if "\r\n" in text[: m.end()] else "\n"
    block = "marcas:" + nl + nl.join("  - " + b for b in marcas)
    front = m.group(2)
    if MARCAS_RE.search(front):
        front2 = MARCAS_RE.sub(lambda _: block, front, count=1)
    else:
        front2 = front + nl + block
    return text[: m.start(2)] + front2 + text[m.end(2):]


def short(s, n=100):
    s = s.replace("|", "/").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    files = sorted(glob.glob("_promocoes/*.md"))
    marcados = []        # (título, [marcas])
    sem_marca = []       # (título, categoria)
    ja_tinham = 0
    ignorados_cat = 0
    contagem = {}

    for path in files:
        text, m, data = read_product(path)
        if m is None:
            continue
        title = str(data.get("title") or "").strip()
        categoria = str(data.get("categoria") or "").strip()

        atuais = data.get("marcas")
        if isinstance(atuais, list) and len(atuais) > 0:
            ja_tinham += 1
            continue
        if categoria in SKIP_CATS:
            ignorados_cat += 1
            continue

        found = detect(title, categoria)
        if not found:
            sem_marca.append((title, categoria or "(vazia)"))
            continue

        marcados.append((title, found))
        for b in found:
            contagem[b] = contagem.get(b, 0) + 1
        if APPLY:
            new_text = set_marcas(text, m, found)
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)

    lines = [
        "# Marcas dos produtos",
        "",
        "Modo: **APLICADO — arquivos alterados**" if APPLY else "Modo: **RELATÓRIO — nada foi alterado**",
        "",
        f"Produtos lidos: **{len(files)}** · "
        f"{'marcados' if APPLY else 'seriam marcados'}: **{len(marcados)}** · "
        f"sem marca identificada: **{len(sem_marca)}** · "
        f"já tinham marca (não mexi): **{ja_tinham}** · jogos/gift cards (sem marca por regra): **{ignorados_cat}**",
        "",
        "## Marcas encontradas",
        "",
    ]
    lines += [f"- **{b}** — {n}" for b, n in sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0].lower()))]

    if sem_marca:
        lines += ["", f"## ⚠️ Sem marca identificada ({len(sem_marca)}) — me diga a marca que eu adiciono na lista", ""]
        lines += [f"- {short(t)} _(categoria: {c})_" for t, c in sem_marca[:80]]
        if len(sem_marca) > 80:
            lines.append(f"- ... e mais {len(sem_marca) - 80}")

    lines += ["", f"<details><summary>Ver marca de cada produto ({len(marcados)})</summary>", ""]
    lines += [f"- {short(t)} → **{', '.join(ms)}**" for t, ms in marcados]
    lines += ["", "</details>"]

    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
