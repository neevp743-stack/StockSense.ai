"""
StockSense AI — Shadow Prediction Tracker (Phase 18)
Provides querying, paired observation matching, and counting utilities for Phase 18 Champion/Challenger shadow prediction records.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord

logger = logging.getLogger(__name__)


class ShadowPredictionTracker:
    """
    Querying and pairing helper for Phase 18 shadow prediction records.
    """

    def query_records(
        self,
        symbol: Optional[str] = None,
        model_role: Optional[str] = None,
        resolved_only: bool = False,
        limit: int = 1000
    ) -> List[Phase18ShadowPredictionRecord]:
        """Queries shadow prediction records filtered by symbol, role, and resolution status."""
        with get_db_context() as db:
            q = db.query(Phase18ShadowPredictionRecord)
            if symbol:
                q = q.filter(Phase18ShadowPredictionRecord.symbol == symbol.upper().strip())
            if model_role:
                q = q.filter(Phase18ShadowPredictionRecord.model_role == model_role.upper().strip())
            if resolved_only:
                q = q.filter(Phase18ShadowPredictionRecord.resolved == True)

            q = q.order_by(Phase18ShadowPredictionRecord.prediction_timestamp.desc())
            if limit > 0:
                q = q.limit(limit)
            return q.all()

    def get_paired_records(
        self,
        symbol: Optional[str] = None,
        resolved_only: bool = True
    ) -> List[Tuple[Phase18ShadowPredictionRecord, Phase18ShadowPredictionRecord]]:
        """
        Pairs Champion and Challenger predictions matched on:
        (symbol, market_timestamp, feature_timestamp, prediction_horizon).
        Ensures both models are evaluated on equivalent future market outcomes.
        """
        with get_db_context() as db:
            q_champ = db.query(Phase18ShadowPredictionRecord).filter(
                Phase18ShadowPredictionRecord.model_role == "CHAMPION"
            )
            if symbol:
                q_champ = q_champ.filter(Phase18ShadowPredictionRecord.symbol == symbol.upper().strip())
            if resolved_only:
                q_champ = q_champ.filter(Phase18ShadowPredictionRecord.resolved == True)

            champ_recs = q_champ.all()
            paired = []

            for champ in champ_recs:
                q_chall = db.query(Phase18ShadowPredictionRecord).filter(
                    Phase18ShadowPredictionRecord.model_role == "CHALLENGER",
                    Phase18ShadowPredictionRecord.symbol == champ.symbol,
                    Phase18ShadowPredictionRecord.market_timestamp == champ.market_timestamp,
                    Phase18ShadowPredictionRecord.feature_timestamp == champ.feature_timestamp,
                    Phase18ShadowPredictionRecord.prediction_horizon == champ.prediction_horizon
                )
                if resolved_only:
                    q_chall = q_chall.filter(Phase18ShadowPredictionRecord.resolved == True)

                chall = q_chall.first()
                if chall is not None:
                    paired.append((champ, chall))

            return paired

    def get_counts(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Returns total predictions and resolved counts per model role."""
        with get_db_context() as db:
            q = db.query(Phase18ShadowPredictionRecord)
            if symbol:
                q = q.filter(Phase18ShadowPredictionRecord.symbol == symbol.upper().strip())

            all_recs = q.all()
            total = len(all_recs)
            champ_total = sum(1 for r in all_recs if r.model_role == "CHAMPION")
            chall_total = sum(1 for r in all_recs if r.model_role == "CHALLENGER")
            champ_resolved = sum(1 for r in all_recs if r.model_role == "CHAMPION" and r.resolved)
            chall_resolved = sum(1 for r in all_recs if r.model_role == "CHALLENGER" and r.resolved)

            return {
                "total_observations": total,
                "champion": {"total": champ_total, "resolved": champ_resolved},
                "challenger": {"total": chall_total, "resolved": chall_resolved},
                "paired_resolved": min(champ_resolved, chall_resolved)
            }


shadow_prediction_tracker = ShadowPredictionTracker()
