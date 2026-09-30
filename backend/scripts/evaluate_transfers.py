"""
Out-of-sample check: do real summer 2026 transfer fees agree with the model?

The model's estimates come from a June 2026 snapshot, before the window
opened, so fees paid in the summer are outcomes it never saw. They are used
here only for evaluation, never as training data.

Questions:
1. Which predicts actual fees better, the Transfermarkt valuation or the
   model's estimate?
2. Does the model's gap (estimate vs valuation) predict which players sold
   above their valuation? This is what the bargain shortlist assumes.

Fees come from Wikipedia's "List of English football transfers summer 2026"
(permanent transfers with a reported amount; free and undisclosed fees are
excluded). Deals are cross-checked against the Premier League's official
summer 2026 transfer list. Pounds convert at a fixed GBP_TO_EUR rate; the
comparisons that matter are ratios and rank correlations, which a single
exchange rate barely affects.

Usage: python scripts/evaluate_transfers.py (run generate_rankings.py first)
Input:  data/raw/wikipedia_english_transfers_summer_2026.csv,
        data/raw/premier_league_summer_2026_moves.csv
Output: model/artifacts/transfer_validation.json, data/processed/transfer_validation.csv
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.name_matching import normalize_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
GBP_TO_EUR = 1.17
CURRENCY_TO_EUR = {"£": GBP_TO_EUR, "€": 1.0, "$": 0.92}
BOOTSTRAP_SAMPLES = 5000


def parse_fee_eur(text: str) -> float:
    """'£117m' -> 136.9e6; 'Undisclosed', 'Free' -> NaN."""
    text = re.sub(r"\[\d+\]", "", str(text))
    m = re.search(r"([£€$])\s*([\d.]+)\s*(m|million|k)?", text, re.I)
    if not m:
        return np.nan
    scale = 1e3 if (m.group(3) or "m").lower() == "k" else 1e6
    return float(m.group(2)) * scale * CURRENCY_TO_EUR[m.group(1)]


def load_fees(rankings: pd.DataFrame) -> pd.DataFrame:
    wiki = pd.read_csv(RAW / "wikipedia_english_transfers_summer_2026.csv")
    wiki["fee_eur"] = wiki["Fee"].map(parse_fee_eur)
    wiki["_name"] = wiki["Player"].map(normalize_name)
    pl_moves = pd.read_csv(RAW / "premier_league_summer_2026_moves.csv")
    confirmed = set(pl_moves["player"].map(normalize_name))

    ranked = rankings.assign(_name=rankings["Player"].map(normalize_name))
    # Names must be unique on both sides; an ambiguous name is skipped, not guessed.
    ranked = ranked[~ranked["_name"].duplicated(keep=False)]
    wiki = wiki[~wiki["_name"].duplicated(keep=False)]
    joined = ranked.merge(wiki[["_name", "Moving from", "Moving to", "Fee", "fee_eur"]], on="_name")
    joined["confirmed_by_premier_league"] = joined["_name"].isin(confirmed)
    return joined[joined["fee_eur"].notna() & joined["estimated_market_value_eur"].notna()]


def spearman_ci(x, y, seed=0):
    rng = np.random.default_rng(seed)
    n = len(x)
    samples = [spearmanr(x[idx], y[idx])[0] for idx in (rng.integers(0, n, n) for _ in range(BOOTSTRAP_SAMPLES))]
    return [float(v) for v in np.percentile(samples, [5, 95])]


def main():
    rankings = pd.read_csv(ROOT / "model" / "artifacts" / "rankings.csv")
    deals = load_fees(rankings)
    log_fee = np.log(deals["fee_eur"].to_numpy())
    log_value = np.log(deals["market_value_in_eur"].to_numpy())
    log_est = np.log(deals["estimated_market_value_eur"].to_numpy())

    # Buying clubs pay a premium over any valuation, so compare errors after
    # removing each predictor's own typical (median) premium.
    def premium_adjusted_mae(pred):
        diff = log_fee - pred
        return float(np.abs(diff - np.median(diff)).mean())

    gap, premium = log_est - log_value, log_fee - log_value
    rho, p_value = spearmanr(gap, premium)
    said_under = gap > 0
    shortlisted = deals[deals["eligible_for_ranking"]]
    fee, value, estimate = deals["fee_eur"], deals["market_value_in_eur"], deals["estimated_market_value_eur"]
    top_quarter = estimate >= estimate.quantile(0.75)
    results = {
        "n_deals": int(len(deals)),
        # How far real fees ran above market values: the headline for fans.
        "n_sold_above_value": int((fee > value).sum()),
        "n_sold_25pct_above_value": int((fee >= 1.25 * value).sum()),
        "n_sold_above_estimate": int((fee > estimate).sum()),
        "total_fees_eur": float(fee.sum()),
        "total_market_value_eur": float(value.sum()),
        # Does a high estimate pick out the players who command big fees?
        "top_quarter_by_estimate": {"n": int(top_quarter.sum()),
                                    "median_fee_eur": float(fee[top_quarter].median()),
                                    "rest_median_fee_eur": float(fee[~top_quarter].median())},
        "sold_above_value_by_model_call": {
            "model_said_undervalued": {"n": int(said_under.sum()),
                                       "sold_above": int((fee[said_under] > value[said_under]).sum())},
            "model_said_overvalued": {"n": int((~said_under).sum()),
                                      "sold_above": int((fee[~said_under] > value[~said_under]).sum())},
        },
        "n_confirmed_by_premier_league": int(deals["confirmed_by_premier_league"].sum()),
        "gbp_to_eur": GBP_TO_EUR,
        "median_fee_over_valuation": float(np.exp(np.median(premium))),
        "median_fee_over_estimate": float(np.exp(np.median(log_fee - log_est))),
        "premium_adjusted_log_mae": {"transfermarkt_valuation": premium_adjusted_mae(log_value),
                                     "model_estimate": premium_adjusted_mae(log_est)},
        "rank_correlation_with_fee": {"transfermarkt_valuation": float(spearmanr(log_value, log_fee)[0]),
                                      "model_estimate": float(spearmanr(log_est, log_fee)[0])},
        "gap_predicts_premium": {"spearman": float(rho), "p_value": float(p_value),
                                 "bootstrap_90_ci": spearman_ci(gap, premium)},
        "median_fee_over_valuation_by_model_call": {
            "model_said_undervalued": {"n": int(said_under.sum()),
                                       "ratio": float(np.exp(np.median(premium[said_under])))},
            "model_said_overvalued": {"n": int((~said_under).sum()),
                                      "ratio": float(np.exp(np.median(premium[~said_under])))},
        },
        "shortlisted_players_sold": [
            {"player": r.Player, "club": r.Squad, "moved_to": r["Moving to"],
             "market_value_eur": float(r.market_value_in_eur),
             "estimated_value_eur": float(r.estimated_market_value_eur), "fee_eur": float(r.fee_eur)}
            for _, r in shortlisted.iterrows()
        ],
    }
    (ROOT / "model" / "artifacts" / "transfer_validation.json").write_text(json.dumps(results, indent=2))
    cols = ["player_id", "Player", "Squad", "Moving to", "Fee", "fee_eur", "market_value_in_eur",
            "estimated_market_value_eur", "eligible_for_ranking", "confirmed_by_premier_league"]
    deals[cols].sort_values("fee_eur", ascending=False).to_csv(
        ROOT / "data" / "processed" / "transfer_validation.csv", index=False)
    print(json.dumps({k: v for k, v in results.items() if k != "shortlisted_players_sold"}, indent=2))


if __name__ == "__main__":
    main()
