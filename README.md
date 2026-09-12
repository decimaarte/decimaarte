# Décima Arte — site

Site estático em Jekyll, hospedado no GitHub Pages, domínio próprio: **decimaarte.com.br**.

## Status atual

- ✅ Site no ar em decimaarte.com.br (GitHub Pages + domínio via Registro.br)
- ✅ Painel de edição visual ativo em `/admin` (Sveltia CMS)
- ✅ Newsletter configurada (Beehiiv), com botão no header e CTA ao fim de cada matéria
- 🔧 Sistema de comentários via Supabase — em implementação

## Estrutura do projeto

- `_posts/` — matérias do site (notícias, curiosidades dev, gameplays)
- `_promocoes/` — produtos em promoção/afiliado
- `_data/textos.yml` — textos institucionais reutilizáveis (avisos, introduções, textos de card)
- `_layouts/` — templates (default, post, home, page, category, tag)
- `_includes/` — componentes reutilizáveis (header, footer)
- `assets/css/style.css` — estilo do site (cores no topo, em `:root` = tema light e `[data-theme="dark"]` = tema dark)
- `admin/config.yml` — configuração do painel de edição (Sveltia CMS)

## Onde mexer no dia a dia

**Pelo painel `/admin` (sem tocar em código):**
- Matérias novas, promoções, e as páginas fixas (Sobre, Contato, Apoie o projeto, Política de Privacidade)
- Textos institucionais reutilizáveis (avisos, cards, rodapé)

**Direto no código (mudanças estruturais, não pelo painel):**
- Cores e tema → `assets/css/style.css`
- Menu do site → `_config.yml`, lista `nav`
- Estrutura do header/footer → `_includes/`
- Layout de matérias/páginas → `_layouts/`

## Painel de edição visual — acesso

Acessa `decimaarte.com.br/admin` no navegador e loga com um **token de acesso pessoal (PAT)** do GitHub:

1. GitHub → foto de perfil → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**
2. "Repository access" → **Only select repositories** → seleciona `decimaarte/decimaarte`
3. "Permissions" → "Repository permissions" → **Contents: Read and write**
4. Gera e copia o token (só aparece uma vez — guarda num lugar seguro, nunca em arquivo do repositório)
5. Cola o token na tela de login do `/admin`

**Atenção com edições diretas no GitHub:** o painel e o código-fonte editam os mesmos arquivos. Se for editar algo manualmente no GitHub que também existe no painel (páginas fixas, textos institucionais), sempre baixa a versão mais recente do repositório antes de mexer na cópia local, pra não sobrescrever uma edição feita pelo painel.

## Testar localmente (opcional, precisa de Ruby instalado)

gem install bundler jekyll
bundle exec jekyll serve

Abre em `http://localhost:4000`.

## Ativando a aba "Guias" no futuro

Quando o primeiro guia estiver pronto:
1. Descomenta as linhas de `Guias` no `nav` do `_config.yml`
2. Usa a collection `_guias` (já configurada) pra criar os arquivos, ou adapta pra posts com categoria `guias`
