# pylint: disable=no-member

from os.path import dirname, join
from unittest import TestCase

from pytezos import ContractInterface, pytezos, MichelsonRuntimeError

fa_address = 'KT1TjdF4H8H2qzxichtEbiCwHxCRM1SVx6B7'  # just some valid address
source = 'tz1cShoBMAfpWX35DUcQRsXbqAgWAB4tz7kj'
another_source = 'tz1grSQDByRpnVs7sPtaprNZRp531ZKz6Jmm'
party = 'tz1h3rQ8wBxFd8L9B3d7Jhaawu6Z568XU3xY'
proxy = 'tz1grSQDByRpnVs7sPtaprNZRp531ZKz6Jmm'
secret = 'dca15ce0c01f61ab03139b4673f4bd902203dc3b898a89a5d35bad794e5cfd4f'
hashed_secret = '05bce5c12071fbca95b13d49cb5ef45323e0216d618bb4575c519b74be75e3da'
hashed_secret_bytes = bytes.fromhex(hashed_secret)
empty_storage = {}
project_dir = dirname(dirname(__file__))

fa2_meta = """
storage unit;
parameter (or (unit %default)
              (list %transfer (pair (address %from_)
                              (list %txs (pair (address %to_)
                                               (pair (nat %token_id)
                                                     (nat %amount)))))));
code {}
"""


class AtomexContractTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.atomex = ContractInterface.create_from(join(project_dir, 'contracts/tezos/fa12_vault.tz'))
        cls.fa2 = ContractInterface.from_michelson(fa2_meta)
        cls.maxDiff = None

    def assertTransfer(self, parameters, from_, to_, txs):
        params = self.fa2.parameter.decode(**parameters)
        self.assertEqual({'transfer': [{
            'from_': from_,
            'txs': [
                {'to_': to_, 'token_id': tx[0], 'amount': tx[1]}
                for tx in txs
            ]}]
        }, params)

    def test_no_tez(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          tokenId=0,
                          totalAmount=1000) \
                .interpret(storage=empty_storage,
                           source=source,
                           amount=1000,
                           now=0)

    def test_initiate(self):
        res = self.atomex \
            .initiate(hashedSecret=hashed_secret,
                      participant=party,
                      refundTime=6 * 3600,
                      tokenAddress=fa_address,
                      tokenId=0,
                      totalAmount=1000) \
            .interpret(storage=empty_storage,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }
        self.assertDictEqual(res_storage, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(
            parameters=res.operations[0]['parameters'],
            from_=source,
            to_=res.operations[0]['source'],
            txs=[(0, 1000)])

    def test_initiate_proxy(self):
        res = self.atomex \
            .initiate(hashedSecret=hashed_secret,
                      participant=party,
                      refundTime=6 * 3600,
                      tokenAddress=fa_address,
                      tokenId=0,
                      totalAmount=1000) \
            .interpret(storage=empty_storage,
                       sender=proxy,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret_bytes: {
                'initiator': proxy,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }
        self.assertDictEqual(res_storage, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(
            parameters=res.operations[0]['parameters'],
            from_=proxy,
            to_=res.operations[0]['source'],
            txs=[(0, 1000)])

    def test_initiate_same_secret(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          tokenId=0,
                          totalAmount=1000) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_initiate_in_the_past(self):
        now = 1000000000
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          tokenId=0,
                          totalAmount=1000) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=now)

    def test_initiate_party_equals_source(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          tokenId=0,
                          totalAmount=1000) \
                .interpret(storage=empty_storage,
                           sender=proxy,
                           source=party,
                           now=0)

    def test_initiate_party_equals_sender(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          tokenId=0,
                          totalAmount=1000) \
                .interpret(storage=empty_storage,
                           sender=party,
                           source=source,
                           now=0)

    def test_redeem_by_third_party(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        res = self.atomex \
            .redeem(secret) \
            .interpret(storage=initial_storage,
                       source=source,
                       now=0)

        self.assertDictEqual({hashed_secret_bytes: None}, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(
            parameters=res.operations[0]['parameters'],
            from_=res.operations[0]['source'],
            to_=party,
            txs=[(0, 1000)])

    def test_redeem_after_expiration(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .interpret(storage=initial_storage,
                           source=party,
                           now=60)

    def test_redeem_invalid_secret(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 60,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem('a' * 32) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_redeem_with_money(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 60,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .with_amount(100000) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_refund(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage, 
                       source=source,
                       now=60)

        self.assertDictEqual({hashed_secret_bytes: None}, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(
            parameters=res.operations[0]['parameters'],
            from_=res.operations[0]['source'],
            to_=source,
            txs=[(0, 1000)])

    def test_third_party_refund(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage,
                       source=proxy,
                       now=60)

        self.assertDictEqual({hashed_secret_bytes: None}, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(
            parameters=res.operations[0]['parameters'],
            from_=res.operations[0]['source'],
            to_=source,
            txs=[(0, 1000)])

    def test_refund_before_expiration(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 60,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_refund_non_existent(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=0)

    def test_refund_with_money(self):
        initial_storage = {
            hashed_secret_bytes: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'tokenId': 0,
                'totalAmount': 1000
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .with_amount(100000) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=60)
