import glob
import os
import re
import time

import requests
import yaml

FRONT_MATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)

# O GitHub aceita no máximo 65536 caracteres no corpo de uma issue.
MAX_BODY = 60000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def parse_front_matter(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = FRONT_MATTER_RE.match(content)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else {}


def check_link(url):
    """Só 404/410 contam como quebrado. Qualquer outro problema vira 'não verificável'."""
    last_error = None
    for _ in range(2):  # uma segunda tentativa pra falha de rede passageira
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
            status = resp.status_code
            if 200 <= status < 400:
                return "ativo", status
            if status in (404, 410):
                return "quebrado", status
            return "nao_verificavel", status
        except requests.RequestException as exc:
            last_error = type(exc).__name__
            time.sleep(2)
    return "nao_verificavel", last_error


def format_section(emoji, title, entries, empty_msg):
    lines = ["", f"## {emoji} {title} ({len(entries)})", ""]
    if entries:
        lines.extend(f"- {e}" for e in entries)
    else:
        lines.append(f"_{empty_msg}_")
    return lines


def main():
    files = sorted(glob.glob("_promocoes/*.md"))
    ativos, quebrados, nao_verificaveis, ignorados = [], [], [], []

    for path in files:
        data = parse_front_matter(path)
        link = ((data or {}).get("link") or "").strip()
        if not link:
            ignorados.append(path)
            continue

        nome = data.get("title", path)
        group, detail = check_link(link)
        time.sleep(1)  # não martelar os servidores das lojas

        if group == "ativo":
            ativos.append(nome)
        else:
            entry = f"**{nome}**  \n  {link}  \n  status: `{detail}` · arquivo: `{path}`"
            if group == "quebrado":
                quebrados.append(entry)
            else:
                nao_verificaveis.append(entry)

    total = len(ativos) + len(quebrados) + len(nao_verificaveis)

    head = [
        "# Verificação de links de afiliado",
        "",
        f"Arquivos em `_promocoes/`: **{len(files)}** · verificados: **{total}** · ignorados (sem link): **{len(ignorados)}**",
        "",
        f"✅ **{len(ativos)}** ativos · ❌ **{len(quebrados)}** quebrados · ⚠️ **{len(nao_verificaveis)}** não verificáveis",
    ]
    head += format_section("❌", "Quebrados — precisam de ação (404/410)", quebrados, "nenhum 🎉")
    head += format_section("⚠️", "Não verificáveis — checar manualmente", nao_verificaveis, "nenhum")

    if ignorados:
        head += ["", f"## Arquivos ignorados ({len(ignorados)})", ""]
        head += [f"- `{p}`" for p in ignorados[:20]]
        if len(ignorados) > 20:
            head.append(f"- ... e mais {len(ignorados) - 20}")

    head_text = "\n".join(head)

    ativos_section = "\n".join(
        ["", f"## ✅ Ativos ({len(ativos)})", "", "<details><summary>ver lista</summary>", ""]
        + [f"- {n}" for n in ativos]
        + ["", "</details>"]
    )

    body = head_text + "\n" + ativos_section
    if len(body) > MAX_BODY:
        body = head_text + f"\n\n_Lista de ativos omitida por tamanho ({len(ativos)} produtos)._"
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY] + "\n\n_Relatório cortado por tamanho._"

    with open("relatorio-links.md", "w", encoding="utf-8") as f:
        f.write(body)

    # Mostra o resumo direto na página da execução (aba Actions).
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(body)

    print(
        f"Relatório gerado: {total} verificados, {len(quebrados)} quebrados, "
        f"{len(nao_verificaveis)} não verificáveis, {len(ignorados)} ignorados."
    )


if __name__ == "__main__":
    main()
