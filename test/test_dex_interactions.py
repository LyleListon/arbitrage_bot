import pytest
from web3 import Web3
from scripts.dex_interactions import (
    BaseDEXInteraction,
    UniswapV2Interaction,
    BalancerInteraction,
    create_dex_interaction
)
import json
import os
from unittest.mock import Mock, patch

# Test constants
TEST_ADDRESS = "0x1234567890123456789012345678901234567890"
TEST_AMOUNT = 1000000000000000000  # 1 ETH in wei
TEST_PATH = [
    "0x2222222222222222222222222222222222222222",
    "0x3333333333333333333333333333333333333333"
]

@pytest.fixture
def web3_mock():
    """Create a mock Web3 instance"""
    w3 = Mock()
    w3.eth.contract.return_value = Mock()
    return w3

@pytest.fixture
def mock_contract():
    """Create a mock contract instance"""
    contract = Mock()
    contract.functions = Mock()
    return contract

def test_create_dex_interaction_invalid_address(web3_mock):
    """Test creating DEX interaction with invalid address"""
    result = create_dex_interaction(web3_mock, "uniswapv2", "invalid_address")
    assert result is None

def test_create_dex_interaction_unsupported_dex(web3_mock):
    """Test creating DEX interaction with unsupported DEX"""
    result = create_dex_interaction(web3_mock, "unsupported", TEST_ADDRESS)
    assert result is None

def test_create_dex_interaction_success(web3_mock):
    """Test successful DEX interaction creation"""
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'
        interaction = create_dex_interaction(web3_mock, "uniswapv2", TEST_ADDRESS)
        assert isinstance(interaction, UniswapV2Interaction)

class TestUniswapV2Interaction:
    """Test UniswapV2 interaction implementation"""
    
    @pytest.fixture
    def uniswap_interaction(self, web3_mock, mock_contract):
        """Create UniswapV2 interaction instance"""
        web3_mock.eth.contract.return_value = mock_contract
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{}'
            return UniswapV2Interaction(web3_mock, TEST_ADDRESS)

    def test_get_amounts_out(self, uniswap_interaction, mock_contract):
        """Test getting output amounts"""
        expected = [TEST_AMOUNT, TEST_AMOUNT * 2]
        mock_contract.functions.getAmountsOut.return_value.call.return_value = expected
        
        result = uniswap_interaction.get_amounts_out(TEST_AMOUNT, TEST_PATH)
        assert result == expected
        mock_contract.functions.getAmountsOut.assert_called_with(TEST_AMOUNT, TEST_PATH)

    def test_check_liquidity(self, uniswap_interaction, mock_contract):
        """Test liquidity checking"""
        mock_contract.functions.getAmountsOut.return_value.call.return_value = [
            TEST_AMOUNT,
            int(TEST_AMOUNT * 1.01)  # 1% slippage
        ]
        
        result = uniswap_interaction.check_liquidity(
            TEST_PATH[0],
            TEST_PATH[1],
            TEST_AMOUNT
        )
        
        assert result['status'] == 'success'
        assert result['sufficient_liquidity'] is True
        assert 'max_impact' in result

class TestBalancerInteraction:
    """Test Balancer interaction implementation"""
    
    @pytest.fixture
    def balancer_interaction(self, web3_mock, mock_contract):
        """Create Balancer interaction instance"""
        web3_mock.eth.contract.return_value = mock_contract
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{}'
            return BalancerInteraction(web3_mock, TEST_ADDRESS)

    def test_get_pool_id_caching(self, balancer_interaction, mock_contract):
        """Test pool ID lookup and caching"""
        test_pool_id = "0x1234"
        mock_contract.functions.getPoolsWithTokens.return_value.call.return_value = [test_pool_id]
        mock_contract.functions.getPoolTokens.return_value.call.return_value = (
            TEST_PATH,  # tokens
            [TEST_AMOUNT, TEST_AMOUNT],  # balances
            100  # lastChangeBlock
        )
        
        # First call should query contract
        pool_id_1 = balancer_interaction._get_pool_id(TEST_PATH[0], TEST_PATH[1])
        assert pool_id_1 == test_pool_id
        mock_contract.functions.getPoolsWithTokens.assert_called_once()
        
        # Second call should use cache
        pool_id_2 = balancer_interaction._get_pool_id(TEST_PATH[0], TEST_PATH[1])
        assert pool_id_2 == test_pool_id
        # Should still be called only once (cached)
        mock_contract.functions.getPoolsWithTokens.assert_called_once()

    def test_get_amounts_out(self, balancer_interaction, mock_contract):
        """Test getting output amounts for Balancer"""
        test_pool_id = "0x1234"
        expected_output = -int(TEST_AMOUNT * 1.01)  # Negative for output amount
        
        # Mock pool ID lookup
        mock_contract.functions.getPoolsWithTokens.return_value.call.return_value = [test_pool_id]
        mock_contract.functions.getPoolTokens.return_value.call.return_value = (
            TEST_PATH,
            [TEST_AMOUNT, TEST_AMOUNT],
            100
        )
        
        # Mock queryBatchSwap
        mock_contract.functions.queryBatchSwap.return_value.call.return_value = [
            TEST_AMOUNT,
            expected_output
        ]
        
        result = balancer_interaction.get_amounts_out(TEST_AMOUNT, TEST_PATH)
        assert result == [TEST_AMOUNT, abs(expected_output)]
        mock_contract.functions.queryBatchSwap.assert_called_once()

    def test_check_liquidity(self, balancer_interaction, mock_contract):
        """Test liquidity checking for Balancer"""
        test_pool_id = "0x1234"
        
        # Mock pool ID lookup
        mock_contract.functions.getPoolsWithTokens.return_value.call.return_value = [test_pool_id]
        mock_contract.functions.getPoolTokens.return_value.call.return_value = (
            TEST_PATH,
            [TEST_AMOUNT * 100, TEST_AMOUNT * 100],  # Large liquidity
            100
        )
        
        # Mock swap queries
        mock_contract.functions.queryBatchSwap.return_value.call.return_value = [
            TEST_AMOUNT,
            -int(TEST_AMOUNT * 1.01)  # 1% slippage
        ]
        
        result = balancer_interaction.check_liquidity(
            TEST_PATH[0],
            TEST_PATH[1],
            TEST_AMOUNT
        )
        
        assert result['status'] == 'success'
        assert result['sufficient_liquidity'] is True
        assert result['max_impact'] < 5  # Impact should be low with high liquidity
