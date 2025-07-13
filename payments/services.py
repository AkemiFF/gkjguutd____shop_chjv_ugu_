# services.py
import os

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(amount_eur, reference, metadata=None, return_url=None):
    """
    Crée un PaymentIntent Stripe en EUR et renvoie le client_secret.
    - amount_eur: montant en euros (float ou Decimal)
    - reference: identifiant unique de la commande/panier
    - metadata: dict de métadonnées à stocker
    - return_url: URL de redirection après paiement (pour 3DS)
    """
    # Stripe attend le montant en cents
    amount_cents = int(amount_eur * 100)
    params = {
        'amount': amount_cents,
        'currency': 'eur',
        'metadata': {
            'reference': reference,
            **(metadata or {}),
        }
    }
    # Si vous utilisez Stripe Checkout Session
    if return_url:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': f'Order {reference}'},
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=return_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=return_url + '?canceled=true',
            metadata={'reference': reference},
        )
        return {'checkout_url': session.url, 'id': session.id, 'reference': reference}

    # Sinon, PaymentIntent classique
    intent = stripe.PaymentIntent.create(**params)
    return {'client_secret': intent.client_secret, 'id': intent.id}