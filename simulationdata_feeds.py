"""
Generates non-stationary synthetic market data with regime shifts.
Implements the Chaos Engine's data corruption capabilities.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class SyntheticMarketGenerator:
    """Generates synthetic market data with controlled non-stationarity."""
    
    def __init__(self, seed: int = 42, chaos_level: float = 0.1):
        """
        Args:
            seed: Random seed for reproducibility
            chaos_level: Probability of chaotic events (0-1)
        """
        self.seed = seed
        self.chaos_level = chaos_level
        self.rng = np.random.default_rng(seed)
        self.regime = 0  # Current market regime
        self.regime_duration = 0
        logger.info(f"Initialized SyntheticMarketGenerator with chaos_level={chaos_level}")
    
    def _generate_regime_shift(self, current_step: int) -> None:
        """Randomly change market regime based on step count."""
        if self.rng.random() < 0.01 or self.regime_duration > 1000:
            self.regime = self.rng.integers(0, 4)
            self.regime_duration = 0
            logger.debug(f"Step {current_step}: Regime shifted to {self.regime}")
        self.regime_duration += 1
    
    def _apply_regime_parameters(self, base_return: float, base_vol: float) -> Tuple[float, float]:
        """Apply current regime's market characteristics."""
        if self.regime == 0:  # Bull market
            return base_return + 0.0002, base_vol * 0.8
        elif self.regime == 1:  # Bear market
            return base_return - 0.0003, base_vol * 1.2
        elif self.regime == 2:  # High volatility
            return base_return * 0.5, base_vol * 2.0
        else:  # Sideways
            return 0.0, base_vol * 0.6
    
    def _apply_chaos(self, data: pd.DataFrame, step: int) -> pd.DataFrame:
        """Apply chaotic events to the data."""
        if self.rng.random() < self.chaos_level:
            chaos_type = self.rng.choice(['spike', 'gap', 'freeze', 'noise'])
            idx = self.rng.integers(0, len(data))
            
            if chaos_type == 'spike':
                data.loc[idx, 'close'] *= 1 + self.rng.uniform(0.05, 0.15)
                logger.debug(f"Step {step}: Applied price spike at index {idx}")
            elif chaos_type == 'gap':
                data.loc[idx, 'volume'] = 0
                logger.debug(f"Step {step}: Applied volume gap at index {idx}")
            elif chaos_type == 'freeze':
                # Copy previous row, simulating frozen price
                if idx > 0:
                    data.loc[idx] = data.loc[idx-1]
                logger.debug(f"Step {step}: Applied price freeze at index {idx}")
            elif chaos_type == 'noise':
                noise = self.rng.normal(0, data['close'].std() * 0.1)
                data.loc[idx, 'close'] += noise
                logger.debug(f"Step {step}: Applied noise at index {idx}")
        
        return data
    
    def generate_series(self, 
                       n_points: int = 10000,
                       initial_price: float = 100.0,
                       base_volatility: float = 0.02) -> pd.DataFrame:
        """
        Generate a synthetic price series with regime shifts.
        
        Returns:
            DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        logger.info(f"Generating {n_points} data points...")
        
        # Initialize arrays
        timestamps = pd.date_range(start='2023-01-01', periods=n_points, freq='1min')
        prices = np.zeros(n_points)
        volumes = np.zeros(n_points)
        
        prices[0] = initial_price
        volumes[0] = 1000.0
        
        for i in range(1, n_points):
            # Generate regime shift
            self._generate_regime_shift(i)
            
            # Base parameters
            base_return = self.rng.normal(0, base_volatility / np.sqrt(252 * 24 * 60))  # Annualized to minute
            base_vol = base_volatility
            
            # Apply regime
            regime_return, regime_vol = self._apply_regime_parameters(base_return, base_vol)
            
            # Generate price movement
            ret = self.rng.normal(regime_return, regime_vol / np.sqrt(252 * 24 * 60))
            prices[i] = prices[i-1] * np.exp(ret)
            
            # Generate volume (correlated with volatility)
            volumes[i] = abs(self.rng.normal(1000, 300)) * (1 + regime_vol)
        
        # Create OHLC data (simplified - using same close for OHLC with small variation)
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices * (1 + self.rng.normal(0, 0.001, n_points)),
            'high': prices * (1 + abs(self.rng.normal(0, 0.002, n_points))),
            'low': prices * (1 - abs(self.rng.normal(0, 0.002, n_points))),
            'close': prices,
            'volume': volumes
        })
        
        # Apply chaos
        df = self._apply_chaos(df, n_points)
        
        logger.info(f"Generated series with {len(df)} points, price range: [{df['close'].min():.2f}, {df['close'].max():.2f}]")