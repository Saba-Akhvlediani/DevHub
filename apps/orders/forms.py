from django import forms
from django.utils.translation import gettext_lazy as _
import re


class CheckoutForm(forms.Form):
    """Checkout form for billing and shipping information"""
    
    # Contact Information
    email = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    # Billing Information
    billing_first_name = forms.CharField(
        label=_('First Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    billing_last_name = forms.CharField(
        label=_('Last Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    billing_company = forms.CharField(
        label=_('Company (Optional)'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company Name'
        })
    )
    
    billing_address = forms.CharField(
        label=_('Address'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Street address, apartment, suite, etc.',
            'rows': 3
        })
    )
    
    billing_city = forms.CharField(
        label=_('City'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    billing_postal_code = forms.CharField(
        label=_('Postal Code'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code'
        })
    )
    
    billing_country = forms.CharField(
        label=_('Country'),
        max_length=100,
        initial='Georgia',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    billing_phone = forms.CharField(
        label=_('Phone Number'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+995 XXX XXX XXX'
        })
    )
    
    # Shipping Option
    different_shipping = forms.BooleanField(
        label=_('Ship to a different address'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'different_shipping'
        })
    )
    
    # Shipping Information (shown conditionally)
    shipping_first_name = forms.CharField(
        label=_('Shipping First Name'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    shipping_last_name = forms.CharField(
        label=_('Shipping Last Name'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    shipping_company = forms.CharField(
        label=_('Shipping Company (Optional)'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company Name'
        })
    )
    
    shipping_address = forms.CharField(
        label=_('Shipping Address'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Street address, apartment, suite, etc.',
            'rows': 3
        })
    )
    
    shipping_city = forms.CharField(
        label=_('Shipping City'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    shipping_postal_code = forms.CharField(
        label=_('Shipping Postal Code'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code'
        })
    )
    
    shipping_country = forms.CharField(
        label=_('Shipping Country'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    shipping_phone = forms.CharField(
        label=_('Shipping Phone Number'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+995 XXX XXX XXX'
        })
    )
    
    # Order Notes
    order_notes = forms.CharField(
        label=_('Order Notes (Optional)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Special instructions for delivery...',
            'rows': 3
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        different_shipping = cleaned_data.get('different_shipping')
        
        # If different shipping is selected, validate shipping fields
        if different_shipping:
            shipping_fields = [
                'shipping_first_name', 'shipping_last_name', 'shipping_address',
                'shipping_city', 'shipping_postal_code', 'shipping_country'
            ]
            
            for field in shipping_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('This field is required when using different shipping address.'))
        
        return cleaned_data


class PaymentForm(forms.Form):
    """Payment form for credit card information"""
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', _('Credit Card')),
        ('debit_card', _('Debit Card')),
    ]
    
    payment_method = forms.ChoiceField(
        label=_('Payment Method'),
        choices=PAYMENT_METHOD_CHOICES,
        initial='credit_card',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    card_name = forms.CharField(
        label=_('Cardholder Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name as shown on card'
        })
    )
    
    card_number = forms.CharField(
        label=_('Card Number'),
        max_length=19,  # 16 digits + 3 spaces
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'id': 'card-number'
        })
    )
    
    expiry_month = forms.ChoiceField(
        label=_('Expiry Month'),
        choices=[(i, f'{i:02d}') for i in range(1, 13)],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    expiry_year = forms.ChoiceField(
        label=_('Expiry Year'),
        choices=[(i, str(i)) for i in range(2024, 2035)],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    cvv = forms.CharField(
        label=_('CVV'),
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '4'
        })
    )
    
    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(' ', '').replace('-', '')
        
        # Basic validation
        if not card_number.isdigit():
            raise forms.ValidationError(_('Card number must contain only digits.'))
        
        if len(card_number) not in [15, 16]:  # Amex is 15, others are 16
            raise forms.ValidationError(_('Card number must be 15 or 16 digits.'))
        
        # Luhn algorithm validation
        if not self.luhn_check(card_number):
            raise forms.ValidationError(_('Invalid card number.'))
        
        # Return the clean card number without spaces
        return card_number
    
    def clean_cvv(self):
        cvv = self.cleaned_data['cvv']
        
        if not cvv.isdigit():
            raise forms.ValidationError(_('CVV must contain only digits.'))
        
        if len(cvv) not in [3, 4]:
            raise forms.ValidationError(_('CVV must be 3 or 4 digits.'))
        
        return cvv
    
    def luhn_check(self, card_number):
        """Luhn algorithm for card number validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10 == 0