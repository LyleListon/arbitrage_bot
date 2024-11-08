"""
Input validation and sanitization for the Arbitrage Bot.
"""

import re
from typing import Any, Dict, List, Union


def validate_network(network: str, allowed_networks: List[str]) -> str:
    """
    Validate the provided network.

    Args:
        network (str): Name of the network
        allowed_networks (List[str]): List of allowed network names

    Returns:
        str: Validated network name

    Raises:
        ValueError: If the network is not supported
    """
    if network not in allowed_networks:
        raise ValueError(f"Unsupported network: {network}. Allowed networks: {', '.join(allowed_networks)}")
    return network


def validate_address(address: str) -> str:
    """
    Validate an Ethereum address.

    Args:
        address (str): Ethereum address to validate

    Returns:
        str: Validated Ethereum address

    Raises:
        ValueError: If the address is not valid
    """
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        raise ValueError(f"Invalid Ethereum address: {address}")
    return address


def validate_positive_float(value: Union[str, float], name: str) -> float:
    """
    Validate a positive float value.

    Args:
        value (Union[str, float]): Value to validate
        name (str): Name of the value for error messages

    Returns:
        float: Validated positive float value

    Raises:
        ValueError: If the value is not a positive float
    """
    try:
        float_value = float(value)
        if float_value <= 0:
            raise ValueError
        return float_value
    except ValueError:
        raise ValueError(f"{name} must be a positive number")


def validate_positive_int(value: Union[str, int], name: str) -> int:
    """
    Validate a positive integer value.

    Args:
        value (Union[str, int]): Value to validate
        name (str): Name of the value for error messages

    Returns:
        int: Validated positive integer value

    Raises:
        ValueError: If the value is not a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError
        return int_value
    except ValueError:
        raise ValueError(f"{name} must be a positive integer")


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the configuration dictionary.

    Args:
        config (Dict[str, Any]): Configuration dictionary to validate

    Returns:
        Dict[str, Any]: Validated configuration dictionary

    Raises:
        ValueError: If any configuration value is invalid
    """
    validated_config = {}

    # Validate and add required fields
    required_fields = [
        "MIN_PROFIT_PERCENTAGE",
        "CHECK_INTERVAL",
        "TRADE_AMOUNT",
        "GAS_PRICE_PREMIUM",
        "SLIPPAGE_TOLERANCE",
        "MAX_RETRIES",
        "RETRY_DELAY",
        "MAX_TRADE_SIZE",
        "DAILY_TRADE_LIMIT",
        "MIN_DAILY_PROFIT",
        "MIN_DAILY_TRADES",
    ]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")

    validated_config["MIN_PROFIT_PERCENTAGE"] = validate_positive_float(config["MIN_PROFIT_PERCENTAGE"], "MIN_PROFIT_PERCENTAGE")
    validated_config["CHECK_INTERVAL"] = validate_positive_int(config["CHECK_INTERVAL"], "CHECK_INTERVAL")
    validated_config["TRADE_AMOUNT"] = validate_positive_int(config["TRADE_AMOUNT"], "TRADE_AMOUNT")
    validated_config["GAS_PRICE_PREMIUM"] = validate_positive_float(config["GAS_PRICE_PREMIUM"], "GAS_PRICE_PREMIUM")
    validated_config["SLIPPAGE_TOLERANCE"] = validate_positive_float(config["SLIPPAGE_TOLERANCE"], "SLIPPAGE_TOLERANCE")
    validated_config["MAX_RETRIES"] = validate_positive_int(config["MAX_RETRIES"], "MAX_RETRIES")
    validated_config["RETRY_DELAY"] = validate_positive_int(config["RETRY_DELAY"], "RETRY_DELAY")
    validated_config["MAX_TRADE_SIZE"] = validate_positive_int(config["MAX_TRADE_SIZE"], "MAX_TRADE_SIZE")
    validated_config["DAILY_TRADE_LIMIT"] = validate_positive_int(config["DAILY_TRADE_LIMIT"], "DAILY_TRADE_LIMIT")
    validated_config["MIN_DAILY_PROFIT"] = validate_positive_float(config["MIN_DAILY_PROFIT"], "MIN_DAILY_PROFIT")
    validated_config["MIN_DAILY_TRADES"] = validate_positive_int(config["MIN_DAILY_TRADES"], "MIN_DAILY_TRADES")

    # Validate NETWORKS
    if "NETWORKS" not in config:
        raise ValueError("Missing required configuration field: NETWORKS")

    validated_config["NETWORKS"] = {}
    for network, network_config in config["NETWORKS"].items():
        validated_network_config = {}
        for key in ["rpc_url", "contract_address", "price_feed_address"]:
            if key not in network_config:
                raise ValueError(f"Missing required field '{key}' for network '{network}'")
            if key.endswith("_address"):
                validated_network_config[key] = validate_address(network_config[key])
            else:
                validated_network_config[key] = network_config[key]
        validated_config["NETWORKS"][network] = validated_network_config

    return validated_config
