import os

import requests
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()
endpoint ='https://preprod.vanilla-pay.net'
# endpoint ='https://api.vanilla-pay.net'
def generate_token():
    """Appelle l'API Vanilla Pay pour générer un token."""
    url = f"{endpoint}/webpayment/token"
    headers = {
        "Accept": "*/*",
        "Client-Id": os.getenv("CLIENT_ID"),
        "Client-Secret": os.getenv("CLIENT_SECRET"),
        "VPI-Version": "2023-01-12",
    }
    response = requests.get(url, headers=headers)
    return response.json()



def initiate_payment(payload):
    """Appelle l'API Vanilla Pay pour initier un paiement."""
    url = f"{endpoint}/webpayment/initiate"
    
    # Générer le token
    token_data = generate_token()
    
    # Vérifier si la génération du token a échoué
    if isinstance(token_data, dict) and "error" in token_data:
        return {'error': 'Failed to initiate payment', 'details': token_data['error']}

    # Récupérer le token
    data = token_data.get("Data")
    token = data.get("Token")
    
    if not token:
        return {'error': 'Token not found in response'}

    headers = {
        "Accept": "*/*",
        "Authorization": f"{token}",
        "VPI-Version": "2023-01-12",
    }

    try:
        # Faire la requête POST à l'API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 

        # Retourner la réponse JSON de l'API
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        return {'error': 'HTTP error occurred', 'details': str(http_err)}
    except requests.exceptions.RequestException as req_err:
        return {'error': 'Request exception occurred', 'details': str(req_err)}
    except Exception as e:
        return {'error': 'An unexpected error occurred', 'details': str(e)}
