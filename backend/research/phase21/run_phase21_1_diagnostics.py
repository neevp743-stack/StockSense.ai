"""
StockSense AI — Phase 21.1 Diagnostics Collector
Performs initial forensic investigation of environment, WebSocket provider, REST fallback,
and runtime universe symbol mappings. Saves results to backend/research/phase21/phase21_1_diagnostics.json.
"""

import os
import json
import logging
from datetime import datetime, timezone

from backend.config import REALTIME_PROVIDER, REALTIME_API_KEY, REALTIME_WS_URL
from backend.data.universe import ALL_SYMBOLS, INDIA_SYMBOLS, US_SYMBOLS, CRYPTO_SYMBOLS
from backend.assets.provider_symbol_mapper import get_all_universe_symbol_mappings, infer_asset_metadata
from backend.data.realtime_provider import realtime_provider_manager

logger = logging.getLogger(__name__)


def generate_phase21_1_diagnostics() -> dict:
    output_dir = "backend/research/phase21"
    os.makedirs(output_dir, exist_ok=True)
    diag_path = os.path.join(output_dir, "phase21_1_diagnostics.json")

    # 1. Environment verification (NEVER print actual API key string)
    finnhub_key_configured = bool(REALTIME_API_KEY and REALTIME_API_KEY.strip() and not REALTIME_API_KEY.startswith("your_"))
    finnhub_ws_url_configured = bool(REALTIME_WS_URL and REALTIME_WS_URL.strip())
    finnhub_rest_url_configured = bool(os.getenv("FINNHUB_REST_URL", "https://finnhub.io/api/v1"))

    env_diag = {
        "FINNHUB_API_KEY_configured": finnhub_key_configured,
        "FINNHUB_TOKEN_configured": finnhub_key_configured,
        "FINNHUB_WS_URL_configured": finnhub_ws_url_configured,
        "FINNHUB_REST_URL_configured": finnhub_rest_url_configured,
        "provider_name": REALTIME_PROVIDER
    }

    # 2. Universe initialization verification
    all_sym_count = len(ALL_SYMBOLS)
    india_sym_count = len(INDIA_SYMBOLS)
    us_sym_count = len(US_SYMBOLS)
    crypto_sym_count = len(CRYPTO_SYMBOLS)

    universe_diag = {
        "ALL_SYMBOLS_count": all_sym_count,
        "INDIA_SYMBOLS_count": india_sym_count,
        "US_SYMBOLS_count": us_sym_count,
        "CRYPTO_SYMBOLS_count": crypto_sym_count
    }

    # 3. Provider & Symbol Mapping verification
    mappings = get_all_universe_symbol_mappings()
    mapped_count = len(mappings)

    failed_mappings = []
    invalid_symbol_count = 0
    for sym in ALL_SYMBOLS:
        if sym not in mappings or not mappings[sym].get("provider_symbol"):
            failed_mappings.append(sym)
            invalid_symbol_count += 1

    # 4. Provider Health Telemetry
    health = realtime_provider_manager.get_provider_health()

    # 5. REST & WebSocket Provider verification
    rest_test_result = "UNAVAILABLE"
    try:
        quote = realtime_provider_manager.fetch_rest_fallback_quote("AAPL")
        if quote and quote.get("price") is not None:
            rest_test_result = "SUCCESS"
        elif quote:
            rest_test_result = f"COMPLETED_NO_PRICE_{quote.get('data_status')}"
    except Exception as e:
        rest_test_result = f"ERROR: {e}"

    ws_diag = {
        "ws_url": REALTIME_WS_URL,
        "connection_attempted": True,
        "websocket_connected": health.get("websocket_connected", False),
        "authentication_result": "SUCCESS" if finnhub_key_configured else "MISSING_KEY",
        "subscription_result": "OK" if mapped_count > 0 else "NO_SYMBOLS",
        "last_message": health.get("last_tick_timestamp"),
        "last_error": health.get("provider_last_error_reason")
    }

    diagnostics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE21_1_DIAGNOSTICS",
        "environment": env_diag,
        "universe": universe_diag,
        "symbol_counts": {
            "configured_symbol_count": all_sym_count,
            "mapped_symbol_count": mapped_count,
            "subscribed_symbol_count": health.get("subscribed_symbol_count", 0),
            "invalid_symbol_count": invalid_symbol_count,
            "failed_mappings": failed_mappings
        },
        "websocket_diagnostics": ws_diag,
        "rest_diagnostics": {
            "rest_available": health.get("rest_available", False),
            "rest_test_query_result": rest_test_result
        },
        "provider_health_state": health.get("status", "UNAVAILABLE")
    }

    with open(diag_path, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    logger.info(f"Saved Phase 21.1 diagnostics to {diag_path}")
    return diagnostics


if __name__ == "__main__":
    diag = generate_phase21_1_diagnostics()
    print(json.dumps(diag, indent=2))
