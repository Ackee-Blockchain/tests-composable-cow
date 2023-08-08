# Tests for Composable Cow
This repository serves as an example of tests written in a testing and development framework called [Woke](https://github.com/Ackee-Blockchain/woke).

<p align="center">
  <img src="https://user-images.githubusercontent.com/56036748/259106454-2994669f-525c-479d-bbc9-c78da6f401de.png" width="80">
</p>

## Setup

1. Clone this repository
2. `git submodule update --init --recursive` if not cloned with `--recursive`
3. `cd source && forge install && cd ..` to install dependencies
4. `woke init pytypes` to generate pytypes
5. `woke test` to run tests

Tested with `woke` version `3.5.0` and `anvil` version `anvil 0.1.0 (638bd2e 2023-05-23T13:45:12.329779000Z)`. Forking was done on Ethereum mainnet with the following block number: `14660289`.
