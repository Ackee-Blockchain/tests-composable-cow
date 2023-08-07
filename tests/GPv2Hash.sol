// SPDX-License-Identifier: None

pragma solidity ^0.8.0;

import "../../source/lib/cowprotocol/src/contracts/libraries/GPv2Order.sol";

contract GPv2Hash {
    function hash(GPv2Order.Data memory order, bytes32 domainSeparator) public pure returns (bytes32) {
        return GPv2Order.hash(order, domainSeparator);
    }
}
