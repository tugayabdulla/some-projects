from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_abi.packed import encode_abi_packed

token_abi = open('tokenabi.json', 'r').read().replace('\n', '')


class Web3Client:
    def __init__(self):
        self.web3_bsc = Web3(Web3.HTTPProvider('https://bsc-dataseed1.defibit.io/'))
        self.web3_bsc.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.web3_eth = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/5ba458236d754f25a0e08414fdac066a'))
        self.web3_eth.middleware_onion.inject(geth_poa_middleware, layer=0)

    def get_price(self, token: str, chain: str):
        if chain == 'bsc':
            pair_address = self._get_pair_address_pancakeswap(token)
            price, name, symbol, decimals = self._get_price_from_pancakeswap(pair_address, token)
        elif chain == 'ethereum':
            pair_address = self._get_pair_address_uniswap(token)
            price, name, symbol, decimals = self._get_price_from_uniswap(pair_address, token)
        else:
            price = 0
            name = ''
            symbol = ''
            decimals = 0
        return price, name, symbol, decimals

    def _get_price_from_uniswap(self, pair_address: str, token_address: str):
        pair_address = Web3.toChecksumAddress(pair_address)
        token_address = Web3.toChecksumAddress(token_address)
        pair_contract = self.web3_eth.eth.contract(address=pair_address, abi=token_abi)

        pair0_token = pair_contract.functions.token0().call()
        (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()

        if str(pair0_token) == str(token_address):
            token_amount = reserve0
            weth_amount = reserve1

        else:
            token_amount = reserve1
            weth_amount = reserve0

        weth_amount = weth_amount * 1e-18

        token_contract = self.web3_eth.eth.contract(address=token_address, abi=token_abi)
        token_decimals = token_contract.functions.decimals().call()
        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()
        token_amount = token_amount * 10 ** (-token_decimals)

        return weth_amount / token_amount, token_name, token_symbol, token_decimals

    def _get_pair_address_uniswap(self, token: str):
        weth = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
        uniswap_factory = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'

        token_b = weth
        pair_traded = [token, token_b]  # token_a, token_b are the address's
        pair_traded.sort()
        hexadem_ = '0x96e8ac4277198ff8b6f785478aa9a39f403cb768dd02cbee326c3e7da348845f'
        abiEncoded_1 = encode_abi_packed(['address', 'address'], (
            pair_traded[0], pair_traded[1]))
        salt_ = Web3.solidityKeccak(['bytes'], ['0x' + abiEncoded_1.hex()])
        abiEncoded_2 = encode_abi_packed(['address', 'bytes32'], (uniswap_factory, salt_))
        resPair = Web3.solidityKeccak(['bytes', 'bytes'], ['0xff' + abiEncoded_2.hex(), hexadem_])[12:]
        return resPair.hex()

    def _get_price_from_pancakeswap(self, pair_address: str, token_address: str):
        pair_address = Web3.toChecksumAddress(pair_address)
        token_address = Web3.toChecksumAddress(token_address)
        pair_contract = self.web3_bsc.eth.contract(address=pair_address, abi=token_abi)
        pair0_token = pair_contract.functions.token0().call()
        (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()

        if str(pair0_token) == str(token_address):
            token_amount = reserve0
            wbnb_amount = reserve1

        else:
            token_amount = reserve1
            wbnb_amount = reserve0

        wbnb_amount = wbnb_amount * 1e-18

        token_contract = self.web3_bsc.eth.contract(address=token_address, abi=token_abi)
        token_decimals = token_contract.functions.decimals().call()
        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()
        token_amount = token_amount * 10 ** (-token_decimals)

        return wbnb_amount / token_amount, token_name, token_symbol, token_decimals

    def _get_pair_address_pancakeswap(self, token: str):
        wbnb = '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
        pancakeswap_factory = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'

        token_b = wbnb
        pair_traded = [token, token_b]  # token_a, token_b are the address's
        pair_traded.sort()
        hexadem_ = '0x00fb7f630766e6a796048ea87d01acd3068e8ff67d078148a3fa3f4a84f69bd5'
        abiEncoded_1 = encode_abi_packed(['address', 'address'], (
            pair_traded[0], pair_traded[1]))
        salt_ = Web3.solidityKeccak(['bytes'], ['0x' + abiEncoded_1.hex()])
        abiEncoded_2 = encode_abi_packed(['address', 'bytes32'], (pancakeswap_factory, salt_))
        resPair = Web3.solidityKeccak(['bytes', 'bytes'], ['0xff' + abiEncoded_2.hex(), hexadem_])[12:]
        return resPair.hex()

    def get_bnb_price(self):
        wbnb_busd_pair = self.web3_bsc.eth.contract(address='0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16', abi=token_abi)

        reserve1, reserve2, _ = wbnb_busd_pair.functions.getReserves().call()
        price = max(reserve1, reserve2) / min(reserve2, reserve1)
        return float(price)

    def get_ether_price(self):
        weth_usdc_pair = self.web3_eth.eth.contract(address='0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc', abi=token_abi)

        reserve1, reserve2, _ = weth_usdc_pair.functions.getReserves().call()
        price = min(reserve1, reserve2) / max(reserve2, reserve1)
        return float(price) * 10 ** 12

    def check_is_contract(self, address, chain):
        web3 = self.web3_bsc if chain == 'bsc' else self.web3_eth
        address = web3.toChecksumAddress(address)
        try:
            code = web3.eth.get_code(address)
            code = code.hex()
            print(code)
        except:
            return False

        return code != '' and code != '0x'
