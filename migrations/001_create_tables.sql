-- DeepStack TradingView — Data Bridge Tables
-- Applied via: supabase db push or manual execution in Supabase SQL Editor

-- ============================================================
-- Indicators: one row per TradingView script (aggregated stats)
-- ============================================================
CREATE TABLE IF NOT EXISTS ds_tv_indicators (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  script_name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  source_url TEXT,
  pine_hash TEXT,
  conversion_status TEXT DEFAULT 'pending',
  composite_score NUMERIC,
  avg_sharpe NUMERIC,
  avg_roi NUMERIC,
  avg_win_rate NUMERIC,
  avg_profit_factor NUMERIC,
  num_tickers_tested INT DEFAULT 0,
  best_ticker TEXT,
  worst_ticker TEXT,
  rank INT,
  tags TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Backtests: one row per (script, ticker) pair
-- ============================================================
CREATE TABLE IF NOT EXISTS ds_tv_backtests (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  indicator_id UUID REFERENCES ds_tv_indicators(id) ON DELETE CASCADE,
  script_name TEXT NOT NULL,
  ticker TEXT NOT NULL,
  roi_pct NUMERIC,
  max_drawdown_pct NUMERIC,
  sharpe_ratio NUMERIC,
  sortino_ratio NUMERIC,
  win_rate_pct NUMERIC,
  profit_factor NUMERIC,
  num_trades INT,
  expectancy_pct NUMERIC,
  error TEXT,
  backtest_file TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(script_name, ticker)
);

-- ============================================================
-- Indexes for fast lookups
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ds_tv_indicators_rank ON ds_tv_indicators(rank);
CREATE INDEX IF NOT EXISTS idx_ds_tv_indicators_composite ON ds_tv_indicators(composite_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_ds_tv_backtests_indicator ON ds_tv_backtests(indicator_id);
CREATE INDEX IF NOT EXISTS idx_ds_tv_backtests_script ON ds_tv_backtests(script_name);

-- ============================================================
-- Trigger: auto-update composite score when backtests change
--
-- Composite score formula (weighted blend):
--   Sharpe (30%) + ROI/100 (25%) + WinRate/100 (25%) + ProfitFactor/10 (20%)
--
-- Also updates: avg_sharpe, avg_roi, avg_win_rate, avg_profit_factor,
--   num_tickers_tested, best_ticker, worst_ticker
-- ============================================================
CREATE OR REPLACE FUNCTION update_ds_tv_composite_score()
RETURNS TRIGGER AS $$
DECLARE
  _avg_sharpe NUMERIC;
  _avg_roi NUMERIC;
  _avg_win_rate NUMERIC;
  _avg_profit_factor NUMERIC;
  _num_tested INT;
  _best TEXT;
  _worst TEXT;
BEGIN
  SELECT
    AVG(sharpe_ratio), AVG(roi_pct), AVG(win_rate_pct), AVG(profit_factor), COUNT(*)
  INTO _avg_sharpe, _avg_roi, _avg_win_rate, _avg_profit_factor, _num_tested
  FROM ds_tv_backtests
  WHERE indicator_id = NEW.indicator_id AND error IS NULL;

  SELECT ticker INTO _best FROM ds_tv_backtests
  WHERE indicator_id = NEW.indicator_id AND error IS NULL
  ORDER BY roi_pct DESC NULLS LAST LIMIT 1;

  SELECT ticker INTO _worst FROM ds_tv_backtests
  WHERE indicator_id = NEW.indicator_id AND error IS NULL
  ORDER BY roi_pct ASC NULLS LAST LIMIT 1;

  UPDATE ds_tv_indicators SET
    composite_score = COALESCE(_avg_sharpe * 0.3, 0)
                    + COALESCE(_avg_roi / 100 * 0.25, 0)
                    + COALESCE(_avg_win_rate / 100 * 0.25, 0)
                    + COALESCE(_avg_profit_factor / 10 * 0.2, 0),
    avg_sharpe = _avg_sharpe,
    avg_roi = _avg_roi,
    avg_win_rate = _avg_win_rate,
    avg_profit_factor = _avg_profit_factor,
    num_tickers_tested = _num_tested,
    best_ticker = _best,
    worst_ticker = _worst,
    updated_at = NOW()
  WHERE id = NEW.indicator_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_composite_score
  AFTER INSERT OR UPDATE ON ds_tv_backtests
  FOR EACH ROW
  EXECUTE FUNCTION update_ds_tv_composite_score();
