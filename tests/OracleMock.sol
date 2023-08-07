// SPDX-License-Identifier: None
pragma solidity ^0.8.0;

interface IAggregatorV3Interface {

  function decimals() external view returns (uint8);
  function description() external view returns (string memory);
  function version() external view returns (uint256);

  // getRoundData and latestRoundData should both raise "No data present"
  // if they do not have data to report, instead of returning unset values
  // which could be misinterpreted as actual reported values.
  function getRoundData(uint80 _roundId)
    external
    view
    returns (
      uint80 roundId,
      int256 answer,
      uint256 startedAt,
      uint256 updatedAt,
      uint80 answeredInRound
    );
  function latestRoundData()
    external
    view
    returns (
      uint80 roundId,
      int256 answer,
      uint256 startedAt,
      uint256 updatedAt,
      uint80 answeredInRound
    );

}

contract MockV3Aggregator is IAggregatorV3Interface {
    uint8 public override decimals;
    string public override description;
    uint256 public override version;

    uint80 public roundId;
    int256 public price;
    uint256 public startedAt;
    uint256 public updatedAt;
    uint80 public answeredInRound;

    constructor(
        uint8 _decimals,
        int256 _price
    ) {
        decimals = _decimals;
        price = _price;
        description = "Mock V3 Aggregator";
        version = 1;
        roundId = uint80(1);
        startedAt = block.timestamp;
        updatedAt = block.timestamp;
        answeredInRound = uint80(1);
    }

    function updateAnswer(int256 _price) public {
        price = _price;
        roundId++;
        updatedAt = block.timestamp;
        answeredInRound = roundId;
    }

    function getRoundData(uint80 _roundId)
        public
        view
        override
        returns (
            uint80,
            int256,
            uint256,
            uint256,
            uint80
        )
    {
        require(_roundId <= roundId, "No data present for the roundId");

        return (
            roundId,
            price,
            startedAt,
            updatedAt,
            answeredInRound
        );
    }

    function latestRoundData()
        public
        view
        override
        returns (
            uint80,
            int256,
            uint256,
            uint256,
            uint80
        )
    {
        return (
            roundId,
            price,
            startedAt,
            updatedAt,
            answeredInRound
        );
    }
}