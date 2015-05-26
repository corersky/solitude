from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase

from braintree.error_result import ErrorResult
from nose.tools import eq_
from rest_framework.serializers import Serializer

from lib.brains import serializers
from lib.brains.errors import BraintreeFormatter, BraintreeResultError


class Fake(Serializer):
    pass


class FakeObject(object):
    id = 'Fake'


class FakeBraintree(serializers.Braintree):
    fields = ['id']


class TestSerializer(TestCase):

    def test_namespaced(self):
        eq_(serializers.Namespaced(Fake(), Fake()).data,
            {'mozilla': {}, 'braintree': {}})

    def test_braintree(self):
        eq_(FakeBraintree(FakeObject()).data,
            {'id': 'Fake'})


def ValidationError():
    # Cribbed from braintree_python source: http://bit.ly/1ICYL1M
    errors = {
        'scope': {
            'errors': [
                {'code': 123, 'message': 'message', 'attribute': 'thing'},
                {'code': 456, 'message': 'else', 'attribute': 'thing'}
            ]
        }
    }
    return ErrorResult(
        'gateway',
        {'errors': errors, 'params': 'params', 'message': 'brief description'}
    )


def CreditCardError():
    return ErrorResult(
        'gateway', {
            'errors': {},
            'message': 'Do Not Honor',
            'verification': {
                'processor_response_code': 'processor-code',
                'processor_response_text': 'processor response',
            },
        }
    )


class TestBraintreeError(TestCase):

    def setUp(self):
        self.brain = BraintreeFormatter

    def test_validation_errors(self):
        eq_(self.brain(BraintreeResultError(ValidationError())).format(),
            {'braintree': {
                'thing': [
                    {'message': 'message', 'code': 123},
                    {'message': 'else', 'code': 456}
                ]}
             })

    def test_credit_card_error(self):
        eq_(self.brain(BraintreeResultError(CreditCardError())).format(), {
            'braintree': {
                NON_FIELD_ERRORS: [{
                    'message': 'processor response',
                    'code': 'cc-processor-code',
                }]
            }
        })
