#coding: utf-8

import os
from datetime import datetime
from unittest import skip

from django.test import Client, SimpleTestCase
from django.conf import settings
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from bson import ObjectId
from django_ses import SESBackend

from .models import User, Category, Products, Orders, ProductsOrdered
from .views import check_token, my_register


class BlogTest(SimpleTestCase):

    def setUp(self):
        email='test_XXX@test.com'
        self.c = Client()
        self.user = User().create_user(username=email,
                                    password='123', email=email)

    def tearDown(self):
        self.user.delete()
        pass

    @skip("Don't want test")
    def test_view_post_image(self):
        """
        Test post image
        """
        asset = os.path.join(settings.BASE_DIR, 'assets', 'press.png')

        with open(asset, 'rb') as fp:
            self.c.post('/post/add/image/', {'title':'Test post by test', 'image': fp})

    def test_put_category_to_user(self):
        """ Test put category or categories for users
        """
        response = self.user.put_category('Startups')
        self.assertEqual(1, response, msg='Test adding category')

    def test_put_category_to_array_as_list(self):
        """ Test put category or categores for users with input
        as list
        """
        response = self.user.put_category(['Startups', 'Lifehacker'])
        self.assertEqual(1, response, msg='Test adding category')

    def test_delete_category(self):
        pass

    def test_view_follower_many_category(self):
        """ Test if can create a new user and to follow many categories
        """
        querystring = {'categories': ['Startups', 'Projects'],
                       'email': self.user.email}
        response = self.c.post(reverse('follower'), querystring)
        # Test response view
        self.assertEqual(response.content, 'true')
        count = User.objects().count()
        categories_persisted = User.objects().skip(count - 1).first().categories
        # Test persistence is right
        self.assertListEqual(querystring['categories'], categories_persisted)

    def test_view_follower_one_category(self):
        """ Test if can create a new user and to follow one category
        """
        querystring = {'categories': ['Startups'],
                       'email': self.user.email}
        response = self.c.post(reverse('follower'), querystring)
        # Test response view
        self.assertEqual(response.content, 'true')
        count = User.objects().count()
        categories_persisted = User.objects().skip(count - 1).first().categories
        # Test persistence is right
        self.assertListEqual(querystring['categories'], categories_persisted)

    def test_create_username_based_objectid(self):
        """ Test if username and emails are different
        """
        self.assertNotEqual(self.user.username, self.user.email)

    def test_clean_username(self):
        self.user.username = 'somebody@example.com'
        pre_username = str(self.user.id)[5:9] + str(self.user.id)[-4:]
        clean_username = self.user.clean_username()
        self.assertEqual(clean_username, pre_username)

    def test_create_user_is_active_false(self):
        self.assertFalse(self.user.is_active)

    def test_check_token(self):
        # Test confirmation page (flow) to check_token
        c = Category(name='Startups', anchor='startups', slug='startups')
        c.save()
        token = self.user.make_token()
        response = self.c.get(reverse('check_token', args=(token,)))
        # test success page
        self.assertEqual(200, response.status_code)
        # test database active account
        user_updated = User.objects.get(token=token)
        # after checking it must change is_active=True
        self.assertTrue(user_updated.is_active)
        # test mistake token
        fail_token = '3qr-07351e93832137ccba45'
        response = self.c.get(reverse('check_token', args=(fail_token,)))
        self.assertEqual(404, response.status_code)
        # test already confirmation
        response = self.c.get(reverse('check_token', args=(token,)))
        self.assertEqual(302, response.status_code)

    def test_make_token(self):
        token = self.user.make_token()
        self.assertEqual(token, default_token_generator.make_token(self.user))

    def test_my_register(self):
        res_1 = self.c.post('/register/', {'username':'mariolago', 'password':'123',
                                  'email':'mariolago@ml.com',
                                  'first_name':'Mario','last_name': 'Lago'})
        self.assertEqual(200, res_1.status_code)
        res_2 = self.c.post('/login/', {'username':'mariolago', 'password':'123'})
        self.assertNotEqual("Invalid login (username or password)", res_2.content)

    def test_my_register_duplicate(self):
        res_1 = self.c.post('/register/', {'username':'mariolago', 'password':'123',
                                  'email':'mariolago@ml.com',
                                  'first_name':'Mario','last_name': 'Lago'})
        self.assertEqual(200, res_1.status_code)
        res_2 = self.c.post('/register/', {'username':'mariolago', 'password':'123',
                                  'email':'mariolago@ml.com',
                                  'first_name':'Mario','last_name': 'Lago'})
        self.assertEqual(200, res_2.status_code)
        self.assertContains(res_2, "username already exists", status_code=200)

    def test_password_reset(self):
        email = 'test_XXX@test.com'
        res = self.c.post('/password_reset/', {'username_or_email': email})
        self.assertContains(res, "recovery password success", status_code=200)

    def test_password_reset_confirm(self):
        email = 'test_XXX@test.com'
        token = self.user.make_token()
        link = reverse('password_reset_confirm', kwargs=dict(token=token,
                                                email=self.user.email))
        link_confirmation = "".join([settings.BASE_URL, link])
        res = self.c.get(link_confirmation)
        self.assertContains(res, "Defina uma nova senha ", status_code=200)


class ServiceTest(SimpleTestCase):

    def setUp(self):
        email='test_XXX@test.com'
        self.c = Client()
        self.user = User().create_user(username=email,
                                    password='123', email=email)

    def tearDown(self):
        self.user.delete()
        pass

    def test_insert_products(self):
        p = Products(sku='34EDFG', description="um tratamento a cada 30 dias com o uso de uma cor ...",
                 fullname="Plano de Assinatura Mensal para 1", short_name="Basic",
                 short_description="1 tratamento",
                 price=6.99, items=[  "Limpeza",  "Conservação (graxa)", "Polimento",  "1 opção de cor"],
                 appointments=1)
        p.save()
        psaved = Products.objects(price=6.99).first()
        self.assertEqual(6.99, psaved.price)

    def test_create_order(self):
        p = Products(sku='34EDFG', description="um tratamento a cada 30 dias com o uso de uma cor ...",
         fullname="Plano de Assinatura Mensal para 1", short_name="Basic",
         short_description="1 tratamento",
         price=6.99, items=["Limpeza",  "Conservação (graxa)", "Polimento", "1 opção de cor"],
         appointments=1)
        p.save()
        p_ord = ProductsOrdered(sku=p.sku, price=p.price, items=p.items,
                        appointmens=p.appointments)
        ord_billing = Orders(product_epoch=p_ord, created_at=datetime.utcnow())
        self.user.orders = [ord_billing,]
        self.user.save()
        u = User.objects.get(email=self.user.email)
        self.assertEqual(u.orders[0].product_epoch, ord_billing.product_epoch)

    def test_get_calendar(self):
        res = self.c.get(reverse('calendar'))
        self.assertEqual(res.status_code, 200)



