"""Price normalization utilities for token pairs"""
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def normalize_weth_dai_to_usdc(
    raw_price: Decimal,
    dai_usdc_ratio: Decimal
) -> Optional[Decimal]:
    """
    Normalize WETH/DAI price to USDC terms
    
    Args:
        raw_price: Raw WETH/DAI price (how many DAI per 1 WETH)
        dai_usdc_ratio: DAI/USDC price (how many USDC you get for 1 DAI)
    
    Returns:
        Normalized price in USDC terms
        
    Example:
        If WETH = 3000 DAI and 1 DAI = 0.983062 USDC:
        - We need to convert 3000 DAI to its USDC equivalent
        - Since each DAI is worth 0.983062 USDC
        - We multiply by 1/0.983062 to get USDC equivalent
        - 3000 * (1/0.983062) ≈ 3052 USDC
    """
    try:
        if raw_price <= 0 or dai_usdc_ratio <= 0:
            logger.warning(f"Invalid prices: raw_price={raw_price}, dai_usdc_ratio={dai_usdc_ratio}")
            return None
            
        # Convert DAI price to USDC
        # Since 1 DAI = 0.983062 USDC, multiply by 1/0.983062 to get USDC equivalent
        normalized_price = raw_price * (1 / dai_usdc_ratio)
        
        logger.info(f"WETH/DAI normalization:")
        logger.info(f"  Raw price: {raw_price} DAI per WETH")
        logger.info(f"  DAI/USDC ratio: {dai_usdc_ratio}")
        logger.info(f"  Normalized price: {normalized_price} USDC per WETH")
        
        return normalized_price
        
    except Exception as e:
        logger.error(f"Error normalizing WETH/DAI price: {e}")
        return None

def validate_normalized_price(price: Decimal, min_price: Decimal = Decimal('2000'), max_price: Decimal = Decimal('3500')) -> bool:
    """
    Validate if normalized price is within reasonable range
    
    Args:
        price: Normalized price to validate
        min_price: Minimum reasonable price (default 2000 USDC)
        max_price: Maximum reasonable price (default 3500 USDC)
    
    Returns:
        True if price is valid, False otherwise
    """
    try:
        if price <= 0:
            logger.warning(f"Invalid price <= 0: {price}")
            return False
            
        if not min_price <= price <= max_price:
            logger.warning(f"Price {price} outside reasonable range [{min_price}, {max_price}]")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating normalized price: {e}")
        return False
