// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../QuoteManager.sol";
import {PathValidator as PathValidatorImpl} from "../PathValidator.sol";
import {PathFinder as PathFinderImpl} from "../PathFinder.sol";

contract CoreComponentsFactory is Ownable {
    // Events
    event ComponentsDeployed(
        address quoteManager,
        address pathValidator,
        address pathFinder
    );

    // Deploy core components
    function deployCoreComponents(
        address dexRegistry
    ) external returns (
        address quoteManager,
        address pathValidator,
        address pathFinder
    ) {
        // Deploy in correct order
        QuoteManager quoteManagerContract = new QuoteManager(dexRegistry);
        PathValidatorImpl pathValidatorContract = new PathValidatorImpl(address(quoteManagerContract));
        PathFinderImpl pathFinderContract = new PathFinderImpl(
            address(pathValidatorContract),
            address(quoteManagerContract)
        );

        // Transfer ownership (only for contracts that support it)
        pathValidatorContract.transferOwnership(owner());
        pathFinderContract.transferOwnership(owner());

        emit ComponentsDeployed(
            address(quoteManagerContract),
            address(pathValidatorContract),
            address(pathFinderContract)
        );

        return (
            address(quoteManagerContract),
            address(pathValidatorContract),
            address(pathFinderContract)
        );
    }
}
