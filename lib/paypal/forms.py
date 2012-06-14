from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django import forms

from lib.buyers.models import Buyer
from lib.sellers.models import Seller
from lib.paypal.constants import PAYPAL_CURRENCIES


class PreapprovalValidation(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    return_url = forms.URLField()
    cancel_url = forms.URLField()
    uuid = forms.ModelChoiceField(queryset=Buyer.objects.all(),
                                  to_field_name='uuid')

    def args(self):
        return [self.cleaned_data.get(k) for k in
                ('start', 'end', 'return_url', 'cancel_url')]


class PayValidation(forms.Form):
    seller = forms.ModelChoiceField(queryset=Seller.objects.all(),
                                    to_field_name='uuid')
    buyer = forms.ModelChoiceField(queryset=Buyer.objects.all(),
                                   to_field_name='uuid', required=False)
    # Note these amounts apply to all currencies.
    amount = forms.DecimalField(min_value=Decimal('0.1'),
                                max_value=Decimal('5000'))
    return_url = forms.URLField()
    cancel_url = forms.URLField()
    ipn_url = forms.URLField()
    currency = forms.ChoiceField(choices=[(c, c) for c in
                                          PAYPAL_CURRENCIES.keys()])
    memo = forms.CharField()

    def clean_seller(self):
        seller = self.cleaned_data['seller']
        self.cleaned_data['seller_email'] = ''
        try:
            self.cleaned_data['seller_email'] = seller.paypal.paypal_id
        except ObjectDoesNotExist:
            pass
        if not self.cleaned_data['seller_email']:
            raise forms.ValidationError('No seller email found.')
        return seller

    def clean_buyer(self):
        buyer = self.cleaned_data['buyer']
        self.cleaned_data['preapproval'] = ''
        try:
            self.cleaned_data['preapproval'] = buyer.paypal.key
        except (AttributeError, ObjectDoesNotExist):
            pass
        return buyer

    def args(self):
        return [self.cleaned_data.get(k) for k in
                ('seller_email', 'amount', 'ipn_url', 'return_url',
                 'cancel_url')]

    def kwargs(self):
        return dict([(k, self.cleaned_data.get(k)) for k in
                     ('currency', 'preapproval', 'memo', 'uuid')])