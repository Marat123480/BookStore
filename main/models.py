from django.db import models
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
# Create your models here.
User = get_user_model()


# Метод для подсчета товаров в категории
def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]

#Метод для получения url для книги
def get_book_url(obj, view_name):

    ct_model = obj.__class__._meta.model_name
    return reverse(view_name, kwargs={'ct_model': ct_model, 'slug': obj.slug})

    #Классы для выбрасывания ошибок
class MinResolutionErrorException(Exception):
    pass
class MaxResolutionErrorException(Exception):
    pass

#Класс с методом который возвращает продукты для главной страницы
class LatestProductsManager:
    @staticmethod
    def get_products_for_main(*args, **kwargs):
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('id')[:4]
            products.extend(model_products)
        return products

#Класс который хранит у себя в обьекте продукты которые возвращаются в LatestProductsManager
class LatestProducts:
    objects = LatestProductsManager()

class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    #Возвращает все категории с подсчетом количества товаров в нем
    def get_categories(self):

        models = get_models_for_count('product')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=c.product__count, image=c.image) for c in qs
        ]
        return data

class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение', default="help")
    objects = CategoryManager()

    #Метод для отображения в админке
    def __str__(self):
        return self.name

    # Метод для получения url для каждой категории
    def get_absolute_url(self):
        return reverse('genre_detail', kwargs={'slug':self.slug})


class Product(models.Model):
    #Глобальные переменные с размерами фото
    MIN_RESOLUTION = (200, 200)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    #Атрибуты в таблице
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Цена")
    author = models.CharField(max_length=255, verbose_name='Автор')
    length = models.PositiveIntegerField(null=True, verbose_name='Количество страниц')
    quantity = models.PositiveIntegerField(null=True, default=0, verbose_name='Количество товара')
    objects = LatestProductsManager()

    #Метод для отображения в базе данных
    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    #Метод для получения ссылки на книгу
    def get_absolute_url(self):
        return get_book_url(self, 'book_detail')

    #Метод для сохранения фотографии с ограничением
    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTION
        max_height, max_width = self.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorException('Разрешение изображения меньше минимального')
        if img.height > max_height or img.width > max_width:
            raise MaxResolutionErrorException('Разрешение изображения больше максимального')
        super().save(*args, **kwargs)

    def get_model_name(self):
        return self.__class__.__name__.lower()

# Busket
class CartProduct(models.Model):
    #Атрибуты для таблицы
    user = models.ForeignKey('Customer', null=True, verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')
    #Метод для отображения в админке
    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.content_object.title)
    #Метод для сохранения финально цены, идет умножение количества товара на цену 1 товара
    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    #Атрибуты в таблице
    owner = models.ForeignKey('Customer', null=True, verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)
    #Метод для отображения в админке
    def __str__(self):
        return str(self.owner)


class Customer(models.Model):
    #Атрибуты в таблице
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Почта', null=True, blank=True)
    orders = models.ManyToManyField('Order', null=True, blank=True, verbose_name='Заказы покупателя', related_name='related_customer')
    #Метод для отображения в админке
    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)


class Order(models.Model):
    #Статусы заказа
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'ready'
    STATUS_COMPLETED = 'completed'
    #Тип заказа
    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'
    #Список статусов заказа
    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )
    #Список типов заказов
    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )
    #Атрибуты в таблице
    customer = models.ForeignKey(Customer,
                                 null=True,
                                 verbose_name='Покупатель',
                                 related_name='related_orders',
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    cart = models.ForeignKey(Cart,
                             verbose_name='Корзина',
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_NEW)
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF)
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_date = models.DateField(verbose_name='Дата получения заказа', default=timezone.now)

    #Метод для отображения в админке
    def __str__(self):
        return str(self.customer)


class Contact(models.Model):
    #Атрибуты
    name = models.CharField(max_length=255, verbose_name='Полное имя')
    address = models.CharField(max_length=255, verbose_name='Почта')
    comment = models.TextField(verbose_name='Сообщение')
