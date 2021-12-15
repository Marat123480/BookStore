from django.urls import path
from .views import (
    BaseView,
    BookDetailView,
    CategoryDetailView,
    CartView,
    AddToCartView,
    DeleteFromCartView,
    ChangeQTYView,
    CheckoutView,
    MakeOrderView,
    ContactView,
    SendMessageView
)
from . import views
urlpatterns = [
    path('', BaseView.as_view(), name='main'),
    path('auth/', views.authPage, name='auth'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('books/<str:ct_model>/<str:slug>/', BookDetailView.as_view(), name='book_detail'),
    path('genre/<str:slug>/', CategoryDetailView.as_view(), name='genre_detail'),
    path('basket/', CartView.as_view(), name='basket'),
    path('add-to-basket/<str:ct_model>/<str:slug>/', AddToCartView.as_view(), name="add_to_basket"),
    path('remove-from-basket/<str:ct_model>/<str:slug>/', DeleteFromCartView.as_view(), name="delete_from_basket"),
    path('change-qty/<str:ct_model>/<str:slug>/', ChangeQTYView.as_view(), name="change_qty"),
    path('checkout/', CheckoutView.as_view(), name="checkout"),
    path('make-order/', MakeOrderView.as_view(), name="make_order"),
    path('contact/', ContactView.as_view(), name="contact"),
    path('send-message/', SendMessageView.as_view(), name="send_message")
]
