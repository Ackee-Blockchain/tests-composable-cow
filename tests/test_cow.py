from woke.testing import *
from woke.testing.fuzzing import random_address
from pytypes.source.lib.cowprotocol.src.contracts.GPv2Settlement import GPv2Settlement
from pytypes.source.lib.cowprotocol.src.contracts.libraries.GPv2Order import GPv2Order
from pytypes.source.lib.safe.contracts.Safe import Safe
from pytypes.source.lib.safe.contracts.handler.ExtensibleFallbackHandler import ExtensibleFallbackHandler
from pytypes.source.lib.safe.contracts.handler.extensible.SignatureVerifierMuxer import ERC1271
from pytypes.source.lib.safe.contracts.proxies.SafeProxyFactory import SafeProxyFactory
from pytypes.source.src.ComposableCoW import ComposableCoW
from pytypes.source.src.interfaces.IConditionalOrder import IConditionalOrder
from pytypes.source.src.types.twap.libraries.TWAPOrder import TWAPOrder
from pytypes.source.src.types.twap.libraries.TWAPOrderMathLib import TWAPOrderMathLib
from pytypes.tests.GPv2Hash import GPv2Hash
from pytypes.tests.MyERC20 import MyERC20


def setup_safe(owners, treshold, handler, token, receiver):
    deployer = owners[0]
    # Singleton original Safe contract
    singleton   = Safe.deploy(from_=deployer)
    factory     = SafeProxyFactory.deploy(from_=deployer)
    # Proxy take singleton code and call create2
    proxy = factory.createProxyWithNonce(
        singleton,
        b"",
        42,
        from_=deployer
    ).return_value
    # Calling our Safe contract methods trough proxy address
    safe = Safe(proxy.address)
    safe.setup(
        owners,
        treshold,
        Address(0),     # no modules
        b"",            # no data
        handler,        # fallback handler (address)
        token,          # payment token (address)
        0,              # payment
        receiver,       # payment receiver (address)
        from_=deployer,
    )
    return safe


def setup_cows():
    # setup accounts
    deployer = default_chain.accounts[0]
    alice = default_chain.accounts[1]
    default_chain.set_default_accounts(deployer)

    # deploy libraries
    GPv2Order.deploy()
    TWAPOrderMathLib.deploy()
    TWAPOrder.deploy()

    # fork settlement
    settlement = GPv2Settlement("0x9008D19f58AAbD9eD0D60971565AA8510560ab41")

    # deploy contracts
    ccow = ComposableCoW.deploy(settlement)
    token0 = MyERC20.deploy("token0", "T0")
    token1 = MyERC20.deploy("token1", "T1")

    # get handler
    ehandler = ExtensibleFallbackHandler.deploy()

    # create safe
    safe = setup_safe([alice], 1, ehandler, random_address(), random_address())

    return safe, ccow, token0, token1


def validate_single_order(params, gpv2order_data, safe, ccow):
    # get payload
    payload = ComposableCoW.PayloadStruct(
        proof=[],
        params=params,
        offchainInput=Abi.encode(['uint256'], [10**18])
    )
    payload_values = [(payload.proof, (params.handler, params.salt, params.staticInput), payload.offchainInput)]
    payload_types = ["(bytes32[],(address,bytes32,bytes),bytes)"]
    payload_encoded = Abi.encode(payload_types, payload_values)

    # it is possible to tamper the order data
    gpv2order_values = [(gpv2order_data.sellToken, gpv2order_data.buyToken, gpv2order_data.receiver, gpv2order_data.sellAmount, gpv2order_data.buyAmount + 10**30, gpv2order_data.validTo, gpv2order_data.appData, gpv2order_data.feeAmount, gpv2order_data.kind, gpv2order_data.partiallyFillable, gpv2order_data.sellTokenBalance, gpv2order_data.buyTokenBalance)]
    gvp2order_types = ["(address,address,address,uint256,uint256,uint32,bytes32,uint256,bytes32,bool,bytes32,bytes32)"]
    gpv2order_encoded = Abi.encode(gvp2order_types, gpv2order_values)

    # do a proper hash
    gpv2hash = GPv2Hash.deploy()
    gpv2order_hash = gpv2hash.hash(gpv2order_data, ccow.domainSeparator())

    tx = ccow.isValidSafeSignature(safe, Address.ZERO, gpv2order_hash, ccow.domainSeparator(), b'', gpv2order_encoded, payload_encoded, request_type="tx")
    assert tx.return_value == ERC1271.isValidSignature.selector


def create_single_order(sco, static_input, ccow, safe):
    salt = b''
    params = IConditionalOrder.ConditionalOrderParams(sco, salt, static_input)
    params_hash = ccow.hash(params)
    ccow.create(params, True, from_=safe)
    assert ccow.singleOrders(safe, params_hash) == True
    return params, params_hash