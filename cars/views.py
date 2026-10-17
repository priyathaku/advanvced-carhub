from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Car, ContactMessage, TestDriveRequest, Favorite
from .forms import ContactForm, TestDriveForm


def _get_user_or_session_favorites(request):
    """Helper to fetch favorite car IDs for current user or guest session."""
    if request.user.is_authenticated:
        return list(Favorite.objects.filter(user=request.user).values_list('car_id', flat=True))
    if not request.session.session_key:
        request.session.create()
    return list(Favorite.objects.filter(session_key=request.session.session_key).values_list('car_id', flat=True))


def home(request):
    """Homepage with hero, featured cars, quick search, statistics, brand highlights, and test drive CTA."""
    featured_cars = Car.objects.filter(is_featured=True)[:6]
    if not featured_cars.exists():
        featured_cars = Car.objects.all()[:6]

    recent_cars = Car.objects.all().order_by('-created_at')[:8]
    brands = Car.objects.values_list('brand', flat=True).distinct()
    body_types = Car.objects.values_list('body_type', flat=True).distinct()
    favorite_ids = _get_user_or_session_favorites(request)
    test_drive_form = TestDriveForm()

    context = {
        'featured_cars': featured_cars,
        'recent_cars': recent_cars,
        'brands': brands,
        'body_types': body_types,
        'favorite_ids': favorite_ids,
        'total_cars_count': Car.objects.count(),
        'test_drive_form': test_drive_form,
    }
    return render(request, 'home.html', context)


def cars_list(request):
    """Advanced search and filter catalog with sorting options."""
    queryset = Car.objects.all()

    # Filters
    brand = request.GET.get('brand', '').strip()
    model_name = request.GET.get('model', '').strip()
    q = request.GET.get('q', '').strip()
    fuel_type = request.GET.get('fuel_type', '').strip()
    transmission = request.GET.get('transmission', '').strip()
    body_type = request.GET.get('body_type', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    year = request.GET.get('year', '').strip()
    max_mileage = request.GET.get('max_mileage', '').strip()
    sort = request.GET.get('sort', '').strip()

    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(brand__icontains=q) |
            Q(description__icontains=q) |
            Q(engine__icontains=q)
        )

    if brand:
        queryset = queryset.filter(brand__iexact=brand)

    if model_name:
        queryset = queryset.filter(name__icontains=model_name)

    if fuel_type:
        queryset = queryset.filter(fuel_type__iexact=fuel_type)

    if transmission:
        queryset = queryset.filter(transmission__iexact=transmission)

    if body_type:
        queryset = queryset.filter(body_type__iexact=body_type)

    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if year:
        try:
            queryset = queryset.filter(year__gte=int(year))
        except ValueError:
            pass

    if max_mileage:
        try:
            queryset = queryset.filter(mileage__lte=int(max_mileage))
        except ValueError:
            pass

    # Sorting
    if sort == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort == 'newest':
        queryset = queryset.order_by('-year', '-created_at')
    elif sort == 'mileage_asc':
        queryset = queryset.order_by('mileage')
    else:
        queryset = queryset.order_by('-is_featured', '-created_at')

    # Available options for filter panel
    all_brands = Car.objects.values_list('brand', flat=True).distinct().order_by('brand')
    all_body_types = Car.objects.values_list('body_type', flat=True).distinct().order_by('body_type')
    all_fuel_types = Car.objects.values_list('fuel_type', flat=True).distinct().order_by('fuel_type')
    all_transmissions = Car.objects.values_list('transmission', flat=True).distinct().order_by('transmission')
    favorite_ids = _get_user_or_session_favorites(request)

    context = {
        'cars': queryset,
        'results_count': queryset.count(),
        'all_brands': all_brands,
        'all_body_types': all_body_types,
        'all_fuel_types': all_fuel_types,
        'all_transmissions': all_transmissions,
        'favorite_ids': favorite_ids,
        # Pass active filter values back to template
        'selected_brand': brand,
        'selected_model': model_name,
        'selected_fuel': fuel_type,
        'selected_transmission': transmission,
        'selected_body_type': body_type,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'selected_year': year,
        'selected_max_mileage': max_mileage,
        'selected_sort': sort,
        'search_query': q,
    }
    return render(request, 'cars.html', context)


