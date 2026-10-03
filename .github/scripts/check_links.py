import glob
import os
import re
import time

import requests
import yaml

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# Domínios que bloqueiam checagem automática com frequência —
# se derem erro, caem em "não verificável" em vez de "quebrado".
BLOCKING_DOMAINS = [
    "amazon.com",
    "amzn.to",
    "mercadolivre.com",
    "mercadolibre.com",
    "meli.la",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def load_products():
    products = []
    for path in sorted(glob.glob("_promocoes/*.md")):
        with open(path, encoding="utf-8") as f:
            content = f.read()
        m = FRONT_MATTER_RE.match(content)
        if not m:
            continue
        data = yaml.safe_load(m.group(1)) or {}
        title = data.get("title", path)
        link = data.get("link")
        if link:
            products.append((title, link))
    return products


def is_blocking_domain(url):
    return any(d in url for d in BLOCKING_DOMAINS)


def check(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return r.status_code
    except requests.RequestException:
        return None


def main():
    products = load_products()
    ativos, quebrados, nao_verificaveis = [], [], []

    for title, link in products:
        status = check(link)
        time.sleep(1)  # não martelar os servidores das lojas

        if status is not None and 200 <= status < 400:
            ativos.append((title, link, status))
        elif status in (403, 429, 503, 999) or (status is None and is_blocking_domain(link)):
            nao_verificaveis.append((title, link, status))
        else:
            quebrados.append((title, link, status))

    gh_output = os.environ.get("GITHUB_OUTPUT")

    if not quebrados and not nao_verificaveis:
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(f"Checados **{len(ativos)}** links — todos ativos, nenhum quebrado ou suspeito dessa vez.")
        if gh_output:
            with open(gh_output, "a", encoding="utf-8") as f:
                f.write("has_findings=false\n")
        return

    lines = [
        f"**{len(ativos)} ativos** · **{len(quebrados)} quebrados** · **{len(nao_verificaveis)} não verificáveis**",
        "",
    ]

    if quebrados:
        lines.append("### ❌ Quebrados (ação necessária)")
        for title, link, status in quebrados:
            lines.append(f"- **{title}** — status `{status}` — {link}")
        lines.append("")

    if nao_verificaveis:
        lines.append("### ⚠️ Não verificáveis (a loja bloqueou a checagem — confirma na mão)")
        for title, link, status in nao_verificaveis:
            lines.append(f"- **{title}** — status `{status}` — {link}")
        lines.append("")

    lines.append(f"### ✅ Ativos confirmados ({len(ativos)})")
    lines.append("<details><summary>ver lista</summary>")
    lines.append("")
    for title, link, status in ativos:
        lines.append(f"- {title}")
    lines.append("")
    lines.append("</details>")

    with open("report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write("has_findings=true\n")


if __name__ == "__main__":
    main()
