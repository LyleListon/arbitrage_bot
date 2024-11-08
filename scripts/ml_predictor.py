import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib
import logging
import json
import os

logging.basicConfig(level=logging.DEBUG)

class MLPredictor:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.lstm_model = self._build_lstm_model()
        self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
        
        self.price_scaler = StandardScaler()
        self.feature_scaler = StandardScaler()
        
        self._load_models()

    def _build_lstm_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(100, 1)),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def _load_models(self):
        try:
            logging.debug("Attempting to load model files...")
            self.lstm_model.load_weights('models/lstm.weights.h5')
            logging.debug("LSTM weights loaded successfully")
            self.rf_classifier = joblib.load('models/rf_classifier.joblib')
            logging.debug("RF classifier loaded successfully")
            self.xgb_model = joblib.load('models/xgb_model.joblib')
            logging.debug("XGB model loaded successfully")
            self.price_scaler = joblib.load('models/price_scaler.joblib')
            logging.debug("Price scaler loaded successfully")
            self.feature_scaler = joblib.load('models/feature_scaler.joblib')
            logging.debug("Feature scaler loaded successfully")
        except FileNotFoundError as e:
            logging.warning(f"Model file not found: {str(e)}")
            logging.info("Training new models with mock data.")
            self._mock_train()
        except Exception as e:
            logging.error(f"Error loading model files: {str(e)}")
            raise

    def _mock_train(self):
        logging.info("Starting mock training...")
        try:
            # Generate mock data
            n_samples = 1000
            n_features = 9
            
            # Price data for LSTM
            price_data = np.cumsum(np.random.randn(n_samples)) + 100
            price_data = price_data.reshape(-1, 1)
            
            # Other features for RF and XGB
            X = np.random.rand(n_samples, n_features)
            y_classifier = np.random.randint(0, 2, n_samples)
            y_regressor = np.random.rand(n_samples) * 10  # Spread predictions
            
            # Train LSTM
            self.price_scaler.fit(price_data)
            scaled_price_data = self.price_scaler.transform(price_data)
            lstm_input = np.array([scaled_price_data[i:i+100] for i in range(n_samples-100)])
            lstm_target = scaled_price_data[100:]
            self.lstm_model.fit(lstm_input, lstm_target, epochs=5, batch_size=32, verbose=0)
            logging.debug("LSTM model trained successfully")
            
            # Train RF and XGB
            self.feature_scaler.fit(X)
            X_scaled = self.feature_scaler.transform(X)
            self.rf_classifier.fit(X_scaled, y_classifier)
            logging.debug("RF classifier trained successfully")
            self.xgb_model.fit(X_scaled, y_regressor)
            logging.debug("XGB model trained successfully")
            
            # Save models
            self._save_models()
        except Exception as e:
            logging.error(f"Error during mock training: {str(e)}")
            raise

    def _save_models(self):
        try:
            if not os.path.exists('models'):
                os.makedirs('models')
            self.lstm_model.save_weights('models/lstm.weights.h5')
            logging.debug("LSTM weights saved successfully")
            joblib.dump(self.rf_classifier, 'models/rf_classifier.joblib')
            logging.debug("RF classifier saved successfully")
            joblib.dump(self.xgb_model, 'models/xgb_model.joblib')
            logging.debug("XGB model saved successfully")
            joblib.dump(self.price_scaler, 'models/price_scaler.joblib')
            logging.debug("Price scaler saved successfully")
            joblib.dump(self.feature_scaler, 'models/feature_scaler.joblib')
            logging.debug("Feature scaler saved successfully")
        except Exception as e:
            logging.error(f"Error saving model files: {str(e)}")
            raise

    def predict_opportunity(self, price_data, volatility_data, correlation_data, market_data):
        # Prepare features
        features = self._prepare_features(price_data, volatility_data, correlation_data, market_data)
        
        # Make predictions
        price_pred = self.lstm_model.predict(features['lstm_input'])[0][0]
        opportunity_prob = self.rf_classifier.predict_proba(features['other_features'])[0][1]
        spread_pred = self.xgb_model.predict(features['other_features'])[0]
        
        # Calculate confidence
        confidence = np.mean([
            opportunity_prob,
            1 if spread_pred > 0 else 0,
            1 if price_pred > price_data['price'].iloc[-1] else 0
        ])
        
        return {
            'price_prediction': float(price_pred),
            'opportunity_probability': float(opportunity_prob),
            'spread_prediction': float(spread_pred),
            'confidence': float(confidence)
        }

    def _prepare_features(self, price_data, volatility_data, correlation_data, market_data):
        # Prepare LSTM input
        lstm_input = self.price_scaler.transform(price_data[['price']].values[-100:])
        lstm_input = np.reshape(lstm_input, (1, 100, 1))

        # Prepare other features
        other_features = pd.concat([
            volatility_data,
            correlation_data,
            market_data
        ], axis=1)
        other_features = self.feature_scaler.transform(other_features)

        return {
            'lstm_input': lstm_input,
            'other_features': other_features
        }

    def get_model_metrics(self):
        # In a real scenario, you would calculate these metrics based on recent performance
        # For now, we'll return some placeholder metrics
        dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
        return pd.DataFrame({
            'LSTM MAE': np.random.rand(30) * 0.1 + 0.9,
            'RF Accuracy': np.random.rand(30) * 0.1 + 0.8,
            'XGB R2': np.random.rand(30) * 0.1 + 0.7
        }, index=dates)

    def train_models(self, price_data, volatility_data, correlation_data, market_data):
        # This method would be used to train the models with new data
        # For now, we'll use mock data, but structure it to be easily replaced with real data
        logging.info("Training models with mock data...")
        
        # Generate mock data (replace this with real data when available)
        n_samples = len(price_data)
        n_features = 9
        
        # Price data for LSTM
        lstm_input = self.price_scaler.fit_transform(price_data[['price']].values)
        lstm_input = np.array([lstm_input[i:i+100] for i in range(n_samples-100)])
        lstm_target = lstm_input[:, -1, 0]
        
        # Other features for RF and XGB
        X = np.random.rand(n_samples, n_features)  # Replace with real features
        y_classifier = np.random.randint(0, 2, n_samples)  # Replace with real binary labels
        y_regressor = np.random.rand(n_samples) * 10  # Replace with real spread values
        
        # Train LSTM
        self.lstm_model.fit(lstm_input, lstm_target, epochs=5, batch_size=32, verbose=0)
        
        # Train RF and XGB
        X_scaled = self.feature_scaler.fit_transform(X)
        self.rf_classifier.fit(X_scaled, y_classifier)
        self.xgb_model.fit(X_scaled, y_regressor)
        
        # Save models
        self._save_models()
        
        logging.info("Models trained and saved successfully.")

if __name__ == "__main__":
    # This section can be used for testing the MLPredictor class
    config_path = 'config.json'  # Update this path as needed
    predictor = MLPredictor(config_path)
    
    # Generate some mock data for testing
    mock_price_data = pd.DataFrame({'price': np.cumsum(np.random.randn(200)) + 100})
    mock_volatility_data = pd.DataFrame(np.random.rand(1, 3), columns=['vol1', 'vol2', 'vol3'])
    mock_correlation_data = pd.DataFrame(np.random.rand(1, 3), columns=['corr1', 'corr2', 'corr3'])
    mock_market_data = pd.DataFrame(np.random.rand(1, 3), columns=['market1', 'market2', 'market3'])
    
    # Test prediction
    prediction = predictor.predict_opportunity(mock_price_data, mock_volatility_data, mock_correlation_data, mock_market_data)
    print("Prediction:", prediction)
    
    # Test model metrics
    metrics = predictor.get_model_metrics()
    print("Model Metrics:\n", metrics)
    
    # Test training
    predictor.train_models(mock_price_data, mock_volatility_data, mock_correlation_data, mock_market_data)
