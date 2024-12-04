# Arbitrage Bot MVP Dashboard

## Overview
This is a Minimum Viable Product (MVP) dashboard for the Arbitrage Bot, designed to provide key insights into trading performance using Streamlit.

## Features
- Performance metrics display
- Recent trade history
- Cumulative profit chart
- Basic error handling and logging

## Prerequisites
- Python 3.9+
- Install dependencies: 
  ```bash
  pip install -r requirements.txt
  ```

## Running the Dashboard
```bash
streamlit run mvp_arbitrage_dashboard.py
```

## Configuration
- Ensure `config.json` is properly configured in the parent directory
- Default configuration will be used if the file is not found

## Logging
- Dashboard logs are saved to `dashboard.log`
- Logs include initialization, configuration, and runtime events

## Next Steps
- Replace placeholder data with actual trading data
- Enhance error handling
- Add more detailed visualizations
- Integrate with live trading backend

## Troubleshooting
- Check `dashboard.log` for any initialization or runtime errors
- Verify all dependencies are installed correctly
- Ensure Python version compatibility
