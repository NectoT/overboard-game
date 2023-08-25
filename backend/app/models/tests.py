'''Набор (рандомных) тестов для проверки моделей модуля'''

import unittest
from unittest import TestResult

from .game import Observable, UNKNOWN, SuppliesEnum
from .server_events import NewSupplies


class TestObservable(unittest.TestCase):

    def test_unknown_converstion(self):
        class O(Observable):
            field: str | UNKNOWN

        o = O(field='field')

        self.assertEqual(o.observer_viewpoint().field, UNKNOWN())

    def test_recursion(self):
        class A(Observable):
            field: str | UNKNOWN

        class B(Observable):
            a: A = A(field='str')

        class C(Observable):
            b: B

        c = C(b=B())

        self.assertEqual(c.observer_viewpoint().b.a.field, UNKNOWN())

    def test_new_supplies(self):
        event = NewSupplies(targets=[''], supplies=[SuppliesEnum.MEDKIT.value])
        self.assertEqual(event.observer_viewpoint().supplies, [UNKNOWN()])

    def test_dict(self):
        class O(Observable):
            f: int | UNKNOWN = 0

        class W(Observable):
            d: dict[str, O] = {'a': O(f=1), 'b': O(f=2)}

        w = W()
        observed_o = O().observer_viewpoint()
        self.assertEqual(w.observer_viewpoint().d['a'], observed_o)
        self.assertEqual(w.observer_viewpoint().d['b'], observed_o)


def run() -> TestResult:
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestObservable))
    return unittest.TextTestRunner().run(suite)