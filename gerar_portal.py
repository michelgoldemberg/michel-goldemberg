#!/usr/bin/env python3
"""
Portal Michel Goldemberg — gerador diário.
Busca notícias do dia via API da Anthropic (web search ligado) e grava index.html.
Roda sozinho pelo GitHub Actions às 10h (Brasília).
Visual: editorial minimalista preto e branco.
"""

import os
import json
import html
from datetime import datetime
from zoneinfo import ZoneInfo
import anthropic

# ----------------------------------------------------------------------------
# Configuração de data / fuso
# ----------------------------------------------------------------------------
TZ = ZoneInfo("America/Sao_Paulo")
HOJE = datetime.now(TZ)
DATA_EXTENSO = HOJE.strftime("%d/%m/%Y")

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DATA_BONITA = f"{DIAS[HOJE.weekday()]}, {HOJE.day} de {MESES[HOJE.month-1]} de {HOJE.year}"

# ----------------------------------------------------------------------------
# Prompt de curadoria
# ----------------------------------------------------------------------------
PROMPT = f"""Você é o curador de notícias diário de um portal pessoal. A data de hoje é {DATA_EXTENSO}.

Pesquise na web as notícias e novidades MAIS RELEVANTES DE HOJE (ou das últimas 24-36h) nas cinco categorias abaixo. Quero qualidade e relevância, não volume: no máximo 5 itens por categoria, e se uma categoria não tiver nada relevante hoje, retorne lista vazia.

Contexto sobre o leitor: empreendedor brasileiro, trabalha com revenda de benefícios corporativos e está construindo uma agência de automação com IA (foco em micro-SaaS). Interesses fortes em IA aplicada a negócios, automação, mercado financeiro/investimentos, empreendedorismo, e acompanha de perto a comunidade judaica (Brasil e Israel).

Categorias (use exatamente estas chaves):
- "politica": Política Brasil e internacional, priorizando o que afeta economia, regulação de negócios ou mercado.
- "mercado": Mercado e finanças — bolsa, Selic/juros, câmbio, cripto, fintechs, movimentos relevantes.
- "ia": IA e automação — lançamentos de modelos, ferramentas, agentes (n8n, Claude, GPT etc.) com aplicação prática para negócios.
- "empreendedorismo": Startups, SaaS, cases de crescimento, fundraising, tendências de modelo de negócio.
- "judaica": Comunidade judaica — notícias envolvendo Brasil e Israel (segurança, política, cultura, economia).

Para cada item retorne: titulo, resumo (2-3 frases, direto ao ponto, sem enrolação), fonte (nome do veículo), url (link real da notícia), e importa (uma frase de "por que isso importa pra mim" — só quando fizer sentido, senão deixe vazio).

Responda EXCLUSIVAMENTE com um objeto JSON válido, sem markdown, sem crases, sem nenhum texto antes ou depois. Estrutura:
{{"politica": [{{"titulo": "...", "resumo": "...", "fonte": "...", "url": "...", "importa": "..."}}], "mercado": [...], "ia": [...], "empreendedorismo": [...], "judaica": [...]}}"""

# ----------------------------------------------------------------------------
# Chamada à API com web search
# ----------------------------------------------------------------------------
def buscar_noticias():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
    )
    texto = "".join(
        bloco.text for bloco in resp.content if getattr(bloco, "type", "") == "text"
    ).strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    texto = texto.strip()
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini != -1 and fim != -1:
        texto = texto[ini:fim + 1]
    return json.loads(texto)

# ----------------------------------------------------------------------------
# Ícones SVG minimalistas (preto e branco, traço fino) por seção
# ----------------------------------------------------------------------------
ICONES = {
    "politica": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M24 6v6M10 20h28M12 20v16M36 20v16M19 20v16M29 20v16M8 36h32M6 42h36"/><path d="M24 6l14 14H10z"/></svg>',
    "mercado": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M6 38h36M10 38V24M20 38V16M30 38V26M40 38V10"/><path d="M8 22l10-10 8 8 16-14" stroke-dasharray="0"/><path d="M34 6h8v8"/></svg>',
    "ia": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="16" y="16" width="16" height="16" rx="2"/><path d="M20 16v-6M28 16v-6M20 38v-6M28 38v-6M16 20h-6M16 28h-6M38 20h-6M38 28h-6"/><circle cx="24" cy="24" r="3"/></svg>',
    "empreendedorismo": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M24 4c8 6 12 14 12 22a12 12 0 01-24 0c0-8 4-16 12-22z"/><path d="M24 30c4 0 6-3 6-7s-2-7-6-9c-4 2-6 5-6 9s2 7 6 7z"/><path d="M18 40l-4 4M30 40l4 4M24 42v4"/></svg>',
    "judaica": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M24 6l6 10h-12zM24 42l-6-10h12zM10 16l10 0 6 10-6 10H10l-6-10zM38 16l-10 0-6 10 6 10h10l6-10z"/></svg>',
}

