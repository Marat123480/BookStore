import datetime
from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.views.generic import DetailView, View
from django.contrib import messages
from .models import Product, Category, LatestProducts, Customer, Cart, CartProduct
from .mixins import CategoryDetailMixin, CartMixin
from django.http import HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from .forms import OrderForm, OrderFormNotAuth, ContactForm
from django.contrib import messages
from .utils import recalc_cart
from django.db import transaction
from django.core.mail import send_mail

#Метод для авторизации
def loginPage(request):

    # is_authenticated проверка на авторизованного ли пользователя
    if request.user.is_authenticated:
        return redirect('/')
    else:
        #Авторизация пользователя
        form = CreateUserForm()
        cart = Cart.objects.filter(for_anonymous_user=True).first()
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password1')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
        context = {'form': form, 'cart': cart}
        return render(request, 'login.html', context)

#Метод для выхода из аккаунта
def logoutUser(request):

    logout(request)
    return redirect('login')

#Метод для регистрации
def authPage(request):

    # is_authenticated проверка на авторизованного ли пользователя
    if request.user.is_authenticated:
        return redirect('/')
    else:
        form = CreateUserForm()
        cart = Cart.objects.filter(for_anonymous_user=True).first()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                return redirect('/login')
        context = {'form': form, 'cart': cart}
        return render(request, 'auth.html', context)

class BaseView(CartMixin, View):
    #Метод get возвращает на главную страницу продукты, категории и корзину
    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories()
        products = LatestProducts.objects.get_products_for_main('product')
        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'index.html', context)

class BookDetailView(CartMixin, CategoryDetailMixin, DetailView):
    #Это список с ключем и значением
    CT_MODEL_MODEL_CLASS = {
        'product': Product,
    }
    #Метод для возвращения продуктов
    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)

    # model = Product
    # queryset =
    context_object_name = 'book'
    template_name = 'book_detail.html'
    slug_url_kwarg = 'slug'

    #Метод который возвращает продукты, корзину
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(category=context['book'].category).exclude(title=context['book'].title).all().order_by('?')[:4]
        context['ct_model'] = self.model._meta.model_name
        context['cart'] = self.cart
        return context


class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'genre'
    template_name = 'genre_detail.html'
    slug_url_kwarg = 'slug'
    #Метод который возвращает продукты, корзину и категорию
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context

class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories()
        context = {
            'cart': self.cart,
            'categories': categories,
        }
        return render(request, 'basket.html', context)

class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, book_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=book_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )

        if created:
            self.cart.products.add(cart_product)
        else:
            cart_product.qty += 1
            cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "You added book successfully")
        return HttpResponseRedirect('/basket/')


class DeleteFromCartView(CartMixin):

    def get(self, request, *args, **kwargs):
        ct_model, book_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=book_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "You deleted book successfully")
        return HttpResponseRedirect('/basket/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        ct_model, book_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=book_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        qty = int(request.POST.get('qty'))
        #Проверка на количество товара, чтобы человек не мог купить больше книг чем у нас имеется
        if(qty<=product.quantity):
            cart_product.qty = qty
            cart_product.save()
            recalc_cart(self.cart)
            messages.add_message(request, messages.INFO, "You changed the number of books successfully")
        else:
            messages.add_message(request, messages.ERROR, "You can't order books more than books count")
        return HttpResponseRedirect('/basket/')

class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories()
        if request.user.is_authenticated:
            form = OrderFormNotAuth(request.POST or None)
        else:
            form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form
        }
        return render(request, 'checkout.html', context)
    
class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            form = OrderFormNotAuth(request.POST or None)
        else:
            form = OrderForm(request.POST or None)
        customer = self.cart.owner
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            if request.user.is_authenticated:
                new_order.first_name = request.user.first_name
                new_order.last_name = request.user.last_name
            else:
                new_order.first_name = form.cleaned_data['first_name']
                new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_date = form.cleaned_data['order_date']
            # Проверка не выбрал ли человек дату позднее сегодняшней
            if(new_order.order_date < datetime.date.today() ):
                # Переадресация на страницу подтверждения заказа
                return HttpResponseRedirect('/checkout/')
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            recalc_cart(self.cart)
            new_order.cart = self.cart
            new_order.save()
            if request.user.is_authenticated:
                customer.orders.add(new_order)
            else:
                cart = Cart.objects.filter(for_anonymous_user=True).first()
                recalc_cart(cart)
            messages.add_message(request, messages.INFO, "Спасибо за заказ менеджер с вами свяжется")
            message = ' Вы оформили заказ на нашем сайте, заказ приедет к вам ' + str(new_order.order_date)
            send_mail(
                ' Вы оформили заказ ',
                message,
                'amantaymarat033@gmail.com',
                [new_order.address]
            )
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')

class ContactView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories()
        form = ContactForm(request.POST or None)
        context = {
            'cart': self.cart,
            'form': form
        }
        return render(request, 'contact.html', context)

class SendMessageView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST or None)
        print("=====================")
        print(form)
        name = form.cleaned_data['name']
        message = form.cleaned_data['comment']
        address = form.cleaned_data['address']
        if form.is_valid():
            message = 'Пользователь ' + name + ' оставил заявку с просьбой связаться с ним. ' + \
                      ' Сообщение содержит в себе: ' + message + '. Почта пользователя: ' + \
                      address
            send_mail(
                ' Форма контакты заполнена ',
                message,
                'amantaymarat033@gmail.com',
                ['amantaymarat033@gmail.com']
            )
            return HttpResponseRedirect('/contact')
        return HttpResponseRedirect('/contact/')