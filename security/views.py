import time

# Create your views here.
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render


def cache_test_view(request):
    """
    Teste le système de cache Redis :
    - Stocke une valeur dans le cache si elle n'existe pas.
    - La récupère et mesure le temps de récupération.
    """
    cache_key = 'test_key'
    cached_value = cache.get(cache_key)
    
    if not cached_value:
        # Si la valeur n'est pas dans le cache, la stocker
        cached_value = {
            'message': 'Ceci est une donnée testée dans le cache.',
            'timestamp': time.time(),
        }
        cache.set(cache_key, cached_value, timeout=60 * 5)  # Cache pendant 5 minutes
        return JsonResponse({
            'status': 'miss',
            'data': cached_value,
            'message': 'Valeur ajoutée au cache.',
        })

    # Si la valeur est trouvée dans le cache
    return JsonResponse({
        'status': 'hit',
        'data': cached_value,
        'message': 'Valeur récupérée depuis le cache.',
    })
