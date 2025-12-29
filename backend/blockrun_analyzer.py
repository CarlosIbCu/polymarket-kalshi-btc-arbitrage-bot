"""
BlockRun AI Analyzer for Polymarket-Kalshi Arbitrage Bot

Provides AI-powered analysis of arbitrage opportunities using BlockRun's
x402 micropayment-enabled LLM gateway. No API keys required - pay with USDC.

Learn more: https://blockrun.ai

Installation:
    pip install blockrun-llm
"""

import os
from typing import Optional

from blockrun_llm import LLMClient
from blockrun_llm.types import APIError, PaymentError


# BlockRun model mappings
BLOCKRUN_MODELS = {
    "gpt-5": "openai/gpt-5",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "claude-3-5-sonnet": "anthropic/claude-3-5-sonnet",
    "gemini-2.0-flash": "google/gemini-2.0-flash",
}

DEFAULT_MODEL = "gpt-4o-mini"

# Cached client instance
_client: Optional[LLMClient] = None


def _get_client() -> LLMClient:
    """Get or create BlockRun client instance."""
    global _client
    if _client is None:
        _client = LLMClient(
            private_key=os.getenv("BLOCKRUN_WALLET_KEY"),
            api_url=os.getenv("BLOCKRUN_API_URL", "https://blockrun.ai/api"),
        )
    return _client


def is_blockrun_enabled() -> bool:
    """Check if BlockRun AI analysis is enabled."""
    return os.getenv("BLOCKRUN_ENABLED", "false").lower() == "true"


def analyze_arbitrage_opportunity(
    poly_data: dict,
    kalshi_data: dict,
    opportunities: list,
    model: str = DEFAULT_MODEL
) -> Optional[dict]:
    """
    Use AI to analyze arbitrage opportunities and provide insights.

    Args:
        poly_data: Polymarket market data
        kalshi_data: Kalshi market data
        opportunities: List of detected arbitrage opportunities
        model: LLM model to use (default: gpt-4o-mini for cost efficiency)

    Returns:
        AI analysis with risk assessment and recommendations
    """
    if not is_blockrun_enabled():
        return None

    blockrun_model = BLOCKRUN_MODELS.get(model, f"openai/{model}")

    # Build analysis prompt
    prompt = _build_analysis_prompt(poly_data, kalshi_data, opportunities)

    system_prompt = (
        "You are an expert quantitative analyst specializing in "
        "prediction market arbitrage. Analyze the given market data "
        "and arbitrage opportunities. Provide concise, actionable insights. "
        "Focus on: execution risk, liquidity concerns, timing, and "
        "whether the opportunity is worth pursuing. Be direct and practical."
    )

    try:
        client = _get_client()
        analysis_text = client.chat(
            model=blockrun_model,
            prompt=prompt,
            system=system_prompt,
            max_tokens=500,
            temperature=0.3,
        )

        return {
            "status": "success",
            "model": blockrun_model,
            "analysis": analysis_text,
        }

    except PaymentError as e:
        return {
            "status": "payment_error",
            "message": f"Payment failed: {str(e)}. Ensure wallet has sufficient USDC balance.",
        }
    except APIError as e:
        return {
            "status": "error",
            "message": f"BlockRun API error: {str(e)}",
        }
    except ValueError as e:
        # Missing private key or invalid config
        return {
            "status": "config_error",
            "message": f"Configuration error: {str(e)}. Set BLOCKRUN_WALLET_KEY env var.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
        }


def _build_analysis_prompt(poly_data: dict, kalshi_data: dict, opportunities: list) -> str:
    """Build the analysis prompt from market data."""

    poly_info = "N/A"
    if poly_data:
        poly_strike = poly_data.get('price_to_beat', 'N/A')
        poly_up = poly_data.get('prices', {}).get('Up', 'N/A')
        poly_down = poly_data.get('prices', {}).get('Down', 'N/A')
        poly_expiry = poly_data.get('expiry', 'N/A')
        poly_info = f"Strike: ${poly_strike:,.2f}, Up: ${poly_up:.3f}, Down: ${poly_down:.3f}, Expiry: {poly_expiry}"

    kalshi_info = "N/A"
    if kalshi_data and kalshi_data.get('markets'):
        markets = kalshi_data['markets'][:5]  # Top 5 closest
        kalshi_info = "\n".join([
            f"  Strike ${m['strike']:,.2f}: Yes ${m['yes_ask']/100:.2f}, No ${m['no_ask']/100:.2f}"
            for m in markets
        ])

    opp_info = "None detected"
    if opportunities:
        opp_info = "\n".join([
            f"  {o['type']}: {o['poly_leg']} (${o['poly_cost']:.3f}) + {o['kalshi_leg']} (${o['kalshi_cost']:.3f}) = ${o['total_cost']:.3f} (margin: ${o['margin']:.3f})"
            for o in opportunities
        ])

    return f"""Analyze this BTC hourly prediction market arbitrage situation:

## Polymarket Data
{poly_info}

## Kalshi Markets (closest to Polymarket strike)
{kalshi_info}

## Detected Opportunities
{opp_info}

Provide:
1. Risk assessment (execution risk, slippage, timing)
2. Liquidity analysis (can this trade actually be executed?)
3. Recommendation (execute, wait, or pass)
4. Any concerns or caveats

Be concise and actionable."""


def get_market_sentiment(model: str = DEFAULT_MODEL) -> Optional[dict]:
    """
    Get AI-powered BTC market sentiment analysis.

    Returns brief sentiment analysis to inform trading decisions.
    """
    if not is_blockrun_enabled():
        return None

    blockrun_model = BLOCKRUN_MODELS.get(model, f"openai/{model}")

    try:
        client = _get_client()
        sentiment = client.chat(
            model=blockrun_model,
            prompt="What's the current BTC market sentiment for the next hour? One sentence only.",
            system="You are a crypto market analyst. Provide very brief BTC sentiment.",
            max_tokens=100,
            temperature=0.5,
        )

        return {
            "status": "success",
            "sentiment": sentiment,
        }

    except PaymentError:
        return {"status": "payment_error", "message": "Insufficient USDC balance"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_available_models() -> dict:
    """List available BlockRun models."""
    return {
        name: {
            "blockrun_id": blockrun_id,
            "description": _get_model_description(name)
        }
        for name, blockrun_id in BLOCKRUN_MODELS.items()
    }


def _get_model_description(model: str) -> str:
    """Get model description."""
    descriptions = {
        "gpt-5": "OpenAI GPT-5 - Most capable",
        "gpt-4o": "OpenAI GPT-4o - Fast and capable",
        "gpt-4o-mini": "OpenAI GPT-4o-mini - Cost efficient (recommended)",
        "claude-3-5-sonnet": "Anthropic Claude 3.5 Sonnet - Strong reasoning",
        "gemini-2.0-flash": "Google Gemini 2.0 Flash - Very fast",
    }
    return descriptions.get(model, "")
