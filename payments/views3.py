import json
import os

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()

def get_token(request):
    url = "https://api.vanilla-pay.net/webpayment/token"
    headers = {
        "Accept": "*/*",
        "Client-Id": os.getenv("CLIENT_ID"),
        "Client-Secret": os.getenv("CLIENT_SECRET"),
        "VPI-Version": "2023-01-12",
    }
    response = requests.get(url, headers=headers)
    return JsonResponse(response.json())
def get_token_one(request):
    url = "https://api.vanilla-pay.net/webpayment/token"
    headers = {
        "Accept": "*/*",
        "Client-Id": os.getenv("CLIENT_ID"),
        "Client-Secret": os.getenv("CLIENT_SECRET"),
        "VPI-Version": "2023-01-12",
    }
    response = requests.get(url, headers=headers)
    return response.json()



@csrf_exempt
def init_payment(request):
    url = "https://api.vanilla-pay.net/webpayment/initiate"

    token_data = get_token_one(request)
    
    if isinstance(token_data, dict) and "error" in token_data:
        return JsonResponse({'error': 'Failed to initiate payment', 'details': token_data['error']}, status=400)


    data = token_data.get("Data")
    token = data.get("Token")
    if token:
        print(token)
    else:
        return JsonResponse({'error': 'Token not found in response'}, status=400)

    headers = {
        "Accept": "*/*",
        "Authorization": f"{token}",
        "VPI-Version": "2023-01-12",
    }
    body = {
        "montant": 58.5,
        "reference": "ABC-1234",
        "panier": "panier123",
        "devise": "Euro",
        "notif_url": "https://shoplg.online/notifications/",
        "redirect_url": "https://shoplg.online/success/",
    }
    response = requests.post(url, headers=headers, json=body)
    return JsonResponse(response.json())
