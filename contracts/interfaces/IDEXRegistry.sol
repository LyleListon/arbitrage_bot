// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IDEXRegistry {
    struct DEXInfo {
        address router;
        string protocol;
        uint256 maxSlippage;
        bool isActive;
    }
    
    function dexes(address) external view returns (
        address router,
        string memory protocol,
        uint256 maxSlippage,
        bool isActive
    );
    
    function gasOverhead(address) external view returns (uint256);
    function activeDEXList(uint256) external view returns (address);
    
    function getActiveDEXes() external view returns (address[] memory);
    function isPairSupported(address router, address baseToken, address quoteToken) external view returns (bool);
    function validateTrade(address router, address baseToken, address quoteToken) external view;
    
    function getDEXInfo(address router) external view returns (
        string memory protocol,
        uint256 maxSlippage,
        bool isActive,
        uint256 overhead
    );
}
