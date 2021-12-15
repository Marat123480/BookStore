from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Order, Contact
from django.contrib.auth.models import User

#Класс отвечающий за данные который будет вводить пользователь
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class OrderForm(forms.ModelForm):
    #Метод для изменения типа данных даты(пользователь выбирает ее при оформлении заказа), p.s до этого она записывалась как тект а теперь как дата
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Дата получения заказа'
    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))
    # Класс отвечающий за те данные который должен ввести пользователь когда оформляет заказ если он не авторизован
    class Meta:
        model = Order
        fields = (
            'first_name', 'last_name', 'phone', 'address', 'buying_type', 'order_date', 'comment'
                  )

class OrderFormNotAuth(forms.ModelForm):
    #Метод для изменения типа данных даты(пользователь выбирает ее при оформлении заказа), p.s до этого она записывалась как тект а теперь как дата
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Дата получения заказа'
    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    #Класс отвечающий за те данные который должен ввести пользователь когда оформляет заказ если он авторизован
    class Meta:
        model = Order
        fields = (
            'phone', 'address', 'buying_type', 'order_date', 'comment'
                  )

class ContactForm(forms.ModelForm):
    #Метод для отображения названия колонки на странице контакты
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].label = 'Сообщение'
    #Класс отвечающий за те данные который должен ввести пользователь когда заполняет форму контакты
    class Meta:
        model = Contact
        fields = (
            'name', 'address', 'comment'
                  )
