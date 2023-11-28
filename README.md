# Tests for Composable Cow
This repository serves as an example of tests written in a development and testing framework called [Wake](https://github.com/Ackee-Blockchain/wake).

![horizontal splitter](https://github.com/Ackee-Blockchain/wake-detect-action/assets/56036748/ec488c85-2f7f-4433-ae58-3d50698a47de)

## Setup

1. Clone this repository
2. `git submodule update --init --recursive` if not cloned with `--recursive`
3. `cd source && forge install && cd ..` to install dependencies
4. `wake init pytypes` to generate pytypes
5. `wake test` to run tests

Tested with `wake` version `4.0.0` and `anvil` version `anvil 0.1.0 (638bd2e 2023-05-23T13:45:12.329779000Z)`. Forking was done on Ethereum mainnet with the following block number: `14660289`.