SECOES = [
    ("politica", "Política", "Brasil & mundo"),
    ("mercado", "Mercado & Finanças", "Bolsa, juros, cripto"),
    ("ia", "IA & Automação", "Modelos, agentes, ferramentas"),
    ("empreendedorismo", "Empreendedorismo", "Startups, SaaS, growth"),
    ("judaica", "Comunidade Judaica", "Brasil & Israel"),
]

def esc(s):
    return html.escape(str(s or ""))

def render_item(item, num):
    titulo = esc(item.get("titulo", ""))
    resumo = esc(item.get("resumo", ""))
    fonte = esc(item.get("fonte", ""))
    url = esc(item.get("url", ""))
    importa = esc(item.get("importa", ""))

    titulo_html = f'<a href="{url}" target="_blank" rel="noopener">{titulo}</a>' if url else titulo
    importa_html = f'<p class="importa"><span>Por que importa</span>{importa}</p>' if importa.strip() else ""
    fonte_html = f'<span class="fonte">{fonte}</span>' if fonte.strip() else ""

    return f"""
      <article class="item">
        <span class="num">{num:02d}</span>
        <div class="item-corpo">
          <h3>{titulo_html}</h3>
          <p class="resumo">{resumo}</p>
          {importa_html}
          {fonte_html}
        </div>
      </article>"""

def render_secao(chave, nome, sub, dados, idx):
    itens = dados.get(chave, []) or []
    if not itens:
        corpo = '<p class="vazio">Nada relevante hoje.</p>'
    else:
        corpo = "".join(render_item(i, n + 1) for n, i in enumerate(itens))
    return f"""
    <section class="secao" id="sec-{chave}">
      <header class="secao-head">
        <span class="secao-icon">{ICONES.get(chave, "")}</span>
        <div>
          <h2>{esc(nome)}</h2>
          <p class="secao-sub">{esc(sub)}</p>
        </div>
        <span class="secao-idx">{idx:02d}</span>
      </header>
      <div class="secao-itens">{corpo}</div>
    </section>"""