def car_detail(request, pk):
    """Car details page with gallery, specs, test drive booking, favorites, and related cars."""
    car = get_object_or_404(Car, pk=pk)
    related_cars = Car.objects.filter(brand=car.brand).exclude(pk=car.pk)[:3]
    if related_cars.count() < 3:
        fill_cars = Car.objects.exclude(pk=car.pk).exclude(pk__in=related_cars.values_list('pk', flat=True))[:3 - related_cars.count()]
        related_cars = list(related_cars) + list(fill_cars)

    favorite_ids = _get_user_or_session_favorites(request)
    is_favorited = car.id in favorite_ids
    test_drive_form = TestDriveForm(initial={'car': car})

    context = {
        'car': car,
        'related_cars': related_cars,
        'is_favorited': is_favorited,
        'favorite_ids': favorite_ids,
        'test_drive_form': test_drive_form,
    }
    return render(request, 'car_detail.html', context)


def compare_cars(request):
    """Compare up to 3 cars side-by-side with difference highlighting."""
    car_ids = request.GET.getlist('car')
    if not car_ids:
        # Check single param fallback (e.g. ?car1=1&car2=2)
        c1 = request.GET.get('car1')
        c2 = request.GET.get('car2')
        c3 = request.GET.get('car3')
        car_ids = [c for c in [c1, c2, c3] if c]

    # Clean IDs
    valid_ids = []
    for cid in car_ids:
        try:
            valid_ids.append(int(cid))
        except (ValueError, TypeError):
            pass

    selected_cars = list(Car.objects.filter(id__in=valid_ids[:3]))
    all_cars = Car.objects.all().order_by('brand', 'name')
    favorite_ids = _get_user_or_session_favorites(request)

    context = {
        'selected_cars': selected_cars,
        'all_cars': all_cars,
        'favorite_ids': favorite_ids,
        'selected_ids': [c.id for c in selected_cars],
    }
    return render(request, 'compare.html', context)


def favorites_list(request):
    """List of all favorited cars for current user or session."""
    fav_ids = _get_user_or_session_favorites(request)
    favorite_cars = Car.objects.filter(id__in=fav_ids)

    context = {
        'favorite_cars': favorite_cars,
        'favorite_ids': fav_ids,
        'count': favorite_cars.count(),
    }
    return render(request, 'favorites.html', context)


def toggle_favorite(request, car_id):
    """AJAX and redirect endpoint to toggle a car in favorites."""
    car = get_object_or_404(Car, id=car_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json'

    if request.user.is_authenticated:
        fav, created = Favorite.objects.get_or_create(user=request.user, car=car)
        if not created:
            fav.delete()
            favorited = False
        else:
            favorited = True
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        fav, created = Favorite.objects.get_or_create(session_key=session_key, car=car)
        if not created:
            fav.delete()
            favorited = False
        else:
            favorited = True

    total_favs = len(_get_user_or_session_favorites(request))

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'car_id': car.id,
            'favorited': favorited,
            'total_favorites': total_favs,
            'message': f"{car.brand} {car.name} {'added to' if favorited else 'removed from'} your favorites."
        })

    messages.success(request, f"{car.brand} {car.name} {'added to' if favorited else 'removed from'} your favorites.")
    return redirect(request.META.get('HTTP_REFERER', 'favorites'))


def book_test_drive(request):
    """Book Test Drive handling with validation and success message."""
    if request.method == 'POST':
        form = TestDriveForm(request.POST)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json'

        if form.is_valid():
            test_drive = form.save()
            success_msg = "Your test drive request has been submitted successfully. Our VIP Concierge will contact you shortly to confirm your booking."
            
            # Optional email notification
            try:
                send_mail(
                    subject=f"CarHub VIP Test Drive Booking #{test_drive.id}",
                    message=f"New test drive booked for {test_drive.car}:\nName: {test_drive.name}\nEmail: {test_drive.email}\nPhone: {test_drive.phone}\nDate: {test_drive.preferred_date}\nTime: {test_drive.preferred_time}\nNotes: {test_drive.notes}",
                    from_email='concierge@carhub.com',
                    recipient_list=[test_drive.email, 'support@carhub.com'],
                    fail_silently=True,
                )
            except Exception:
                pass

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': success_msg,
                    'booking_id': test_drive.id
                })

            messages.success(request, success_msg)
            return redirect('car_detail', pk=test_drive.car.id)
        else:
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.as_json()
                }, status=400)
            messages.error(request, "Please correct the errors in the test drive form.")
            car_id = request.POST.get('car')
            if car_id:
                return redirect('car_detail', pk=car_id)
            return redirect('home')

    return redirect('home')


