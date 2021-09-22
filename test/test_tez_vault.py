from os.path import dirname, join
from unittest import TestCase
from decimal import Decimal

from pytezos import ContractInterface, MichelsonRuntimeError


source = 'tz1irF8HUsQp2dLhKNMhteG1qALNU9g3pfdN'
party = 'tz1h3rQ8wBxFd8L9B3d7Jhaawu6Z568XU3xY'
proxy = 'tz1grSQDByRpnVs7sPtaprNZRp531ZKz6Jmm'
secret = 'dca15ce0c01f61ab03139b4673f4bd902203dc3b898a89a5d35bad794e5cfd4f'
hashed_secret = bytes.fromhex('05bce5c12071fbca95b13d49cb5ef45323e0216d618bb4575c519b74be75e3da')
empty_storage = [{}, None]
project_dir = dirname(dirname(__file__))


class AtomexContractTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.atomex = ContractInterface.from_file(join(project_dir, 'build/contracts/tez_vault.tz'))
        cls.maxDiff = None

    def test_initiate(self):
        res = self.atomex \
            .initiate(participant=party,
                      hashed_secret=hashed_secret,
                      refund_time=6 * 3600,
                      payoff=20000) \
            .with_amount(1000000) \
            .interpret(storage=empty_storage,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': 980000,
                'refund_time': 6 * 3600,
                'payoff': 20000
            }
        }
        self.assertDictEqual(res_storage, res.storage[0])
        self.assertEqual([], res.operations)

    def test_initiate_proxy(self):
        res = self.atomex \
            .initiate(participant=party,
                      hashed_secret=hashed_secret,
                      refund_time=6 * 3600,
                      payoff=20000) \
            .with_amount(1000000) \
            .interpret(storage=empty_storage,
                       sender=proxy,
                       source=source,
                       now=0)

        res_storage = {
            hashed_secret: {
                'initiator': proxy,
                'participant': party,
                'amount': 980000,
                'refund_time': 6 * 3600,
                'payoff': 20000
            }
        }
        self.assertDictEqual(res_storage, res.storage[0])
        self.assertEqual([], res.operations)

    def test_initiate_same_secret(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 6 * 3600,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(participant=party,
                          hashed_secret=hashed_secret,
                          refund_time=6 * 3600,
                          payoff=Decimal('0.02')) \
                .with_amount(1000000) \
                .interpret(storage=initial_storage,
                           source=source,
                           now=0)

    def test_initiate_payoff_overflow(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(participant=party,
                          hashed_secret=hashed_secret,
                          refund_time=6 * 3600,
                          payoff=1100000) \
                .with_amount(1000000) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=0)

    def test_initiate_in_the_past(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(participant=party,
                          hashed_secret=hashed_secret,
                          refund_time=0,
                          payoff=Decimal('0.01')) \
                .with_amount(1000000) \
                .interpret(storage=empty_storage,
                           source=source,
                           now=6 * 3600)

    def test_initiate_same_party(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .initiate(participant=party,
                          hashed_secret=hashed_secret,
                          refund_time=0,
                          payoff=Decimal('0.01')) \
                .with_amount(1000000) \
                .interpret(storage=empty_storage,
                           source=party,
                           now=6 * 3600)

    def test_add_non_existent(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .add(hashed_secret) \
                .with_amount(1000000) \
                .interpret(storage=empty_storage)

    def test_add_another_address(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': 980000,
                'refund_time': 6 * 3600,
                'payoff': 20000
            }
        }, None]

        res = self.atomex \
            .add(hashed_secret) \
            .with_amount(1000000) \
            .interpret(storage=initial_storage, source=party, now=0)

        res_storage = initial_storage[0]
        res_storage[hashed_secret]['amount'] = 1980000
        self.assertDictEqual(res_storage, res.storage[0])

    def test_add_after_expiration(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 0,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .add(hashed_secret) \
                .with_amount(1000000) \
                .interpret(storage=initial_storage, source=source, now=6 * 3600)

    def test_redeem_by_third_party(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 60,
                'payoff': Decimal('0.02')
            }
        }, None]

        res = self.atomex \
            .redeem(secret) \
            .interpret(storage=initial_storage, source=source, now=0)

        self.assertDictEqual({hashed_secret: None}, res.storage[0])
        self.assertEqual(2, len(res.operations))

        redeem_tx = res.operations[0]
        self.assertEqual(party, redeem_tx['destination'])
        self.assertEqual('980000', redeem_tx['amount'])

        payoff_tx = res.operations[1]
        self.assertEqual(source, payoff_tx['destination'])
        self.assertEqual('20000', payoff_tx['amount'])

    def test_redeem_after_expiration(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 0,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .interpret(storage=initial_storage, source=party, now=60)

    def test_redeem_invalid_secret(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 60,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem('a' * 32) \
                .interpret(storage=initial_storage, source=source, now=0)

    def test_redeem_with_money(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 60,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .redeem(secret) \
                .with_amount(1000000) \
                .interpret(storage=initial_storage, source=source, now=0)

    def test_refund(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 0,
                'payoff': Decimal('0.02')
            }
        }, None]

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage, source=source, now=60)

        self.assertDictEqual({hashed_secret: None}, res.storage[0])
        self.assertEqual(1, len(res.operations))

        refund_tx = res.operations[0]
        self.assertEqual(source, refund_tx['destination'])
        self.assertEqual('1000000', refund_tx['amount'])

    def test_refund_before_expiration(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 60,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=initial_storage, source=source, now=0)

    def test_refund_non_existent(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .interpret(storage=empty_storage, source=source)

    def test_refund_with_money(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 0,
                'payoff': Decimal('0.02')
            }
        }, None]

        with self.assertRaises(MichelsonRuntimeError):
            self.atomex \
                .refund(hashed_secret) \
                .with_amount(1000000) \
                .interpret(storage=initial_storage, source=source, now=60)

    def test_refund_by_third_party(self):
        initial_storage = [{
            hashed_secret: {
                'initiator': source,
                'participant': party,
                'amount': Decimal('0.98'),
                'refund_time': 0,
                'payoff': Decimal('0.02')
            }
        }, None]

        res = self.atomex \
            .refund(hashed_secret) \
            .interpret(storage=initial_storage, source=party, now=60)

        self.assertDictEqual({hashed_secret: None}, res.storage[0])
        self.assertEqual(1, len(res.operations))

        refund_tx = res.operations[0]
        self.assertEqual(source, refund_tx['destination'])
        self.assertEqual('1000000', refund_tx['amount'])
