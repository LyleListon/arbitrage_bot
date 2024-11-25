from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Union, Type

# Robust import handling for machine learning libraries
try:
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import mutual_info_regression
except ImportError as e:
    print(f"Critical ML library import failed: {e}")
    print("Please install required dependencies: numpy, pandas, scikit-learn")
    
    # Provide mock classes to prevent total failure
    class MockArray:
        def __init__(self, data: Any = None):
            self.data = data or []
        
        def __getitem__(self, key: Any) -> Any:
            return self.data[key] if self.data else None
        
        def __len__(self) -> int:
            return len(self.data)
        
        def shape(self) -> Tuple[int, ...]:
            return (len(self.data),)
    
    class MockScaler:
        def __init__(self) -> None:
            pass
        
        def fit_transform(self, X: Any) -> Any:
            return X
        
        def transform(self, X: Any) -> Any:
            return X
        
        def inverse_transform(self, X: Any) -> Any:
            return X
    
    class MockPCA:
        def __init__(self, n_components: Optional[int] = None) -> None:
            self.n_components = n_components
        
        def fit_transform(self, X: Any) -> Any:
            return X
        
        def transform(self, X: Any) -> Any:
            return X
        
        def inverse_transform(self, X: Any) -> Any:
            return X
    
    # Fallback mock implementations
    np = type('MockNumpy', (), {
        'ndarray': MockArray, 
        'zeros': lambda shape: MockArray([0] * (shape[0] if isinstance(shape, tuple) else shape)),
        'array': lambda x: MockArray(x)
    })()
    
    pd = type('MockPandas', (), {
        'DataFrame': dict,
        'to_datetime': lambda x: x
    })()
    
    StandardScaler: Type[MockScaler] = MockScaler
    MinMaxScaler: Type[MockScaler] = MockScaler
    PCA: Type[MockPCA] = MockPCA
    
    def mutual_info_regression(X: Any, y: Any) -> List[float]:
        return [0.0] * (X.shape[1] if hasattr(X, 'shape') else 0)