def about(request):
    """About CarHub page."""
    total_cars = Car.objects.count()
    brands_count = Car.objects.values('brand').distinct().count()
    context = {
        'total_cars': total_cars,
        'brands_count': brands_count,
    }
    return render(request, 'about.html', context)


def brands_page(request):
    """Dedicated luxury Brands showcase page with model counts and direct catalog filters."""
    distinct_brands = list(Car.objects.values_list('brand', flat=True).distinct().order_by('brand'))
    
    brand_meta = {
        'Porsche': {
            'origin': 'Stuttgart, Germany',
            'tagline': 'Motorsport Heritage & Track Precision',
            'desc': 'Synonymous with racing pedigree, legendary rear-engine dynamics, and timeless silhouette design.'
        },
        'Mercedes-Benz': {
            'origin': 'Affalterbach, Germany',
            'tagline': 'Handcrafted AMG Power & Grand Touring',
            'desc': 'Pioneering automotive luxury, opulent executive appointments, and blistering biturbo V8 performance.'
        },
        'BMW': {
            'origin': 'Munich, Germany',
            'tagline': 'The Ultimate Driving Machine',
            'desc': 'Razor-sharp chassis balance, M xDrive intelligence, and high-revving TwinPower turbocharged powerplants.'
        },
        'Audi': {
            'origin': 'Ingolstadt, Germany',
            'tagline': 'Vorsprung durch Technik & RS Dynamics',
            'desc': 'Quattro all-wheel drive dominance, aerodynamic EV platforms, and cutting-edge digital light optics.'
        },
        'Land Rover': {
            'origin': 'Gaydon, United Kingdom',
            'tagline': 'Peerless All-Terrain Luxury',
            'desc': 'Commanding road presence, bespoke executive rear seating, and unstoppable electronic air suspension.'
        }
    }

    brands_data = []
    for b in distinct_brands:
        cars = Car.objects.filter(brand=b)
        first_car = cars.first()
        min_price = cars.order_by('price').first().formatted_price if cars.exists() else None
        meta = brand_meta.get(b, {
            'origin': 'Global Luxury',
            'tagline': 'Exotic Automotive Engineering',
            'desc': 'High-performance grand touring and uncompromising prestige craftsmanship.'
        })
        brands_data.append({
            'name': b,
            'count': cars.count(),
            'image': first_car.get_image_url() if first_car else '/static/images/car1.png',
            'min_price': min_price,
            'origin': meta['origin'],
            'tagline': meta['tagline'],
            'desc': meta['desc'],
        })

    return render(request, 'brands.html', {
        'brands': brands_data,
        'total_brands_count': len(brands_data),
        'total_fleet_count': Car.objects.count(),
    })


def contact(request):
    """Dealer & contact page with form validation, database storage, and email confirmation."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_msg = form.save()
            try:
                send_mail(
                    subject=f"CarHub VIP Inquiry: {contact_msg.subject}",
                    message=f"Message from {contact_msg.name} ({contact_msg.email}):\n\n{contact_msg.message}",
                    from_email=contact_msg.email,
                    recipient_list=['support@carhub.com'],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, "Your message has been sent successfully! A CarHub luxury specialist will contact you shortly.")
            return render(request, "contact.html", {"form": ContactForm(), "success": True})
        else:
            messages.error(request, "Please correct the highlighted errors below.")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})


# Preserved existing pages
def interior(request):
    return render(request, 'interior.html')


def exterior(request):
    return render(request, 'exterior.html')


def reviews(request):
    return render(request, 'reviews.html')


# Authentication helper views
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Link guest session favorites to this user
                if request.session.session_key:
                    guest_favs = Favorite.objects.filter(session_key=request.session.session_key)
                    for f in guest_favs:
                        if not Favorite.objects.filter(user=user, car=f.car).exists():
                            f.user = user
                            f.session_key = None
                            f.save()
                        else:
                            f.delete()
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next') or 'home'
                return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Link guest session favorites to this user
            if request.session.session_key:
                guest_favs = Favorite.objects.filter(session_key=request.session.session_key)
                for f in guest_favs:
                    if not Favorite.objects.filter(user=user, car=f.car).exists():
                        f.user = user
                        f.session_key = None
                        f.save()
                    else:
                        f.delete()
            messages.success(request, f"Your CarHub VIP account has been created! Welcome, {user.username}.")
            return redirect('home')
        else:
            messages.error(request, "Registration could not be completed. Please check the details entered.")
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out of CarHub.")
    return redirect('home')
