"""Web scraper for InfinitePay pages.

Fetches and cleans HTML content from InfinitePay URLs
for ingestion into the RAG knowledge base.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# All InfinitePay URLs to scrape for RAG
INFINITEPAY_URLS = [
    "https://www.infinitepay.io",
    "https://www.infinitepay.io/maquininha",
    "https://www.infinitepay.io/maquininha-celular",
    "https://www.infinitepay.io/tap-to-pay",
    "https://www.infinitepay.io/pdv",
    "https://www.infinitepay.io/receba-na-hora",
    "https://www.infinitepay.io/gestao-de-cobranca-2",
    "https://www.infinitepay.io/gestao-de-cobranca",
    "https://www.infinitepay.io/link-de-pagamento",
    "https://www.infinitepay.io/loja-online",
    "https://www.infinitepay.io/boleto",
    "https://www.infinitepay.io/conta-digital",
    "https://www.infinitepay.io/conta-pj",
    "https://www.infinitepay.io/pix",
    "https://www.infinitepay.io/pix-parcelado",
    "https://www.infinitepay.io/emprestimo",
    "https://www.infinitepay.io/cartao",
    "https://www.infinitepay.io/rendimento",
    # JIM Knowledge Base
    "https://ajuda.infinitepay.io/pt-BR/articles/14088698-como-fazer-pagamentos-pelo-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/14088921-como-acompanhar-minhas-financas-pelo-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/14089162-como-criar-imagens-profissionais-com-o-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/13919788-como-criar-e-personalizar-seu-site-com-o-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/10538821-como-o-jim-funciona-conheca-seu-assistente-que-faz-tudo",
    "https://ajuda.infinitepay.io/pt-BR/articles/14089069-como-criar-campanhas-e-conteudo-de-marketing-com-o-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/14089032-como-calcular-preco-e-margem-de-lucro-com-o-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/14089187-como-criar-lembretes-e-organizar-minha-agenda-com-o-jim",
    "https://ajuda.infinitepay.io/pt-BR/articles/14089239-como-o-jim-aprende-sobre-meu-negocio-e-personaliza-as-respostas",
    "https://ajuda.infinitepay.io/pt-BR/articles/11481595-como-funciona-o-radar-de-boletos-no-jim",
]


@dataclass
class ScrapedPage:
    """A scraped and cleaned web page."""

    url: str
    title: str
    content: str
    section: str  # Product category


def _clean_html(html: str) -> str:
    """Extract clean text from HTML, removing scripts, styles, and navigation."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, nav, footer
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Get text with newlines between blocks
    text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive newlines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def _extract_title(html: str) -> str:
    """Extract page title from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)

    h1_tag = soup.find("h1")
    if h1_tag:
        return h1_tag.get_text(strip=True)

    return "InfinitePay"


def _url_to_section(url: str) -> str:
    """Map a URL to a product section name."""
    path = url.replace("https://www.infinitepay.io", "").strip("/")
    section_map = {
        "": "home",
        "maquininha": "maquininha_smart",
        "maquininha-celular": "infinitetap",
        "tap-to-pay": "tap_to_pay",
        "pdv": "pdv",
        "receba-na-hora": "recebimento",
        "gestao-de-cobranca-2": "gestao_cobranca",
        "gestao-de-cobranca": "gestao_cobranca",
        "link-de-pagamento": "link_pagamento",
        "loja-online": "loja_online",
        "boleto": "boleto",
        "conta-digital": "conta_digital",
        "conta-pj": "conta_pj",
        "pix": "pix",
        "pix-parcelado": "pix_parcelado",
        "emprestimo": "emprestimo",
        "cartao": "cartao",
        "rendimento": "rendimento",
    }
    if "ajuda.infinitepay.io/pt-BR/articles/" in url and "jim" in url.lower():
        return "jim"
    return section_map.get(path, path or "unknown")


async def scrape_pages(urls: list[str] | None = None) -> list[ScrapedPage]:
    """Scrape and clean content from InfinitePay URLs.

    Args:
        urls: List of URLs to scrape. Defaults to INFINITEPAY_URLS.

    Returns:
        List of cleaned ScrapedPage objects.
    """
    urls = urls or INFINITEPAY_URLS
    pages: list[ScrapedPage] = []

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "InfinityAgent/1.0 RAG Scraper"},
    ) as client:
        for url in urls:
            try:
                logger.info("Scraping: %s", url)
                response = await client.get(url)
                response.raise_for_status()

                html = response.text
                content = _clean_html(html)
                title = _extract_title(html)
                section = _url_to_section(url)

                if content and len(content) > 50:  # Skip near-empty pages
                    pages.append(
                        ScrapedPage(
                            url=url,
                            title=title,
                            content=content,
                            section=section,
                        )
                    )
                    logger.info("  ✅ Scraped %s (%d chars)", title, len(content))
                else:
                    logger.warning("  ⚠️  Skipped %s (too short: %d chars)", url, len(content))

            except Exception as e:
                logger.error("  ❌ Failed to scrape %s: %s", url, str(e))

    logger.info("Scraped %d/%d pages successfully", len(pages), len(urls))
    return pages
