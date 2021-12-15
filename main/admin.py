from PIL import Image
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, ModelForm
from django.utils.safestring import mark_safe

from .models import *

class ProductAdminForm(ModelForm):
    #Метод для вывода подсказки какой размерности должна быть картинка
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = \
            '<span style="color:red;">Загружайте изображение с минимальным разрешением {}x{}</span>'.format(
            *Product.MIN_RESOLUTION
        )
    #Метод для отображения фото, так же удаление фото и вывод ошибки если размерность фото не подходит
    def clean_image(self):
        image = self.cleaned_data['image']
        img = Image.open(image)
        min_height, min_width = Product.MIN_RESOLUTION
        max_height, max_width = Product.MAX_RESOLUTION
        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError('Размер изображения не должен превышать 3МБ')
        if img.height < min_height or img.width < min_width:
            raise ValidationError('Разрешение изображения меньше минимального')
        if img.height > max_height or img.width > max_width:
            raise ValidationError('Разрешение изображения больше максимального')
        return image

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm


#Добавление каждой модели в админку
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(CartProduct)
admin.site.register(Customer)
admin.site.register(Order)

