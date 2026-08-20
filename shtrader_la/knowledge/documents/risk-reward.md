# Risk/Reward and Expectancy
tags: risk reward, expectancy, win rate, breakeven

Risk/reward compares the distance from entry to target with the distance from entry to stop. For a long, risk is entry minus stop and reward is target minus entry; for a short the two are reversed. A setup where the stop sits on the winning side of entry is not a low-quality trade, it is an invalid one, and should be rejected outright.

The ratio determines the win rate required to break even: breakeven win rate = 1 / (1 + R:R). At 1:1 you need 50%, at 2:1 you need 33.3%, at 3:1 you need 25%. This is why a 2:1 minimum is a common filter — it leaves room to be wrong more often than right and still finish flat before costs.

Expectancy per trade = (win rate * average win) − (loss rate * average loss). A strategy with a 40% win rate at 3:1 has an expectancy of +0.6R per trade; a strategy with a 70% win rate at 0.5:1 has +0.05R and is destroyed by spread, commission and slippage. Always subtract costs from reward before judging the ratio: on tight intraday stops, spread can consume a fifth of the expected R.

Targets must be justified by structure — a prior swing, a measured move, a liquidity pocket — not chosen to manufacture a flattering ratio. Widening a target until the R:R passes a filter is a way of failing the filter dishonestly. If the honest ratio is below the minimum, the correct action is to tighten the stop only if structure allows, or to skip the trade.

Partial exits change the realised ratio. Taking half at 1R and moving the stop to breakeven converts a 3:1 trade into roughly 2:1 with a materially higher win rate; the choice is a preference about variance, not an improvement in expectancy.
