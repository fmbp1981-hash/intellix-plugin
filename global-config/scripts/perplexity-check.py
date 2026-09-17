# -*- coding: utf-8 -*-
"""
Hook UserPromptSubmit — detecta quando Perplexity deve ser usado
e injeta instrucao no contexto do Claude.
"""
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "").lower()
    except Exception:
        sys.exit(0)

    # Gatilhos que indicam necessidade de dados atualizados/externos
    triggers = {
        "versao": "perplexity_search",
        "version": "perplexity_search",
        "latest": "perplexity_search",
        "atual": "perplexity_search",
        "atualiz": "perplexity_search",
        "preco": "perplexity_search",
        "price": "perplexity_search",
        "plano": "perplexity_search",
        "custo": "perplexity_search",
        "noticia": "perplexity_search",
        "news": "perplexity_search",
        "recente": "perplexity_search",
        "recent": "perplexity_search",
        "2024": "perplexity_search",
        "2025": "perplexity_search",
        "2026": "perplexity_search",
        "documentacao": "perplexity_ask",
        "documentation": "perplexity_ask",
        "docs": "perplexity_ask",
        "changelog": "perplexity_ask",
        "release": "perplexity_ask",
        "erro": "perplexity_search",
        "error": "perplexity_search",
        "bug": "perplexity_search",
        "issue": "perplexity_search",
        "mercado": "perplexity_research",
        "market": "perplexity_research",
        "concorrent": "perplexity_research",
        "competitor": "perplexity_research",
        "tendencia": "perplexity_research",
        "trend": "perplexity_research",
        "pesquis": "perplexity_research",
        "research": "perplexity_research",
        "status": "perplexity_search",
        "disponivel": "perplexity_search",
        "available": "perplexity_search",
        "suporta": "perplexity_search",
        "support": "perplexity_search",
        "compatib": "perplexity_search",
        "instalar": "perplexity_search",
        "install": "perplexity_search",
        "npm install": "perplexity_search",
        "pip install": "perplexity_search",
    }

    matched_tool = None
    matched_trigger = None
    for trigger, tool in triggers.items():
        if trigger in prompt:
            matched_tool = tool
            matched_trigger = trigger
            # Preferir research sobre search se ambos batem
            if tool == "perplexity_research":
                break

    if matched_tool:
        msg = (
            f"\n[PERPLEXITY] Esta tarefa contem '{matched_trigger}' — "
            f"use `{matched_tool}` para obter informacoes atualizadas ANTES de responder. "
            f"Nunca assuma versoes, precos ou dados externos sem verificar via Perplexity.\n"
        )
        print(msg)

if __name__ == "__main__":
    main()
