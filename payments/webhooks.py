import os

import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from orders.models import Order

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@csrf_exempt
def handle_payment_notification(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not endpoint_secret:
        return HttpResponse("Webhook secret not configured", status=500)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Gérer l'événement
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        reference = session['id']
        print(f"Session completed for reference: {reference}")
  

        Order.objects.filter(reference=reference).update(status='pending', is_paid=True)
    elif event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        reference = intent['id']
        print(f"Session completed for reference: {reference}")
        
        Order.objects.filter(reference=reference).update(status='pending', is_paid=True)

    return HttpResponse(status=200)