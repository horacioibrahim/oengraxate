#coding: utf-8

import sys
import datetime
import pymongo
import doctest
from json import loads, dumps
from random import randint

# Django Framework
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.template import loader, Context

# MongoEngine
from mongoengine.django.shortcuts import get_document_or_404
from mongoengine.document import NotUniqueError

# App modules
from . import models, forms, postDAO
from .utils import do_syntax_html
from tasks.tasks import task_send_simple_email, task_send_mail_text_and_html


# Setup to connect server.
# workaround MongoEngine and use pymongo (directly)
db_name = '%s' % (settings.MONGO_DATABASE_NAME)
connection_string = "mongodb://localhost"
connection = pymongo.MongoClient(connection_string)
database = connection[db_name]
collection_post = postDAO.PostDAO(database)


def password_reset(request):
    """ Begin the process to restart password
    """

    if request.method == "POST":
        form = forms.PasswordResetForm(request.POST,)

        if form.is_valid():
            form.save()
            # success request for reset
            return render(request, "password_reset_done.html")

    else:
        form = forms.PasswordResetForm()

    return render(request, "password_reset.html", dict(form=form))

def password_reset_confirm(request, token, email):
    """ Receives typed data by user for remake password
    """
    user = get_document_or_404(models.User, email=email)

    if default_token_generator.check_token(user, token):
        request.session['email'] = email
        return password_reset_done(request) # success token. to open fields for news passwords

    return render(request, "password_reset_fail.html")

def password_reset_done(request):
    """ Make new password to user by email
    """
    if request.method == "POST":
        form = forms.PasswordConfirm(request.POST, )
        if form.is_valid():
            new_password = form.cleaned_data["new_password2"]
            email = request.session.get('email', False)
            user = get_document_or_404(models.User, email=email)
            user.set_password(new_password)
            user.save()

            auth_user = authenticate(username=user.username, password=new_password)
            if auth_user is not None:
                if auth_user.is_active:
                    login(request, auth_user)
                    return redirect(reverse("dashboard"))
                else:
                    pass # account disabled
            else:
                return HttpResponse('Invalid login (username or password)')

    else:
        form = forms.PasswordConfirm()

    return render(request, "password_reset_form.html", dict(form=form))

def index(request):
    today = datetime.datetime.now()
    all_categories = models.Category.objects()
    categories = all_categories(is_main=True)[0:5]
    why_category = all_categories(anchor="why")[0]
    posts = models.Post.objects(published=True,
                    categories=why_category).order_by('created_at').limit(3) # TODO index sort

    if request.method == 'POST':
        orig_terms = None
        try:
            terms = request.POST['terms']
            orig_terms = terms
            terms = terms.split(" ")
        except:
            terms = None

        results_all = collection_post.search_text(terms=terms)

        if terms:
            ts = results_all['stats']['timeMicros'] / 100000.0
            results_all['stats']['timeMicros'] = round(ts, 2)
            return render(request, 'search.html', {'results_all': results_all,
                                                   'posts': results_all[
                                                       'results'],
                                                   'stats': results_all[
                                                       'stats'],
                                                   'terms': orig_terms,
            }
            )

    return render(request, 'index.html',
                  {'categories': categories, 'posts': posts})

def my_register(request):
    """ Creates a new user for services
    """
    was_created = False

    if request.method == "POST":
        form = forms.FormRegister(request.POST,)
        if form.is_valid():
            was_created = form.save()

        if not was_created:
            return render(request, "register_unsuccess.html")
        else:
            return render(request, "register_success.html", dict(form=form))


    else:
        form = forms.FormRegister()

    return render(request, "register.html", dict(form=form))


def my_login(request):
    if request.user.is_authenticated():
        return redirect(reverse("post_add"))

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(reverse("post_add"))
            else:
                pass # account disabled
        else:
            return HttpResponse('Invalid login (username or password)')

    else:
        pass

    return render(request, 'login.html')


