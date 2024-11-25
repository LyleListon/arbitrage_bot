# Active Context: Arbitrage Bot

**Current Focus:** Implementation of data collection and arbitrage detection logic.

**Recent Changes:** Created `dex_config.json` and updated `data_collection.py` and `ml_strategy.py` to use the configuration file.  Added placeholder implementations for data collection and arbitrage detection.

**Active Files:** `dashboard/trading_strategies.py`, `dashboard/data_collection.py`, `dashboard/ml_strategy.py`, `configs/dex_config.json`.

**Next Steps:**
1. Implement data collection logic in `data_collection.py` using the DEX APIs specified in `dex_config.json`.  This will involve fetching price and liquidity data for each token pair on each DEX.
2. Implement arbitrage detection logic in `ml_strategy.py`.  This will involve comparing prices across different DEXs to identify arbitrage opportunities.
3. Add error handling and data validation to both modules.
4. Write unit tests to verify the correctness of the implementation.

**Issues:** The data collection and arbitrage detection logic are currently placeholder implementations.  The next step is to implement the actual logic using the specified DEX APIs.
