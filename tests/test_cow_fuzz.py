from hmac import new
from traitlets import default
from woke.testing import *
from woke.testing.fuzzing import *

from pytypes.source.lib.safe.contracts.Safe import Safe
from pytypes.source.src.ComposableCoW import ComposableCoW
from pytypes.source.src.interfaces.IConditionalOrder import IConditionalOrder
from pytypes.source.src.types.twap.TWAP import TWAP
from pytypes.source.src.types.twap.libraries.TWAPOrder import TWAPOrder
from pytypes.tests.MyERC20 import MyERC20

from .config import FORK_URL
from .utils import revert_handler
from .test_cow import setup_cows, create_single_order


def shoudl_revert(partSellAmount, minPartLimit, t0, n, t, span):
    blocktimestamp = default_chain.blocks["pending"].timestamp

    if not partSellAmount > 0:
        return True, IConditionalOrder.OrderNotValid("invalid part sell amount")
    if not minPartLimit > 0:
        return True, IConditionalOrder.OrderNotValid("invalid min part limit")
    if not t0 < (2**32 - 1):
        return True, IConditionalOrder.OrderNotValid("invalid start time")
    if not n > 1 and n < (2**32 - 1):
        return True, IConditionalOrder.OrderNotValid("invalid num parts")
    if not t > 0 and t < 31_536_000:
        return True, IConditionalOrder.OrderNotValid("invalid frequency")
    if not span <= t:
        return True, IConditionalOrder.OrderNotValid("invalid span")

    if not t0 <= blocktimestamp:
        return True, IConditionalOrder.OrderNotValid("before twap start")
    if not blocktimestamp < t0 + (n*t):
        return True, IConditionalOrder.OrderNotValid("after twap finish")

    part = (blocktimestamp - t0) // t
    if span == 0:
        valid_to = t0 + (part+1) * t - 1
    else:
        valid_to = t0 + (n*part) + span - 1
    if not blocktimestamp <= valid_to:
        return True, IConditionalOrder.OrderNotValid("not within span")

    return False, None


# Example of writing a fuzz test, it should definitely deserve to be extended
class CoWOrderFuzzTest(FuzzTest):
    safe: Safe
    ccow: ComposableCoW
    token0: MyERC20
    token1: MyERC20
    twap: TWAP

    def __init__(self):
        self.safe, self.ccow, self.token0, self.token1 = setup_cows()
        self.twap = TWAP.deploy(self.ccow)

    def pre_sequence(self) -> None:
        self.token0.mint(self.safe, 2**256-1)

    @flow()
    def flow_get_tradeable_order(self) -> None:
        now = default_chain.blocks["pending"].timestamp

        # fuzzing these values
        partSellAmount = random_int(0, 10**18, edge_values_prob=0.3)
        minPartLimit = random_int(0, 10**6)
        t0 = now - random_int(0, 10**3)
        n = random_int(0, 10**6)
        t = random_int(0, 10**6)
        span = random_int(0, 10**6)

        # construct order
        twap_order = TWAPOrder.Data(
            sellToken=self.token0,
            buyToken=self.token1,
            receiver=self.safe,
            partSellAmount=partSellAmount,
            minPartLimit=minPartLimit,
            t0=t0,
            n=n,
            t=t,
            span=span,
            appData=b''
        )

        # abi encode it
        types = ["(address,address,address,uint256,uint256,uint256,uint256,uint256,uint256,bytes32)"]
        values = [(twap_order.sellToken, twap_order.buyToken, twap_order.receiver, twap_order.partSellAmount, twap_order.minPartLimit, twap_order.t0, twap_order.n, twap_order.t, twap_order.span, twap_order.appData)]
        static_input = Abi.encode(types, values)

        # create order
        params, params_hash = create_single_order(self.twap, static_input, self.ccow, self.safe)

        # check if should revert
        should_revert, revert_reason = shoudl_revert(partSellAmount, minPartLimit, t0, n, t, span)
        print("---> should_revert: " + str(should_revert) + " , revert_reason: " + str(revert_reason))
        tx = TransactionAbc
        if (should_revert):
            with must_revert(revert_reason):
                tx = self.ccow.getTradeableOrderWithSignature(
                    owner=self.safe,
                    params=params,
                    offchainInput=Abi.encode(['uint256'], [10**18]),
                    proof=[],
                    request_type="tx"
                )
                # we want values if not reverted
                print(tx.return_value)
        else:
            tx = self.ccow.getTradeableOrderWithSignature(
                owner=self.safe,
                params= params,
                offchainInput=Abi.encode(['uint256'], [10**18]),
                proof=[],
                request_type="tx"
            )

@default_chain.connect(fork=FORK_URL)
@on_revert(revert_handler)
def test_single_order_twap():
    CoWOrderFuzzTest().run(100, 100)