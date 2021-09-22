from os.path import dirname, join
from unittest import TestCase

from pytezos import ContractInterface, MichelsonRuntimeError

fa_address = 'KT1TjdF4H8H2qzxichtEbiCwHxCRM1SVx6B7' # should be deployed in the current test network
source = 'tz1cShoBMAfpWX35DUcQRsXbqAgWAB4tz7kj'
another_source = 'tz1grSQDByRpnVs7sPtaprNZRp531ZKz6Jmm'
party = 'tz1h3rQ8wBxFd8L9B3d7Jhaawu6Z568XU3xY'
proxy = 'tz1grSQDByRpnVs7sPtaprNZRp531ZKz6Jmm'
secret = 'dca15ce0c01f61ab03139b4673f4bd902203dc3b898a89a5d35bad794e5cfd4f'
hashed_secret = bytes.fromhex('05bce5c12071fbca95b13d49cb5ef45323e0216d618bb4575c519b74be75e3da')
empty_storage = {}
project_dir = dirname(dirname(__file__))

fa12_meta = """
storage unit;
parameter (or (unit %default)
              (pair %transfer (address %from) 
                              (pair (address %to) 
                                    (nat %value))));
code {}
"""


class AtomexContractTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.atomex = ContractInterface.from_file(join(project_dir, 'build/contracts/fa12_vault.tz'))
        cls.fa12 = ContractInterface.from_michelson(fa12_meta)
        cls.maxDiff = None

    def assertTransfer(self, src, dst, amount, parameters):
        params = self.fa12.contract.parameter.decode(**parameters)
        self.assertEqual({'from': src, 'to': dst, 'value': amount}, params['transfer'])

    def test_no_tez(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          totalAmount=1000,
                          payoffAmount=0) \
                .with_amount(1000) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=0)

    def test_initiate(self):
        res = self.atomex \
            .initiate(hashedSecret=hashed_secret,
                      participant=party,
                      refundTime=6 * 3600,
                      tokenAddress=fa_address,
                      totalAmount=1000,
                      payoffAmount=10) \
            .interpret(storage=empty_storage,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'payoffAmount': 10,
                'totalAmount': 1000,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address
            }
        }
        self.assertDictEqual(res_storage, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(src=source,
                            dst=res.operations[0]['source'],
                            amount=1000,
                            parameters=res.operations[0]['parameters'])

    def test_initiate_proxy(self):
        res = self.atomex \
            .initiate(hashedSecret=hashed_secret,
                      participant=party,
                      refundTime=6 * 3600,
                      tokenAddress=fa_address,
                      totalAmount=1000,
                      payoffAmount=10) \
            .interpret(storage=empty_storage,
                       sender=proxy,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret: {
                'initiator': proxy,
                'participant': party,
                'payoffAmount': 10,
                'totalAmount': 1000,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address
            }
        }
        self.assertDictEqual(res_storage, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(src=proxy,
                            dst=res.operations[0]['source'],
                            amount=1000,
                            parameters=res.operations[0]['parameters'])

    def test_initiate_same_secret(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 0
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          totalAmount=1000,
                          payoffAmount=0) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_initiate_payoff_overflow(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          totalAmount=100,
                          payoffAmount=101) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=0)

    def test_initiate_in_the_past(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=0,
                          tokenAddress=fa_address,
                          totalAmount=1000,
                          payoffAmount=0) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=6 * 3600)

    def test_initiate_party_equals_source(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(hashedSecret=hashed_secret,
                          participant=party,
                          refundTime=6 * 3600,
                          tokenAddress=fa_address,
                          totalAmount=1000,
                          payoffAmount=0) \
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
                          totalAmount=1000,
                          payoffAmount=0) \
                .interpret(storage=empty_storage,
                           sender=party,
                           source=source,
                           now=0)

    def test_redeem_by_third_party(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        res = self.atomex \
            .redeem(secret) \
            .interpret(storage=initial_storage, source=source, now=0)

        self.assertDictEqual({hashed_secret: None}, res.storage)
        self.assertEqual(2, len(res.operations))
        self.assertTransfer(src=res.operations[0]['source'],
                            dst=party,
                            amount=990,
                            parameters=res.operations[0]['parameters'])
        self.assertTransfer(src=res.operations[0]['source'],
                            dst=source,
                            amount=10,
                            parameters=res.operations[1]['parameters'])

    def test_redeem_after_expiration(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .interpret(storage=initial_storage, source=party, now=60)

    def test_redeem_invalid_secret(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem('a' * 32) \
                .interpret(storage=initial_storage, source=source, now=60)

    def test_redeem_with_money(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .with_amount(100000) \
                .interpret(storage=initial_storage, source=source, now=60)

    def test_refund(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage, source=source, now=60)

        self.assertDictEqual({hashed_secret: None}, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(src=res.operations[0]['source'],
                            dst=source,
                            amount=1000,
                            parameters=res.operations[0]['parameters'])

    def test_third_party_refund(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage, source=party, now=60)

        self.assertDictEqual({hashed_secret: None}, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(src=res.operations[0]['source'],
                            dst=source,
                            amount=1000,
                            parameters=res.operations[0]['parameters'])

    def test_refund_before_expiration(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 60,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=initial_storage, source=source, now=0)

    def test_refund_non_existent(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=empty_storage, source=source, now=0)

    def test_refund_with_money(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 60,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .with_amount(100000) \
                .interpret(storage=initial_storage, source=source, now=0)

    def test_add_invalid_hashed_secret(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .add(hashedSecret=hashed_secret, addAmount=100) \
                .interpret(storage=empty_storage, source=source, now=0)

    def test_add_after_expiration(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 0,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .add(hashedSecret=hashed_secret, addAmount=100) \
                .interpret(storage=initial_storage, source=source, now=60)

    def test_add_another_source(self):
        initial_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address,
                'totalAmount': 1000,
                'payoffAmount': 10
            }
        }

        res = self.atomex \
            .add(hashedSecret=hashed_secret, addAmount=100) \
            .interpret(storage=initial_storage, source=another_source, now=0)

        res_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'payoffAmount': 10,
                'totalAmount': 1100,
                'refundTime': 6 * 3600,
                'tokenAddress': fa_address
            }
        }
        self.assertDictEqual(res_storage, res.storage)
        self.assertEqual(1, len(res.operations))
        self.assertTransfer(src=another_source,
                            dst=res.operations[0]['source'],  # Atomex address
                            amount=100,
                            parameters=res.operations[0]['parameters'])
