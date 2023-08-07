from flask import app
from woke.testing import *

from pytypes.source.src.ComposableCoW import ComposableCoW
from pytypes.source.src.interfaces.IConditionalOrder import IConditionalOrder
from pytypes.source.src.types.GoodAfterTime import GoodAfterTime
from pytypes.source.src.types.PerpetualStableSwap import PerpetualStableSwap
from pytypes.source.src.types.StopLoss import StopLoss
from pytypes.source.src.types.TradeAboveThreshold import TradeAboveThreshold
from pytypes.source.src.types.twap.TWAP import TWAP
from pytypes.source.src.types.twap.libraries.TWAPOrder import TWAPOrder
from pytypes.tests.OracleMock import MockV3Aggregator

from .config import FORK_URL
from .utils import MerkleTree, revert_handler
from .test_cow import setup_cows, validate_single_order, create_single_order


# Single order examples
@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_twap():
    safe, ccow, token0, token1 = setup_cows()
    sco = TWAP.deploy(ccow)

    token0.mint(safe, 1000 * 10**18)

    t = default_chain.blocks["pending"].timestamp

    twap_order = TWAPOrder.Data(
        sellToken=token0,
        buyToken=token1,
        receiver=safe,
        partSellAmount=10**18,
        minPartLimit=100,
        t0=t+100,
        n=10,
        t=1000,
        span=100,
        appData=b''
    )

    types = ["(address,address,address,uint256,uint256,uint256,uint256,uint256,uint256,bytes32)"]
    values = [(twap_order.sellToken, twap_order.buyToken, twap_order.receiver, twap_order.partSellAmount, twap_order.minPartLimit, twap_order.t0, twap_order.n, twap_order.t, twap_order.span, twap_order.appData)]

    static_input = Abi.encode(types, values)

    params, params_hash = create_single_order(sco, static_input, ccow, safe)

    with must_revert(IConditionalOrder.OrderNotValid):
        tx = ccow.getTradeableOrderWithSignature(
            owner=safe,
            params=params,
            offchainInput=Abi.encode(['uint256'], [10**18]),
            proof=[],
            request_type="tx"
        )

    default_chain.mine_many(101)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )

    validate_single_order(params, tx.return_value[0], safe, ccow)


@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_pss():
    safe, ccow, token0, token1 = setup_cows()
    sco = PerpetualStableSwap.deploy()

    token0.mint(safe, 1000 * 10**18)

    t = default_chain.blocks["pending"].timestamp

    pss_order = PerpetualStableSwap.Data(
        tokenA=token0,
        tokenB=token1,
        validityBucketSeconds=t+1000,
        halfSpreadBps=5000,
        appData=b''
    )

    types = ["(address,address,uint32,uint256,bytes32)"]
    values = [(pss_order.tokenA, pss_order.tokenB, pss_order.validityBucketSeconds, pss_order.halfSpreadBps, pss_order.appData)]
    static_input = Abi.encode(types, values)

    params, params_hash = create_single_order(sco, static_input, ccow, safe)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )
    #print(tx.console_logs)

    token0.mint(safe, 1000 * 10**18)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )
    #print(tx.console_logs)

    validate_single_order(params, tx.return_value[0], safe, ccow)


@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_tat():
    safe, ccow, token0, token1 = setup_cows()
    sco = TradeAboveThreshold.deploy()

    token0.mint(safe, 1000 * 10**18)

    t = default_chain.blocks["pending"].timestamp

    tat_order = TradeAboveThreshold.Data(
        sellToken=token0,
        buyToken=token1,
        receiver=Address.ZERO,
        validityBucketSeconds=t + 1000,
        threshold= (1000 * 10**18) + 1,
        appData=b''
    )

    types = ["(address,address,address,uint32,uint256,bytes32)"]
    values = [(tat_order.sellToken, tat_order.buyToken, tat_order.receiver, tat_order.validityBucketSeconds, tat_order.threshold, tat_order.appData)]

    static_input = Abi.encode(types, values)

    params, params_hash = create_single_order(sco, static_input, ccow, safe)

    with must_revert(IConditionalOrder.OrderNotValid):
        tx = ccow.getTradeableOrderWithSignature(
            owner=safe,
            params=params,
            offchainInput=Abi.encode(['uint256'], [10**18]),
            proof=[],
            request_type="tx"
        )

    token0.mint(safe, 1)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )

    validate_single_order(params, tx.return_value[0], safe, ccow)