def my_logout(request):
    logout(request)
    return redirect(reverse('homepage'))

def follower(request):
    """ Method to save followers of blog. It receives selected categories by POST
    and put categories in user profile (a mongoengine User subclass).
    Return True in case success rather False.
    """
    response = False
    if request.method == "POST":
        categories = request.POST.getlist('categories', None)
        if not categories:
            categories = request.POST.getlist('categories[]', None) # mysterious[]<-
        email = request.POST['email']
        u = models.User()

        try:
            new_u = u.create_user(username=email, email=email, password=None)
            new_u.put_category(categories)
            response = True
        except NotUniqueError:
            response = False
        except:
            raise

        if response:
            token = new_u.make_token()
            link = reverse('check_token', args=(token,))
            link_cancel = reverse('cancel_subscribe', args=(token,))
            link_confirmation = "".join([settings.BASE_URL, link])
            link_cancel_subscribe = "".join([settings.BASE_URL, link_cancel])

            context = dict(link_confirmation=link_confirmation,
                           link_cancel_subscribe=link_cancel_subscribe )
            task_id = task_send_mail_text_and_html.\
                delay('Obrigado pelo seu interesse no OEngraxate.com!',
                              'mail/subscribe', context, [new_u.email,],
                              'horacioibrahim@gmail.com') #TODO change sender

    else:
        return redirect(reverse('homepage'))

    return HttpResponse(dumps(response), content_type=("text", "javascript"))


def category_posts(request, category_anchor):
    """
    The below anchor of Category can contain: #anchor or page (domain/page).

    NOTE(DATABASE): We don't interested to use Index to anchor field
    because Category collection is very small the performance result is no
    significant
    """
    is_container = False
    anchor_exists = get_document_or_404(models.Category,
                                        anchor__contains=category_anchor.lower())

    today = datetime.datetime.now()
    # TODO index sort (order_by)
    posts = models.Post.objects(categories=anchor_exists, published=True,
                                created_at__lte=today).order_by('-created_at')

    try:
        is_container = anchor_exists.is_container
    except AttributeError:
           pass

    if is_container:
        posts = posts.first()
        return post_view(request, posts.slug)

    return render_to_response('posts_by_category.html',
                              {'posts': posts, 'category': anchor_exists})


def post_view(request, slug_title):
    """
    Return a post page (tpl: pages.html)
    """
    slug_title = slug_title.lower()
    post = get_document_or_404(models.Post, published=True, slug=slug_title)

    return render_to_response('pages.html', {'post': post})


@login_required
def post_delete(request, oid):
    """
    Delete documents
    """
    if request.user.is_superuser:
        post = get_document_or_404(models.Post, id=oid)
        post.delete()

    return redirect(reverse('post_add'))


@login_required
def post_add(request):
    """
    The hub of posts types. "Flat is better than nested."
    """
    form = None
    posts = models.Post.objects().order_by('-update_at') # unlimited for instance

    if request.method == 'POST':
        # check what type of post: Text, Image, Podcast, Url
        query_dict = request.POST

        try:
            type_post = query_dict['type_post']
        except:
            type_post = None

        if type_post is not None:
            # Call the type post method
            if type_post == 'TextPost':
                return post_text(request, posts=posts)

            if type_post == 'ImagePost':
                return post_image(request, posts=posts)
        else:
            # TODO: if post not selected
            messages.info(request, u'Nenhum post selecionado!')

    else:
        #TODO: remove forms here.
        form = forms.UploadImageForm()

    return render(request, 'to_post.html', {'form': form, 'posts': posts})


def post_image(request, posts=None):
    """
    Post like Image (rather than Text, Podcast, Link etc)
    """
    form = forms.UploadImageForm(request.POST, request.FILES, )

    if form.is_valid():
        # Save image in MEDIA_ROOT and PATH in model
        post_image = models.ImagePost()
        post_image.title = form.cleaned_data['title']
        post_image.create(request.FILES['image'])
    else:
        raise TypeError(form.errors)

    return render(request, 'to_post.html', {'form': form, 'posts': posts})


