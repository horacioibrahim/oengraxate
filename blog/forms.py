# coding=utf-8

from datetime import date
# Django Framework
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.core.urlresolvers import reverse
from django.conf import settings

# MongoEngine
from mongoengine import NotUniqueError

# App
from .models import Post, User
from tasks.tasks import task_send_mail_text_and_html

class PostForm(forms.Form):
    oid = forms.CharField(required=False)
    title = forms.CharField(Post.title.max_length)
    subtitle = forms.CharField(Post.subtitle.max_length, required=False)
    categories = forms.CharField()
    tags = forms.CharField(required=False)
    priority_show = forms.IntegerField(max_value=3, min_value=1)
    published = forms.IntegerField(required=False)

    # TODO: Criar heranças para uploadimageform e textcontentform


class UploadImageForm(PostForm):
    image = forms.ImageField()

    # Access image as request.FILES['image'] (if the form contain enctype="multipart/form-data")
    # para manipular imagens não vamos precisar usar chunks, pois serão menores que 2.5MB
    # mas nos videos e podcasts pode ser necessário usar chunks para não carregar tudo na memória
    # e sentar o servidor. Ver docs.djangoproject.../file-uploads/


class TextContentForm(PostForm):
    cover = forms.ImageField(required=False)
    content = forms.CharField()


class FormRegister(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput())
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()

    def clean(self):
        cleaned_data = super(FormRegister, self).clean()
        self.username = cleaned_data["username"]
        self.first_name = cleaned_data["first_name"]
        self.last_name = cleaned_data["last_name"]
        self.email = cleaned_data["email"]
        self.password = cleaned_data["password"]
        return cleaned_data

    def save(self, *args, **kwargs):
        user = User(username=self.username, email=self.email,
                    first_name=self.first_name, last_name=self.last_name)
        try:
            user.set_password(self.password)
            user.save()
        except NotUniqueError:
            return False

        return True


class PasswordResetForm(forms.Form):
    error_messages = {
        'unknown': ("Usuário ou e-mail não cadastrado . Você"
                    "tem certeza que está registrado"),
    }
    username_or_email = forms.CharField()


    def clean_username_or_email(self):
        """
        Validates that an active user exists with given email address or username
        """
        user = self.cleaned_data["username_or_email"]

        try:
            if "@" in user:
                self.user_cache = User.objects.get(email__iexact=user)
            else:
                self.user_cache = User.objects.get(username=user)
        except:
            raise forms.ValidationError(self.error_messages['unknown'])

        return user

    def save(self, *args, **kwargs):
        # send mail by tasks
        token = self.user_cache.make_token()
        link = reverse('password_reset_confirm', kwargs=dict(token=token,
                                                email=self.user_cache.email))
        link_confirmation = "".join([settings.BASE_URL, link])

        if self.user_cache.first_name:
            first_name = self.user_cache.first_name
        else:
            first_name = ""
        if self.user_cache.last_name:
            last_name = self.user_cache.last_name
        else:
            last_name = ""

        context = dict(first_name=first_name,
                       last_name=last_name,
                       url_action=link_confirmation)

        task_id = task_send_mail_text_and_html.\
            delay('Recuperação de senha solicitada',
                          'mail/password_reset_done', context, [self.user_cache.email,],
                          'horacioibrahim@gmail.com') #TODO change sender

class PasswordConfirm(forms.Form):
    error_messages = {
        'password_mismatch': (u"As senhas são diferentes. Digite novamente."),
    }
    new_password1 = forms.CharField(widget=forms.PasswordInput())
    new_password2 = forms.CharField(widget=forms.PasswordInput())

    def clean_new_password2(self):
        value = self.cleaned_data['new_password2']

        if self.cleaned_data.get('new_password1') != value:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])

        return value


class PaymentCardForm(forms.Form):
    CHOICE_BRAND = (
        ("visa", "Visa"),
        ("master", "Mastercard" ),
        ("amex", "American Express"),
        ("diners", "Diners"),
    )

    CHOICE_MONTH =(
        ("01", "Jan"),
        ("02", "Fev"),
        ("03", "Mar"),
        ("04", "Abr"),
        ("05", "Mai"),
        ("06", "Jun"),
        ("07", "Jul"),
        ("08", "Ago"),
        ("09", "Set"),
        ("10", "Out"),
        ("11", "Nov"),
        ("12", "Dez"),
    )

    current_year = date.today().year
    choice_year = lambda year: tuple([(y, str(y)) for y in range(year, year + 11)])
    brand = forms.ChoiceField(widget=forms.Select, choices=CHOICE_BRAND,
                              label="Tipo")
    full_name = forms.CharField(widget=forms.TextInput(attrs={"data-iugu": "full_name"}),
                           max_length=80, label="Nome")
    number = forms.CharField(widget=forms.TextInput(attrs={"data-iugu": "number"}),label="Número")
    verification_value  = forms.CharField(widget=forms.TextInput(attrs={"data-iugu":"verification_value"}),
                            label="Código (CVV)")
    dt_expire_month = forms.ChoiceField(widget=forms.Select(attrs={"class":"change_dt"}),
                                        choices=CHOICE_MONTH,
                                        label="Expira mês")
    dt_expire_year = forms.ChoiceField(widget=forms.Select(attrs={"class":"change_dt"}),
                                       choices=choice_year(current_year),
                                       label="Expira Ano")


