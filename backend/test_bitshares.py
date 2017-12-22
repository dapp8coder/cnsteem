from bitshares import BitShares
from bitshares.blockchain import Blockchain
from pprint import pprint

from bitshares.account import Account

account = Account("skenan-bitshares")
print(account.balances)
print(account.openorders)
for h in account.history():
    print(h)