def post_text(request, posts=None):
    """
    Post like Text (rather than Image, Podcast, Link etc)
    """
    form = forms.TextContentForm(request.POST, )

    if form.is_valid():
        # Save image in MEDIA_ROOT and PATH in model

        # if exists oid make update. instance with id arg
        oid = form.cleaned_data['oid']
        try:
            # Get the object otherwise create one.
            # you can to use models.MODEL(id='id') will updated BUT (It's BAD)
            # But you can not handling an previous existent object
            # like overwriting save method in models.
            # The best way is get object like instance of existent document:
            post = models.TextPost.objects.get(id=oid) # (It GOOD)
        except:
            post = models.TextPost()

        # Default fields
        post.title = form.cleaned_data['title']
        post.subtitle = form.cleaned_data['subtitle']
        category = form.cleaned_data['categories']
        post.categories = models.Category.objects(pk=category) # category
        tags = form.cleaned_data['tags']
        tags = tags.replace(" ", "")
        tags = tags.split(',')
        post.tags = tags # array
        post.priority_show = form.cleaned_data['priority_show']
        post.published = True if form.cleaned_data['published'] == 1 else False
        # TextPost fields
        content = form.cleaned_data['content']
        post.content = do_syntax_html(content)

        # Optional: schedule a post
        try:
            reschedule = request.POST['reschedule']
        except:
            reschedule = None

        reschedule_check = len(reschedule)

        if reschedule_check > 1:
            res_date = reschedule.split("/")

            if len(res_date) == 3:
                # parse to integer the split array (res_date) with [dd, mm, yy]
                day, month, year = int(res_date[0]), int(res_date[1]), int(
                    res_date[2])
                res_date = datetime.datetime(year, month, day,
                                             12) # 12h because timezone
                post.created_at = res_date
            else:
                messages.warning(request,
                                 u'Wrong with date in reschedule field. Use d,m,y')

        # Optional remake slug
        try:
            remake_slug = request.POST["remake_slug"]
        except:
            remake_slug = None

        if remake_slug is not None:
            post.slug = None

        post.save()

    else:
        raise TypeError(form.errors) # Debug

    return render(request, 'to_post.html', {'form': form, 'posts': posts})

def cancel_subscribe(request, token):
    user_by_token = get_document_or_404(models.User, token=token)
    email = user_by_token.email
    user_by_token.remove()

    return render(request, 'cancel_subscribe.html', dict(email=email))

def check_token(request, token):
    """Confirm user by token sent by email"""
    categories = models.Category.objects()
    user_by_token = get_document_or_404(models.User, token=token)
    if user_by_token.is_active:
        user_categories = user_by_token.categories
        if len(user_categories) > 0:
            end = len(user_categories) - 1
            aleatory = randint(0, end)
            return redirect(reverse('category_posts', args=(user_by_token.categories[aleatory].lower(),)))
        else:
            end = len(categories) - 1
            aleatory = randint(0, end)
            return redirect(reverse('category_posts', args=(categories[aleatory].slug,)))

    user_by_token.is_active = True

    try:
        user_by_token.save()
        confirmed_db = True
    except:
        raise

    # TODO: Check token with mail models
    if confirmed_db:
        body = '''
        Obrigado pela confirmação!

        Minha missão nesse projeto é influenciar positivamente a vida das pessoas
        que se relacionam comigo direta ou indiretamente nos tornando, reciprocamente,
        ainda melhores.

        # Saiba mais sobre o projeto hipy.
        http://hipy.co/post/as-metas-e-objetivos-do-hipy/

        Deixo um sincero abraço e desejo-lhe liberdade de conhecimento!

        Horacio Ibrahim
        hipy.co
        '''
        task_id = task_send_simple_email.delay('Obrigado pela confirmação - hipy', body,
                          [user_by_token.email])

    return render(request, 'check_token.html',
                  {'email': user_by_token.email, 'categories':categories})

