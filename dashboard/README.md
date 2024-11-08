# Arbitrage Bot Dashboard

## Overview
This dashboard provides real-time monitoring and visualization for the Arbitrage Bot. It displays system metrics, token prices, and price trends.

## ⚠️ IMPORTANT: Use Real Data Only ⚠️
**DO NOT USE MOCK DATA IN PRODUCTION OR TESTING ENVIRONMENTS.**
Always use real price feeds and data sources to ensure accurate and reliable operation of the Arbitrage Bot.

## Setup and Installation

1. Ensure you have Python 3.7+ installed.
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables in a `.env` file (see `.env.example` for reference).
4. Configure real price feeds (see "Setting Up Real Price Feeds" section below).

## Running the Dashboard

1. Navigate to the project root directory.
2. Run the following command:
   ```
   python run_dashboard.py
   ```
3. Open a web browser and go to `http://127.0.0.1:5000`

## Setting Up Real Price Feeds

To ensure accurate and reliable operation, always use real price feeds. Follow these steps to set up Chainlink price feeds:

1. Sign up for an Infura account and create a new project to get an API key.
2. In your `.env` file, add your Infura project ID:
   ```
   INFURA_PROJECT_ID=your_project_id_here
   ```
3. In `dashboard/app.py`, update the Web3 provider with your Infura project ID:
   ```python
   w3 = Web3(Web3.HTTPProvider(f'https://sepolia.infura.io/v3/{os.getenv("INFURA_PROJECT_ID")}'))
   ```
4. Ensure the `PRICE_FEED_ADDRESSES` dictionary in `dashboard/app.py` contains the correct Chainlink price feed contract addresses for the Sepolia testnet.

## Key Components

- `app.py`: Main Flask application
- `templates/index.html`: Frontend HTML template
- `static/css/style.css`: Custom CSS styles

## Important Notes and Troubleshooting

1. **PyYAML Installation**: If you encounter issues installing PyYAML, it might be due to missing C++ build tools. Ensure you have the appropriate build tools installed for your system.

2. **Web3 Connection**: The dashboard connects to the Ethereum network using the Infura RPC URL. Ensure your `.env` file contains the correct `INFURA_PROJECT_ID`.

3. **Token Prices**: The dashboard uses real-time price feeds from Chainlink. Ensure the price feed addresses are correct and up-to-date.

4. **Real-time Updates**: The dashboard uses Socket.IO for real-time updates. If you're not seeing live updates, check your browser's console for any connection errors.

5. **Chart.js**: The price trend chart is implemented using Chart.js. If the chart is not rendering correctly, ensure that the Chart.js library is properly loaded.

6. **Error Handling**: The application includes error handling for various scenarios, but you may need to add more specific error handling based on your production environment.

7. **Performance Considerations**: For large-scale deployments, consider optimizing the update frequency and data storage methods to reduce server load and improve performance.

## Current State and Future Improvements

1. ✅ Implement real price feed integration using Chainlink
2. Add more detailed trade information display
3. Create a notification system for important events
4. Develop a settings page for user preferences
5. Enhance security features for production deployment
6. Implement comprehensive unit and integration tests
7. Optimize performance for handling larger datasets

## Contribution Guidelines

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

For any questions or issues, please open an issue in the GitHub repository.
