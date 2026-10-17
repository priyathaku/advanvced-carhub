from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cars/', views.cars_list, name='cars_list'),
    path('cars/<int:pk>/', views.car_detail, name='car_detail'),
    path('compare/', views.compare_cars, name='compare_cars'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('favorites/toggle/<int:car_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('book-test-drive/', views.book_test_drive, name='book_test_drive'),
    path('about/', views.about, name='about'),
    path('brands/', views.brands_page, name='brands'),
    path('contact/', views.contact, name='contact'),
    path('interior/', views.interior, name='interior'),
    path('exterior/', views.exterior, name='exterior'),
    path('reviews/', views.reviews, name='reviews'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
]