# services scope

@login_required
def dashboard(request):
    """ Shows dashboards page with many functionality for users staff, superuser
    and common users (consumers).
    """
    pagename = 'home'

    return render(request, "services/home.html", dict(pagename=pagename))

def checkout(request, sku=None):
    """ Returns the details of product selected in catalog. It's the last step
      before payment
    """
    product = None

    if request.method == "POST":
        # TODO: save info sku in session
        sku = request.POST['sku']
        request.session['sku'] = sku
        return redirect(reverse('payment'))

    else:
        if sku:
            product = get_document_or_404(models.Products, sku=sku)

    # TODO: multiple products
    checkout_data = {"total": product.price}

    return render(request, "services/checkout.html",
                  dict(product=product, checkout=checkout_data))

def payment(request):
    """
    Receives data by user to order
    """
    sku = request.session.get('sku', None)
    product = get_document_or_404(models.Products, sku=sku)

    if request.method == "POST":
        form = forms.PaymentCardForm(request.POST,)
        if form.is_valid():
            pass
    else:
        form = forms.PaymentCardForm()

    return render(request, "services/payment.html",
                  dict(form=form, product=product))

def profile(request):
    """ Returns the details of registered users
    """
    pagename = 'profile'
    form = forms.FormRegister()
    return render(request, "services/actions/profile.html",
                  dict(form=form, pagename=pagename))

def calendar(request):
    """ Returns the details of calendar
    """
    pagename = 'calendar'
    return render(request, "services/actions/calendar.html",
                  dict(pagename=pagename))

# AJAX GET and POSTS
def ajax_get_post(request, objid):
    """
    Return JOSN post by _id
    """
    try:
        post = models.Post.objects.get(id=objid)
        output = post.to_json()
    except:
        output = []

    return HttpResponse(output, content_type=("text", "javascript"))


def ajax_search(request, term):
    """
    Receives a list or one term for search
    """
    pass


def get_categories(request):
    """
    Get all categories for user follow it
    """
    # The vex is a plugin to modal dialog. It has many requirements
    # as messages, inputs or buttons attributes. The vex's better
    # is capable of doing faster and easier handles dialog modal rather
    # foundation (zurb).
    # DISCLOSURE: The callback function receive name attribute of inputs
    # if form tags is not exists.
    #
    # e.g:
    # Example 1 - Empty data:
    # <form><input name="name" value="1"></form>
    # callback: function(data) { print data.name } // output Object {}
    #
    # Example 2 - Useful data (without tag <form>):
    # <input name="name" value="1">
    # callback: function(data) { print data.name } // output Object {name: 1}
    #
    # See more Vex: http://github.hubspot.com/vex/api/basic/

    categories = models.Category.objects(is_main=True)
    t = loader.get_template("modal_categories.html")
    c = Context({'categories': categories})

    # Options for Vex.js
    output = {}
    message = u'Marque uma ou mais categorias de interesse:'
    btn_text = {'YES': u'Seguir'}
    options_vex = dict(message=message, btn_text=btn_text, html=t.render(c))

    # Add options of Vex in "queryset" (it's now list)
    output['options_vex'] = options_vex

    return HttpResponse(dumps(output), content_type=("text", "javascript"))

def ajax_get_actions(request, action):
    """
    Returns content for actions of main menu. For example: action='profile' will
    return data of user as first_name, last_name, etc.

    @param action: an action that defines what return. ['profile', 'calendar',
    'messages', 'billing']

    """
    response = None

    if action == 'profile':
        pass

    return HttpResponse(response, content_type=("text", "javascript"))

def services(request):
    raise TypeError(request)