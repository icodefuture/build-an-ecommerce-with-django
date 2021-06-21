from django.utils.text import slugify
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, ProductForm, GalleryForm, CheckoutForm
from .models import Product, Gallery, Order, Cart, CartItem, OrderItem
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail
import stripe
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
stripe.api_key = ''

def index(request):
    products = Product.objects.all()

    return render(request, 'main/pages/home.html', {
        'products': products
    })

@login_required(login_url='/login')
def dashboard(request):
    if request.user.groups.all()[0].name == "seller":
        orders = OrderItem.objects.filter(product__user=request.user)
    else:
        orders = Order.objects.filter(user=request.user)

    return render(request, 'main/dashboard/index.html', {
        'orders': orders
    })

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('main:dashboard'))
            else:
                messages.success(request, 'Username or password is wrong')
                return HttpResponseRedirect(reverse('main:login'))
        
        return render(request, 'main/auth/login.html', {
            'form': form
        })
    else:
        form = LoginForm()
        
        return render(request, 'main/auth/login.html', {
            'form': form
        })

def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('main:home'))

def register_user(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            seller = Group.objects.get(name='buyer')
            user.groups.add(seller)
            login(request, user)
            return HttpResponseRedirect(reverse('main:dashboard'))

        return render(request, 'main/auth/register.html', {
            'form': form
        })
    else:
        form = RegistrationForm()

        return render(request, 'main/auth/register.html', {
            'form': form
        })

def register_merchant(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            seller = Group.objects.get(name='seller')
            user.groups.add(seller)
            login(request, user)
            return HttpResponseRedirect(reverse('main:dashboard'))

        return render(request, 'main/auth/register-merchant.html', {
            'form': form
        })
    else:
        form = RegistrationForm()

        return render(request, 'main/auth/register-merchant.html', {
            'form': form
        })

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES or None)
        if form.is_valid():
            product = form.save(commit=False)
            product.user_id = request.user.id
            product.slug = slugify(product.title)
            product.save()
            messages.success(request, 'Product added!')
            return HttpResponseRedirect(reverse('main:dashboard_products'))
        
        return render(request, 'main/product/create.html', {
            'form': form
        })
    else:
        form = ProductForm()

        return render(request, 'main/product/create.html', {
            'form': form
        })

def product_show(request, slug):
    product = Product.objects.get(slug=slug)

    return render(request, 'main/product/show.html', {
        'product': product
    })

def product_gallery(request, id):
    product = Product.objects.get(pk=id)
    gallery = product.gallery.all()

    if request.method == 'POST':
        form = GalleryForm(request.POST, request.FILES or None)
        if form.is_valid():
            files = request.FILES.getlist('image')
            
            for f in files:
                gallery = Gallery(image=f, product_id=product.id)
                gallery.save()

            messages.success(request, 'Product gallery updated!')
            return HttpResponseRedirect(reverse('main:product_gallery', args=(product.id,)))
        
        return render(request, 'main/product/gallery.html', {
            'product': product,
            'form': form,
            'gallery': gallery
        })
    else:
        form = GalleryForm()

        return render(request, 'main/product/gallery.html', {
            'product': product,
            'form': form,
            'gallery': gallery
        })

def product_gallery_delete(request, id):
    image = Gallery.objects.get(pk=id)
    product = image.product_id
    image.delete()
    messages.success(request, 'Gallery item removed!')
    return HttpResponseRedirect(reverse('main:product_gallery', args=(product,)))

def product_edit(request):
    return HttpResponse('Edit')

def product_delete(request, id):
    product = Product.objects.get(pk=id)
    product.delete()
    messages.success(request, 'Product removed successfully!')
    return HttpResponseRedirect(reverse('main:dashboard'))

def dashboard_products(request):
    products = Product.objects.filter(user_id=request.user)

    return render(request, 'main/dashboard/products.html', {
        'products': products
    })

def dashboard_orders(request):
    orders = Order.objects.get(user_id=request.user)

    return render(request, 'main/dashboard/orders.html', {
        'orders': orders
    })

@login_required(login_url='/login')
def add_cart_item(request):
    if request.method == 'POST':
        product = Product.objects.get(pk=request.POST['product_id'])
        quantity = int(request.POST['quantity'])
        try:
            cart = Cart.objects.get(user=request.user)
            cart.total = cart.total + (product.price * quantity)
            cart.save()
        except Cart.DoesNotExist:
            cart = Cart(user=request.user)
            # cart total
            cart.total = product.price * quantity
            cart.save()
        
        CartItem.objects.create(
            cart=cart,
            product=product, 
            quantity=quantity
        )
        messages.success(request, 'Product added to cart!')
        return HttpResponseRedirect(reverse('main:cart'))

@login_required(login_url='/login')
def cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    return render(request, 'main/pages/cart.html', {
        'cart': cart
    })

@login_required(login_url='/login')
def delete_cart_item(request, id):
    if request.method == 'POST':
        item = CartItem.objects.get(pk=id)
        cart = Cart.objects.get(pk=item.cart.id)
        cart.total = cart.total - (item.product.price * item.quantity)
        cart.save()
        item.delete()
        messages.success(request, 'Product removed from cart!')
        return HttpResponseRedirect(reverse('main:cart'))

@login_required(login_url='/login')
def order(request):
    cart = Cart.objects.get(user=request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.status = 'created'
            order.created_at = datetime.now()
            order.updated_at = datetime.now()
            order.total = cart.total
            order.save()

            # set order items
            for item in cart.cart_item.all():
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            # redirect to checkout
            return HttpResponseRedirect(reverse('main:checkout'))
        
        return render(request, 'main/pages/order.html', {
            'cart': cart,
            'form': form
        })
    else:
        form = CheckoutForm()
        
        return render(request, 'main/pages/order.html', {
            'cart': cart,
            'form': form
        })

@csrf_exempt
@login_required(login_url='/login')
def checkout(request):
    if request.method == 'POST':
        order = Order.objects.get(user=request.user, status='created')
        cart = Cart.objects.get(user=request.user)
        try:
            domain_url = 'http://codersdiaries.pythonanywhere.com'
            session = stripe.checkout.Session.create(
                success_url=domain_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'payment/cancelled',
                payment_method_types=['card'],
                mode='payment',
                line_items=get_order_items(order)
            )
            # update order data
            order.session_id = session.id
            order.payment_id = session.payment_intent
            order.save()
            # remove cart items
            cart.total = 0
            cart.cart_item.all().delete()
            cart.save()

            return JsonResponse({'sessionId': session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return render(request, 'main/pages/checkout.html')

def get_order_items(order):
    items = []
    for item in order.order_item.all():
        items.append({
            'price_data': {
                'currency': 'inr',
                'unit_amount': item.product.price * 100,
                'product_data': {
                    'name': item.product.title
                },
            },
            'quantity': item.quantity,
        })

    return items

def payment_success(request):
    order = Order.objects.get(session_id=request.GET['session_id'])
    pi = stripe.PaymentIntent.retrieve(order.payment_id)

    # verify payment intent
    if pi.amount == pi.amount_received:
        order.status = 'paid'
        order.save()
        send_mail(
            'Order Confirmed', 
            'Hi, your order is confirmed at ecomx. You can get the details in your dashboard!',
            'team@ecomx.com',
            [order.user.email],
            fail_silently=True
        )
        return render(request, 'main/payment/success.html')
    else:
        order.delete()
        return HttpResponseRedirect(reverse('main:payment_cancelled'))

def payment_cancelled(request):
    send_mail(
        'Order Confirmed', 
        'Hi, your order is cancelled due to non payment!',
        request.user.email,
        'team@ecomx.com'
    )
    return render(request, 'main/payment/cancelled.html')