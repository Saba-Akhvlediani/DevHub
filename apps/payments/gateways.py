# apps/payments/gateways.py
import requests
import json
import hmac
import hashlib
import uuid
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_payment(self, order, amount, currency='GEL'):
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id, signature_data):
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id, amount=None):
        pass


class BOGPaymentGateway(PaymentGateway):
    """Bank of Georgia payment gateway integration"""
    
    def __init__(self):
        self.client_id = settings.BOG_CLIENT_ID
        self.client_secret = settings.BOG_CLIENT_SECRET
        self.sandbox_mode = getattr(settings, 'BOG_SANDBOX_MODE', True)
        
        if self.sandbox_mode:
            self.base_url = 'https://api.bog.ge/payments/sandbox'
        else:
            self.base_url = 'https://api.bog.ge/payments'
    
    def get_access_token(self):
        """Get OAuth access token from BOG"""
        url = f"{self.base_url}/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        return response.json()['access_token']
    
    def create_payment(self, order, amount, currency='GEL'):
        """Create payment order with BOG"""
        access_token = self.get_access_token()
        
        payment_data = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': currency,
                    'value': str(amount)
                },
                'description': f'Order #{order.order_number}',
                'custom_id': str(order.id),
                'invoice_id': order.order_number
            }],
            'application_context': {
                'return_url': f"{settings.SITE_URL}/orders/payment-success/{order.id}/",
                'cancel_url': f"{settings.SITE_URL}/orders/payment-failed/{order.id}/",
                'brand_name': 'Georgian Equipment',
                'locale': 'ka-GE',
                'user_action': 'PAY_NOW'
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/v1/checkout/orders"
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        
        return response.json()
    
    def verify_payment(self, payment_id, signature_data):
        """Verify payment status with BOG"""
        access_token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/v1/checkout/orders/{payment_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        payment_info = response.json()
        return payment_info.get('status') == 'COMPLETED'
    
    def refund_payment(self, payment_id, amount=None):
        """Process refund through BOG"""
        access_token = self.get_access_token()
        
        refund_data = {}
        if amount:
            refund_data['amount'] = {
                'value': str(amount),
                'currency_code': 'GEL'
            }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/v1/payments/captures/{payment_id}/refund"
        response = requests.post(url, headers=headers, json=refund_data)
        response.raise_for_status()
        
        return response.json()


class TBCPaymentGateway(PaymentGateway):
    """TBC Bank payment gateway integration"""
    
    def __init__(self):
        self.client_id = settings.TBC_CLIENT_ID
        self.client_secret = settings.TBC_CLIENT_SECRET
        self.sandbox_mode = getattr(settings, 'TBC_SANDBOX_MODE', True)
        
        if self.sandbox_mode:
            self.base_url = 'https://api.tbcbank.ge/v1/sandbox'
        else:
            self.base_url = 'https://api.tbcbank.ge/v1'
    
    def create_payment(self, order, amount, currency='GEL'):
        """Create payment with TBC"""
        payment_data = {
            'amount': float(amount),
            'currency': currency,
            'description': f'Order #{order.order_number}',
            'order_id': str(order.id),
            'return_url': f"{settings.SITE_URL}/orders/payment-success/{order.id}/",
            'cancel_url': f"{settings.SITE_URL}/orders/payment-failed/{order.id}/",
            'language': 'ka'
        }
        
        # Create signature
        signature = self._create_signature(payment_data)
        payment_data['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client_id}'
        }
        
        url = f"{self.base_url}/payments"
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        
        return response.json()
    
    def verify_payment(self, payment_id, signature_data):
        """Verify payment with TBC"""
        headers = {
            'Authorization': f'Bearer {self.client_id}'
        }
        
        url = f"{self.base_url}/payments/{payment_id}/status"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        payment_info = response.json()
        
        # Verify signature
        expected_signature = self._create_signature(payment_info)
        if not hmac.compare_digest(expected_signature, signature_data.get('signature', '')):
            return False
        
        return payment_info.get('status') == 'SUCCESS'
    
    def refund_payment(self, payment_id, amount=None):
        """Process refund with TBC"""
        refund_data = {
            'payment_id': payment_id,
            'reason': 'Customer request'
        }
        
        if amount:
            refund_data['amount'] = float(amount)
        
        signature = self._create_signature(refund_data)
        refund_data['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client_id}'
        }
        
        url = f"{self.base_url}/refunds"
        response = requests.post(url, headers=headers, json=refund_data)
        response.raise_for_status()
        
        return response.json()
    
    def _create_signature(self, data):
        """Create HMAC signature for TBC API"""
        # Sort data keys and create string
        sorted_keys = sorted(data.keys())
        signature_string = '&'.join([f"{key}={data[key]}" for key in sorted_keys])
        
        # Create HMAC signature
        signature = hmac.new(
            self.client_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature


# Payment manager to handle multiple gateways
class PaymentManager:
    """Manages multiple payment gateways"""
    
    def __init__(self):
        self.gateways = {
            'bog': BOGPaymentGateway(),
            'tbc': TBCPaymentGateway(),
        }
    
    def get_gateway(self, gateway_name):
        """Get specific payment gateway"""
        return self.gateways.get(gateway_name)
    
    def create_payment(self, gateway_name, order, amount, currency='GEL'):
        """Create payment using specified gateway"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            raise ValueError(f"Unknown payment gateway: {gateway_name}")
        
        return gateway.create_payment(order, amount, currency)
    
    def verify_payment(self, gateway_name, payment_id, signature_data):
        """Verify payment using specified gateway"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            raise ValueError(f"Unknown payment gateway: {gateway_name}")
        
        return gateway.verify_payment(payment_id, signature_data)