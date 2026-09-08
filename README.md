# Décima Arte — site

Site estático em Jekyll, pronto pro GitHub Pages.

## Como subir (primeira vez)

1. Cria um repositório novo no GitHub chamado `decimaarte.github.io` **ou** qualquer nome (se for nome diferente, o site fica em `usuario.github.io/nome-do-repo` até você configurar o domínio próprio).
2. Sobe esses arquivos pro repositório:
   ```
   git init
   git add .
   git commit -m "primeira versão do site"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git
   git push -u origin main
   ```
3. No GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → main / (root)**.
4. Ainda em Settings → Pages, em **Custom domain**, coloca `decimaarte.com.br` (o arquivo `CNAME` já existe no projeto, então o GitHub reconhece sozinho).
5. No Registro.br, aponta o domínio pro GitHub Pages: cria os registros DNS tipo A pros IPs do GitHub Pages (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) e um CNAME `www` apontando pra `SEU_USUARIO.github.io`.

## Como testar localmente (opcional, precisa de Ruby instalado)

```
gem install bundler jekyll
bundle exec jekyll serve
```
Abre em `http://localhost:4000`.

## Onde mexer no dia a dia

- **Nova matéria/notícia:** cria um arquivo em `_posts/`, formato `AAAA-MM-DD-titulo.md`, com o cabeçalho (front matter) igual ao post de exemplo.
- **Cores e tema:** `assets/css/style.css`, nas variáveis lá no topo (`:root` = tema light, `[data-theme="dark"]` = tema dark).
- **Menu do site:** `_config.yml`, na lista `nav`.
- **Textos institucionais:** `sobre.html`, `contato.html`, `apoie.html`.
- **Logo:** troca o SVG simplificado (dentro de `_includes/header.html` e `_includes/footer.html`) pelo arquivo oficial quando quiser — ideal é exportar a logo como `.svg` ou `.png` com fundo transparente e trocar a tag `<svg>...</svg>` por `<img src="{{ '/assets/img/logo.png' | relative_url }}">`.

## Ativando a aba "Guias" no futuro

Quando o primeiro guia estiver pronto:
1. Descomenta as linhas de `Guias` no `nav` do `_config.yml`.
2. Usa a collection `_guias` (já configurada) pra criar os arquivos, ou adapta pra posts com categoria `guias`.