@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_stoploss():
    safe, ccow, token0, token1 = setup_cows()
    sco = StopLoss.deploy()

    token0.mint(safe, 1000 * 10**18)

    oracle0 = MockV3Aggregator.deploy(18, 3000 * 10**18)
    oracle1 = MockV3Aggregator.deploy(18, 1000 * 10**18)

    sl_order = StopLoss.Data(
        sellToken=token0,
        buyToken=token1,
        sellAmount=1000,
        buyAmount=1000,
        appData=b'',
        receiver=Address.ZERO,
        isSellOrder=True,
        isPartiallyFillable=False,
        validityBucketSeconds= 60 * 15,
        sellTokenPriceOracle=oracle0,
        buyTokenPriceOracle=oracle1,
        strike=5*10**17,
        maxTimeSinceLastOracleUpdate=360
    )

    types = ["(address,address,uint256,uint256,bytes32,address,bool,bool,uint32,address,address,int256,uint256)"]
    values = [(sl_order.sellToken, sl_order.buyToken, sl_order.sellAmount, sl_order.buyAmount, sl_order.appData, sl_order.receiver, sl_order.isSellOrder, sl_order.isPartiallyFillable, sl_order.validityBucketSeconds, sl_order.sellTokenPriceOracle, sl_order.buyTokenPriceOracle, sl_order.strike, sl_order.maxTimeSinceLastOracleUpdate)]

    static_input = Abi.encode(types, values)

    params, params_hash = create_single_order(sco, static_input, ccow, safe)

    with must_revert(IConditionalOrder.OrderNotValid):
        tx = ccow.getTradeableOrderWithSignature(
            owner=safe,
            params=params,
            offchainInput=Abi.encode(['uint256'], [10**18]),
            proof=[],
            request_type="tx"
        )
        print(tx.console_logs)

    oracle0.updateAnswer(500 * 10**18)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )

    validate_single_order(params, tx.return_value[0], safe, ccow)


@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_gat():
    safe, ccow, token0, token1 = setup_cows()
    sco = GoodAfterTime.deploy()

    token0.mint(safe, 1000 * 10**18)

    # set swap guard
    # tx = ccow.setSwapGuard(alices_swapguard, from_=safe)
    # assert ccow.swapGuards(safe) == alices_swapguard
    # print(tx.events)

    # get static input
    t = default_chain.blocks["pending"].timestamp

    gat_order = GoodAfterTime.Data(
        sellToken=token0,
        buyToken=token1,
        receiver=Address.ZERO,
        sellAmount=100 * 10**18,
        minSellBalance=200 * 10**18,
        startTime=t + 100,
        endTime=t + 3000,
        allowPartialFill=False,
        priceCheckerPayload=b'',
        appData=b''
    )

    # Types in the correct order
    types = [
        "address",   # sellToken
        "address",   # buyToken
        "address",   # receiver
        "uint256",   # sellAmount
        "uint256",   # minSellBalance
        "uint256",   # startTime
        "uint256",   # endTime
        "bool",      # allowPartialFill
        "bytes",     # priceCheckerPayload
        "bytes32"      # appData
    ]
    types = ["(" + ",".join(types) + ")"]

    # Values in the correct order
    values = [(
        gat_order.sellToken,
        gat_order.buyToken,
        gat_order.receiver,
        gat_order.sellAmount,
        gat_order.minSellBalance,
        gat_order.startTime,
        gat_order.endTime,
        gat_order.allowPartialFill,
        gat_order.priceCheckerPayload,
        gat_order.appData
    )]
    static_input = Abi.encode(types, values)

    params, params_hash = create_single_order(sco, static_input, ccow, safe)

    default_chain.mine_many(101)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=[],
        request_type="tx"
    )

    validate_single_order(params, tx.return_value[0], safe, ccow)


# Multi order examples
@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_multi_order_gat():
    safe, ccow, token0, token1 = setup_cows()

    gat = GoodAfterTime.deploy()

    token0.mint(safe, 1000 * 10**18)

    # get static input
    t = default_chain.blocks["pending"].timestamp

    tree = MerkleTree()
    leaves = []
    params = []
    for i in range (3):
        gat_order = GoodAfterTime.Data(
            sellToken=token0,
            buyToken=token1,
            receiver=Address.ZERO,
            sellAmount=100 * 10**18,
            minSellBalance=200 * 10**18,
            startTime=t + (100 * i+1),
            endTime=t + 3000,
            allowPartialFill=False,
            priceCheckerPayload=b'',
            appData=b''
        )

        # Types in the correct order
        types = [
            "address",   # sellToken
            "address",   # buyToken
            "address",   # receiver
            "uint256",   # sellAmount
            "uint256",   # minSellBalance
            "uint256",   # startTime
            "uint256",   # endTime
            "bool",      # allowPartialFill
            "bytes",     # priceCheckerPayload
            "bytes32"      # appData
        ]
        types = ["(" + ",".join(types) + ")"]

        # Values in the correct order
        values = [(
            gat_order.sellToken,
            gat_order.buyToken,
            gat_order.receiver,
            gat_order.sellAmount,
            gat_order.minSellBalance,
            gat_order.startTime,
            gat_order.endTime,
            gat_order.allowPartialFill,
            gat_order.priceCheckerPayload,
            gat_order.appData
        )]
        static_input = Abi.encode(types, values)
        salt = b''
        params.append(IConditionalOrder.ConditionalOrderParams(gat, salt, static_input))
        leaves.append(ccow.hash(params[i]))
        tree.add_leaf(leaves[i])

    # set root
    tx = ccow.setRoot(tree.root, ComposableCoW.Proof(0,b''), from_=safe)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params[0],
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=tree.get_proof(0),
        request_type="tx"
    )

    with must_revert(IConditionalOrder.OrderNotValid):
        tx = ccow.getTradeableOrderWithSignature(
            owner=safe,
            params=params[1],
            offchainInput=Abi.encode(['uint256'], [10**18]),
            proof=tree.get_proof(1),
            request_type="tx"
        )

    default_chain.mine_many(101)

    tx = ccow.getTradeableOrderWithSignature(
        owner=safe,
        params=params[1],
        offchainInput=Abi.encode(['uint256'], [10**18]),
        proof=tree.get_proof(1),
        request_type="tx"
    )