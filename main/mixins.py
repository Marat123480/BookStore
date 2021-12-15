from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View
from .models import Category, Product, Cart, Customer

#Класс для возвращения категории и продуктов ней
class CategoryDetailMixin(SingleObjectMixin):

    CATEGORY_MODEL2PRODUCT_MODEL = {
        'product': Product,
    }

    def get_context_data(self, **kwargs):
        if isinstance(self.get_object(), Category):
            model = self.CATEGORY_MODEL2PRODUCT_MODEL['product']
            context = super().get_context_data(**kwargs)
            context['categories'] = Category.objects.get_categories()
            context['category_books'] = model.objects.filter(category=self.get_object())
            return context
        else:
            context = super().get_context_data(**kwargs)
            context['categories'] = Category.objects.get_categories()
            return context

#Класс для возвращения корзины
class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()
            if not customer:
                customer = Customer.objects.create(
                    user=request.user
                )
            cart = Cart.objects.filter(owner=customer, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(id=(Cart.objects.all().count()+1), owner=customer)
        else:
            cart = Cart.objects.filter(for_anonymous_user=True, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(id=(Cart.objects.all().count()+1), for_anonymous_user=True)
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)