class FeatureEngineeringPipeline:
    """
    Advanced feature engineering pipeline for arbitrage trading
    Provides comprehensive data transformation and feature generation techniques
    """
    
    def __init__(
        self, 
        scaling_method: str = 'standard', 
        pca_components: Optional[int] = None
    ):
        """
        Initialize feature engineering pipeline
        
        :param scaling_method: Method for feature scaling ('standard' or 'minmax')
        :param pca_components: Number of PCA components to retain
        """
        self.scaling_method = scaling_method
        self.pca_components = pca_components
        
        # Scalers and transformers
        self._scaler: Optional[Union[StandardScaler, MinMaxScaler]] = None
        self._pca: Optional[PCA] = None
        
        # Feature metadata
        self.feature_importances_: Dict[str, float] = {}
        self.original_feature_names_: List[str] = []
        self.transformed_feature_names_: List[str] = []
    
    def _select_scaler(self) -> Union[StandardScaler, MinMaxScaler]:
        """
        Select appropriate scaling method
        
        :return: Selected scaler
        """
        if self.scaling_method == 'standard':
            return StandardScaler()
        elif self.scaling_method == 'minmax':
            return MinMaxScaler()
        else:
            raise ValueError(f"Unsupported scaling method: {self.scaling_method}")
    
    def extract_blockchain_features(
        self, 
        blockchain_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract advanced blockchain-specific features
        
        :param blockchain_data: Raw blockchain transaction data
        :return: DataFrame with extracted features
        """
        try:
            features = blockchain_data.copy()
            
            # Temporal features
            features['hour_of_day'] = pd.to_datetime(features['timestamp']).dt.hour
            features['day_of_week'] = pd.to_datetime(features['timestamp']).dt.dayofweek
            
            # Transaction volume features
            features['rolling_volume_mean_1h'] = features['volume'].rolling(window=60).mean()
            features['rolling_volume_std_1h'] = features['volume'].rolling(window=60).std()
            
            # Price-related features
            features['price_change_rate'] = features['price'].pct_change()
            features['price_momentum'] = features['price'].diff()
            
            # Network activity indicators
            features['transaction_density'] = features['transaction_count'] / features['block_time']
            
            return features
        except Exception as e:
            print(f"Error in blockchain feature extraction: {e}")
            return blockchain_data
    
    def generate_cross_market_features(
        self, 
        market_data: List[pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Generate cross-market correlation and divergence features
        
        :param market_data: List of market dataframes from different exchanges
        :return: DataFrame with cross-market features
        """
        try:
            # Compute correlations
            price_correlations = pd.concat([df['price'] for df in market_data], axis=1).corr()
            volume_correlations = pd.concat([df['volume'] for df in market_data], axis=1).corr()
            
            # Generate divergence features
            cross_market_features = pd.DataFrame()
            for i in range(len(market_data)):
                for j in range(i+1, len(market_data)):
                    cross_market_features[f'price_divergence_{i}_{j}'] = (
                        market_data[i]['price'] - market_data[j]['price']
                    )
                    cross_market_features[f'volume_ratio_{i}_{j}'] = (
                        market_data[i]['volume'] / market_data[j]['volume']
                    )
            
            return cross_market_features
        except Exception as e:
            print(f"Error in cross-market feature generation: {e}")
            return pd.DataFrame()
    
    def compute_feature_importance(
        self, 
        X: np.ndarray, 
        y: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute feature importance using mutual information
        
        :param X: Input features
        :param y: Target variable
        :return: Dictionary of feature importances
        """
        try:
            importances = mutual_info_regression(X, y)
            self.feature_importances_ = dict(zip(self.transformed_feature_names_, importances))
            return self.feature_importances_
        except Exception as e:
            print(f"Error computing feature importance: {e}")
            return {}
    
    def transform(
        self, 
        X: pd.DataFrame, 
        fit: bool = True
    ) -> np.ndarray:
        """
        Transform features through scaling and optional dimensionality reduction
        
        :param X: Input feature DataFrame
        :param fit: Whether to fit scalers/transformers
        :return: Transformed feature array
        """
        try:
            # Store original feature names
            self.original_feature_names_ = list(X.columns)
            
            # Select and fit scaler
            if fit or self._scaler is None:
                self._scaler = self._select_scaler()
                X_scaled = self._scaler.fit_transform(X)
            else:
                X_scaled = self._scaler.transform(X)
            
            # Optional PCA
            if self.pca_components:
                if fit or self._pca is None:
                    self._pca = PCA(n_components=self.pca_components)
                    X_reduced = self._pca.fit_transform(X_scaled)
                else:
                    X_reduced = self._pca.transform(X_scaled)
                
                # Generate PCA feature names
                self.transformed_feature_names_ = [
                    f'pca_component_{i}' for i in range(self.pca_components)
                ]
                
                return X_reduced
            
            # If no PCA, use scaled features
            self.transformed_feature_names_ = self.original_feature_names_
            return X_scaled
        except Exception as e:
            print(f"Error in feature transformation: {e}")
            return X.to_numpy()
    
    def inverse_transform(self, X_transformed: np.ndarray) -> np.ndarray:
        """
        Reverse the feature transformation
        
        :param X_transformed: Transformed feature array
        :return: Original scale features
        """
        try:
            # Reverse PCA if used
            if self.pca_components and self._pca is not None:
                X_unscaled = self._pca.inverse_transform(X_transformed)
            else:
                X_unscaled = X_transformed
            
            # Reverse scaling
            if self._scaler is not None:
                return self._scaler.inverse_transform(X_unscaled)
            
            return X_unscaled
        except Exception as e:
            print(f"Error in inverse transformation: {e}")
            return X_transformed

def create_arbitrage_feature_pipeline(
    scaling_method: str = 'standard', 
    pca_components: Optional[int] = 10
) -> FeatureEngineeringPipeline:
    """
    Create a feature engineering pipeline optimized for arbitrage trading
    
    :param scaling_method: Scaling method to use
    :param pca_components: Number of PCA components
    :return: Configured feature engineering pipeline
    """
    return FeatureEngineeringPipeline(
        scaling_method=scaling_method, 
        pca_components=pca_components
    )
