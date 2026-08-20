# Position Sizing Methods
tags: position size, lots, units, pip value, leverage

Position sizing converts a risk decision into a quantity. The universal formula is: size = risk amount / stop distance, where risk amount is account balance times risk percent, and stop distance is the absolute difference between entry and stop loss expressed in the same units as the instrument price.

For instruments quoted directly in the account currency — spot crypto, shares, most CFDs — the linear method applies. With a $1,000 account, 1% risk and a $500 stop distance on Bitcoin, the size is 10 / 500 = 0.02 BTC. Notional exposure is size times entry price, which is what leverage limits apply to.

For forex, size is expressed in lots and the stop distance is expressed in pips. One pip is 0.0001 for most pairs and 0.01 for JPY-quoted pairs. Lots = risk amount / (stop in pips * pip value per lot). A standard lot is 100,000 units; a mini lot is 10,000 and a micro lot 1,000. Pip value per standard lot is roughly 10 units of the quote currency, exactly 10 when the quote currency is the account currency; cross pairs require converting the pip value into the account currency at the current rate, which must be supplied rather than assumed.

Leverage does not change risk, it changes margin. A position sized correctly at 1% risk carries the same loss potential whether it is opened at 1x or 30x; what leverage changes is whether the broker will permit the notional and how close the margin call sits. Check that notional does not exceed balance times available leverage, and treat any size that requires maximum leverage as a sizing error.

Fractional sizing rules such as fixed-fractional and Kelly scale size with equity. Fixed-fractional (constant percent of current equity) reduces size automatically during drawdowns, which is why it is the default for retail accounts.
