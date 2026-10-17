from .models import Favorite, Car


def global_carhub_context(request):
    fav_count = 0
    fav_ids = []
    try:
        if request.user.is_authenticated:
            fav_ids = list(Favorite.objects.filter(user=request.user).values_list('car_id', flat=True))
        else:
            if request.session.session_key:
                fav_ids = list(Favorite.objects.filter(session_key=request.session.session_key).values_list('car_id', flat=True))
        fav_count = len(fav_ids)
    except Exception:
        pass

    try:
        quick_brands = list(Car.objects.values_list('brand', flat=True).distinct()[:6])
    except Exception:
        quick_brands = []

    return {
        'nav_favorite_count': fav_count,
        'global_favorite_ids': fav_ids,
        'nav_brands': quick_brands,
    }
