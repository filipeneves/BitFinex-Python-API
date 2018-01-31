from __future__ import absolute_import
import requests
import time
import json
import hashlib
import base64
import hmac

#
# Constants
#

BITFINEX_API_URL = 'https://api.bitfinex.com'
BITFINEX_API_VERSION = 'v1'

class BitFinex:

    apikey = None
    apisecret = None

    def __init__(self, apikey, apisecret):
        """
        Constructor for BitFinex
        :param apikey:
        :param apisecret:
        """
        self.apikey = apikey
        self.apisecret = apisecret
        pass

    #
    # Private requests
    #

    def my_account(self):
        """
        Gets your account information
        :return:
        """

        url = self.generate_url('account_infos')

        payload = {
            "request": "/v1/account_infos",
            "nonce": self.nonce
        }

        return self.call('post', url, payload)

    def my_balance(self):

        url = self.generate_url('balances')

        payload = {
            "request": '/v1/balances',
            "nonce": self.nonce
        }

        return self.call('post', url, payload)

    def my_trades(self, symbol='btcusd', limit=50, timestamp=None, until=None, reverse=0):
        """
        Gets all your trades
        :param symbol: Optional. The name of the symbol, to get list of symbols call /symbols
        :param limit: Optional. Limit the number of trades returned. Default 50.
        :param timestamp: Optional. Trades made this date won't be returned.
        :param until: Optional. Trades made after this date won't be returned.
        :param reverse: Optional. Revert listing of trades (oldest to newest). Default is newest to oldest
        :return:
        """

        url = self.generate_url('mytrades')

        payload = {
            "request": '/v1/mytrades',
            "nonce": self.nonce,
            "symbol": symbol,
            "limit_trades": limit,
            "reverse": reverse
        }

        if timestamp:
            payload['timestamp'] = timestamp

        if until:
            payload['until'] = until

        return self.call('post', url, payload)

    def my_history(self, currency='USD', limit=500, timestamp=None, until=None, reverse=0):
        """
        View balance history across ledger entries
        :param currency: Optional. Currency to look for. Defaults USD.
        :param limit: Optional. Limit the number of trades returned. Default 500.
        :param timestamp: Optional. Trades made this date won't be returned.
        :param until: Optional. Trades made after this date won't be returned.
        :param reverse: Optional. Revert listing of trades (oldest to newest). Default is newest to oldest
        :return:
        """

        url = self.generate_url('history');

        payload = {
            "request": '/v1/history',
            "nonce": self.nonce,
            "currency": currency,
            "limit": limit,
            "reverse": reverse
        }

        if timestamp:
            payload["timestamp"] = timestamp

        if until:
            payload["until"] = until

        return self.call('post', url, payload)

    def do_deposit(self, method='bitcoin', wallet='exchange', renew=0):
        """
        Returns a deposit address to make a new deposit
        :param method: Method of deposit accepted: bitcoin, litecoin, ethereum, tetheruso, ethereumc, zcash, monero, iota, bcash
        :param wallet: Wallet to deposit it. Accepted: trading, exchange, deposit. The wallet needs to already exist
        :param renew: If set to 1, it will return a new, unused, address to deposit to.
        :return:
        """

        url = self.generate_url('deposit/new')

        payload = {
            "request": '/v1/deposit/new',
            "nonce": self.nonce,
            "method": method,
            "wallet_name": wallet,
            "renew": renew
        }

        return self.call('post', url, payload)


    #
    # Public requests
    #

    def symbols(self):
        """
        A list of symbol names
        :return:
        """
        return self.call('get', self.generate_url('symbols'))

    def symbols_details(self):
        """
        List of valid symbol IDs and the pair details
        :return:
        """
        return self.call('get', self.generate_url('symbols_details'))

    def book(self, symbol='btcusd'):
        """
        Full order book
        :param symbol:
        :return:
        """
        return self.call('get', self.generate_url('book', None, symbol))

    def ticker(self, symbol='btcusd'):
        """
        The ticker is a high level overview of the state of the market.
        :param symbol:
        :return:
        """
        return self.call('get', self.generate_url('pubticker', None, symbol))

    def stats(self, symbol='btcusd'):
        """
        Various stats about the requested pair
        :param symbol:
        :return:
        """
        return self.call('get', self.generate_url('stats', None, symbol))

    def lendbook(self, currency='usd'):
        """
        Full margin funding book
        :param currency:
        :return:
        """
        return self.call('get', self.generate_url('lendbook', None, currency))

    def trades(self, symbol='btcusd'):
        """
        Get a list of the most recent trades for the given symbol
        :param symbol:
        :return:
        """
        return self.call('get', self.generate_url('trades', None, symbol))

    def lends(self, currency='usd'):
        """
        Get a list of the most recent funding data for the given currency.
        :param currency:
        :return:
        """
        return self.call('get', self.generate_url('lends', None, currency))


    # Request and authentication

    @property
    def nonce(self):
        """
        Returns a nonce... yeah.
        :return:
        """
        return str(time.time() * 1000000)

    def server(self):
        """
        :return: The web address in the correct format (with version)
        """
        return u"{0:s}/{1:s}".format(BITFINEX_API_URL, BITFINEX_API_VERSION)

    def call(self, method, url, payload=None):
        """
        Makes the actual HTTP request, POST or GET depending on the method
        :param method:
        :param url:
        :param payload:
        :return:
        """
        if method == 'post':
            return requests.post(url, headers=self.generate_headers(payload), verify=True).json()
        else:
            return requests.get(url, timeout=5.0).json()

    def generate_url(self, path, parameters=None, args=None):
        """
        Generates the URL to be executed
        :param path:
        :param parameters:
        :param args:
        :return:
        """
        url = "%s/%s" % (self.server(), path)

        if args:
            url = "%s/%s" % (url, args)

        if parameters:
            url = "%s?%s" % (url, self.parse_parameters(parameters))

        return url

    def parse_parameters(self, parameters):
        """
        Parse the parameters that go through the URL generation and basically format them nicely
        :param parameters:
        :return:
        """
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

    def generate_headers(self, payload):
        """
        Generates the headers to be sent with the request.
        :param payload: Generated by the request, dict of all the elements necessary for the headers to be created
        :return:
        """
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))

        h = hmac.new(self.apisecret.encode('utf8'), data, hashlib.sha384)
        sig = h.hexdigest()

        return {
            "X-BFX-APIKEY": self.apikey,
            "X-BFX-SIGNATURE": sig,
            "X-BFX-PAYLOAD": data
        }