def montar_html(dados):
    secoes_html = "".join(
        render_secao(c, n, s, dados, i + 1) for i, (c, n, s) in enumerate(SECOES)
    )
    atualizado = HOJE.strftime("%H:%M")
    nav = "".join(
        f'<a href="#sec-{c}">{n}</a>' for c, n, _ in SECOES
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Michel Goldemberg</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;900&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: #0a0a0a;
    --paper: #ffffff;
    --smoke: #6b6b6b;
    --line: #e2e2e2;
    --line-strong: #0a0a0a;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: var(--paper);
    color: var(--ink);
    font-family: "Newsreader", Georgia, serif;
    -webkit-font-smoothing: antialiased;
    line-height: 1.5;
  }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}

  /* ---------- HERO / assinatura ---------- */
  .hero {{
    border-bottom: 2px solid var(--line-strong);
    padding: 56px 0 28px;
  }}
  .hero .eyebrow {{
    font-family: "Archivo", sans-serif;
    font-size: 0.72rem; letter-spacing: 0.34em; text-transform: uppercase;
    color: var(--smoke); margin-bottom: 22px;
  }}
  .hero h1 {{
    font-family: "Archivo", sans-serif;
    font-weight: 900; font-size: clamp(2.6rem, 8vw, 5.2rem);
    letter-spacing: -0.03em; line-height: 0.92; text-transform: uppercase;
  }}
  .hero .risk {{
    display: block;
    font-family: "Newsreader", serif; font-style: italic; font-weight: 400;
    text-transform: none; letter-spacing: -0.01em;
    font-size: clamp(1.1rem, 3.5vw, 1.9rem);
    color: var(--ink); margin-top: 14px;
  }}
  .hero-meta {{
    display: flex; justify-content: space-between; align-items: baseline;
    flex-wrap: wrap; gap: 8px; margin-top: 30px;
    font-family: "Archivo", sans-serif; font-size: 0.78rem;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--smoke);
  }}

  /* ---------- nav ---------- */
  nav.indice {{
    position: sticky; top: 0; z-index: 10;
    background: var(--paper);
    border-bottom: 1px solid var(--line);
    display: flex; gap: 26px; overflow-x: auto;
    padding: 14px 0; margin-bottom: 12px;
  }}
  nav.indice a {{
    font-family: "Archivo", sans-serif; font-size: 0.74rem;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--smoke); text-decoration: none; white-space: nowrap;
    border-bottom: 2px solid transparent; padding-bottom: 2px;
    transition: color .15s, border-color .15s;
  }}
  nav.indice a:hover {{ color: var(--ink); border-color: var(--ink); }}

  /* ---------- seções ---------- */
  .secao {{ padding: 40px 0; border-bottom: 1px solid var(--line); }}
  .secao-head {{
    display: flex; align-items: center; gap: 18px; margin-bottom: 26px;
  }}
  .secao-icon {{ width: 40px; height: 40px; flex: 0 0 40px; color: var(--ink); }}
  .secao-icon svg {{ width: 100%; height: 100%; }}
  .secao-head h2 {{
    font-family: "Archivo", sans-serif; font-weight: 700;
    font-size: 1.5rem; letter-spacing: -0.01em; text-transform: uppercase;
  }}
  .secao-sub {{
    font-family: "Archivo", sans-serif; font-size: 0.72rem;
    letter-spacing: 0.14em; text-transform: uppercase; color: var(--smoke);
    margin-top: 2px;
  }}
  .secao-idx {{
    margin-left: auto; font-family: "Archivo", sans-serif; font-weight: 900;
    font-size: 1.5rem; color: var(--line); letter-spacing: -0.02em;
  }}

  /* ---------- itens ---------- */
  .item {{
    display: grid; grid-template-columns: 44px 1fr; gap: 18px;
    padding: 22px 0; border-top: 1px solid var(--line);
  }}
  .item:first-child {{ border-top: none; }}
  .num {{
    font-family: "Archivo", sans-serif; font-weight: 700; font-size: 0.9rem;
    color: var(--ink); padding-top: 4px;
  }}
  .item h3 {{ font-size: 1.32rem; font-weight: 500; line-height: 1.25; letter-spacing: -0.01em; }}
  .item h3 a {{ color: var(--ink); text-decoration: none; background-image: linear-gradient(var(--ink),var(--ink)); background-size: 0% 1px; background-repeat: no-repeat; background-position: 0 100%; transition: background-size .25s; }}
  .item h3 a:hover {{ background-size: 100% 1px; }}
  .resumo {{ margin-top: 8px; font-size: 1.04rem; color: #222; }}
  .importa {{
    margin-top: 12px; padding-left: 16px; border-left: 2px solid var(--ink);
    font-size: 0.96rem; color: #333;
  }}
  .importa span {{
    display: block; font-family: "Archivo", sans-serif; font-size: 0.66rem;
    letter-spacing: 0.18em; text-transform: uppercase; color: var(--smoke);
    margin-bottom: 3px;
  }}
  .fonte {{
    display: inline-block; margin-top: 12px;
    font-family: "Archivo", sans-serif; font-size: 0.68rem;
    letter-spacing: 0.16em; text-transform: uppercase; color: var(--smoke);
  }}
  .fonte::before {{ content: "— "; }}
  .vazio {{ color: var(--smoke); font-style: italic; padding: 8px 0; }}

  /* ---------- footer ---------- */
  footer {{
    padding: 44px 0 64px; text-align: center;
    font-family: "Archivo", sans-serif; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--smoke);
  }}
  footer .line {{ width: 40px; height: 2px; background: var(--ink); margin: 0 auto 20px; }}

  @media (max-width: 560px) {{
    .item {{ grid-template-columns: 32px 1fr; gap: 12px; }}
    .secao-icon {{ width: 32px; height: 32px; flex-basis: 32px; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior: auto; }}
    * {{ transition: none !important; }}
  }}
</style>
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">Briefing diário · curadoria pessoal</p>
      <h1>Michel<br>Goldemberg
        <span class="risk">“Take the risk.”</span>
      </h1>
      <div class="hero-meta">
        <span>{esc(DATA_BONITA)}</span>
        <span>Atualizado {atualizado} · Brasília</span>
      </div>
    </div>
  </header>

  <div class="wrap">
    <nav class="indice">{nav}</nav>
    <main>
      {secoes_html}
    </main>
    <footer>
      <div class="line"></div>
      Portal pessoal · atualização automática diária às 10h
    </footer>
  </div>
</body>
</html>"""

def main():
    try:
        dados = buscar_noticias()
    except Exception as e:
        print(f"Erro ao buscar/parsear notícias: {e}")
        dados = {c: [] for c, _, _ in SECOES}
    html_final = montar_html(dados)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_final)
    print(f"index.html gerado ({DATA_EXTENSO}).")

if __name__ == "__main__":
    main()
