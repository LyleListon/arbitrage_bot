// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../../dex/PriceFeedRegistry.sol";
import "../../dex/DEXRegistry.sol";

contract RegistryFactory is Ownable {
    // Events
    event RegistriesDeployed(
        address priceFeed,
        address dex
    );
    
    // Deploy registries
    function deployRegistries() external returns (address priceFeed, address dex) {
        PriceFeedRegistry priceFeedRegistry = new PriceFeedRegistry();
        DEXRegistry dexRegistry = new DEXRegistry();
        
        // Transfer ownership
        priceFeedRegistry.transferOwnership(owner());
        dexRegistry.transferOwnership(owner());
        
        emit RegistriesDeployed(
            address(priceFeedRegistry),
            address(dexRegistry)
        );
        
        return (address(priceFeedRegistry), address(dexRegistry));
    }
}
