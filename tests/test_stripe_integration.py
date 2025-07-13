import json
import os
from unittest import mock

import pytest
import stripe
from django.test import Client
from django.urls import reverse
from payments.services import create_payment_intent

pytestmark = pytest.mark.django_db

@pytest.fixture(autouse=True)
def stripe_env(monkeypatch):
    monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_123')
    monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test_123')

@mock.patch('payments.services.stripe.PaymentIntent.create')
def test_create_payment_intent_payment_intent(mock_create):
    # Simuler la réponse Stripe
    mock_create.return_value = mock.Mock(client_secret='secret_123', id='pi_123')
    
    res = create_payment_intent(12.34, 'REF1', metadata={'foo':'bar'})
    assert res['client_secret'] == 'secret_123'
    assert res['id'] == 'pi_123'
    mock_create.assert_called_once()

@mock.patch('payments.services.stripe.checkout.Session.create')
def test_create_payment_intent_checkout_session(mock_session):
    session_mock = mock.Mock(url='https://checkout', id='cs_123')
    mock_session.return_value = session_mock
    res = create_payment_intent(5.0, 'REF2', return_url='https://site/success')
    assert res['checkout_url'] == 'https://checkout'
    assert res['id'] == 'cs_123'
    mock_session.assert_called_once()

@mock.patch('payments.webhooks.stripe.Webhook.construct_event')
def test_handle_payment_notification_success(mock_construct):
    client = Client()
    payload = {'type':'payment_intent.succeeded', 'data':{'object': {'metadata': {'reference':'REF1'}}}}
    mock_construct.return_value = payload
    response = client.post(reverse('stripe_webhook'), data=json.dumps(payload), content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
    assert response.status_code == 200

