from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, Order, OrderItem, Category
from django.contrib.auth import authenticate, login, get_user_model, update_session_auth_hash, logout
from .forms import RegisterForm, LoginForm, ProductForm, OrderForm
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
import json

# Create your views here.
User = get_user_model()

def is_staff(user):
    return user.is_staff

@method_decorator(csrf_exempt, name='dispatch')
class ProductListView(View):
    def get(self, request):
        products = Product.objects.all().values()
        return JsonResponse(list(products), safe=False)

    @method_decorator(user_passes_test(is_staff))
    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return JsonResponse(product.serialize(), status=201)
        return JsonResponse(form.errors, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(View):
    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
            return JsonResponse(product.serialize())
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

    @method_decorator(user_passes_test(is_staff))
    def put(self, request, id):
        try:
            product = Product.objects.get(id=id)
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                product = form.save()
                return JsonResponse(product.serialize())
            return JsonResponse(form.errors, status=400)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

    @method_decorator(user_passes_test(is_staff))
    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
            return JsonResponse({'message': 'Product deleted'}, status=204)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class OrderListView(View):
    @method_decorator(login_required)
    def get(self, request):
        orders = Order.objects.filter(user=request.user).values()
        return JsonResponse(list(orders), safe=False)

    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            user = request.user
            total_price = data.get('total_price')
            status = data.get('status', 'Pending')
            order = Order.objects.create(user=user, total_price=total_price, status=status)
            for item_data in data.get('items', []):
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)
            return JsonResponse(order.serialize(), status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class OrderDetailView(View):
    @method_decorator(login_required)
    def get(self, request, id):
        try:
            order = Order.objects.get(id=id, user=request.user)
            return JsonResponse(order.serialize())
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

    @method_decorator(login_required)
    def delete(self, request, id):
        try:
            order = Order.objects.get(id=id, user=request.user)
            order.delete()
            return JsonResponse({'message': 'Order deleted'}, status=204)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'main/order_list.html', {'orders': orders})

@login_required
@user_passes_test(is_staff)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'main/order_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def order_update(request, id):
    order = get_object_or_404(Order, id=id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)
    return render(request, 'main/order_form.html', {'form': form})

@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    items = OrderItem.objects.filter(order=order)
    return render(request, 'main/order_detail.html', {'order': order, 'items': items})

@login_required
def order_delete(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    if request.method == 'POST':
        order.delete()
        return redirect('order_list')
    return render(request, 'main/order_confirm_delete.html', {'order': order})

@login_required
@user_passes_test(is_staff)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'main/product_list.html', {'products': products})

@login_required
@user_passes_test(is_staff)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'main/product_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def product_update(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'main/product_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'main/product_confirm_delete.html', {'product': product})

def home(request):
    return render(request, 'main/home.html')

# def product_list(request):
#     products = Product.objects.all()
#     return render(request, 'main/product_list.html', {'products': products})

def product_detail(request, id):
    product = Product.objects.get(id=id)
    return render(request, 'main/product_detail.html', {'product': product})

# @login_required
# def cart(request):
#     return render(request, 'main/cart.html')

# @login_required
# def checkout(request):
#     return render(request, 'main/checkout.html')

# @login_required
# def order_history(request):
#     return render(request, 'main/order_history.html')

# def register(request):
#     return render(request, 'main/register.html')

# def login_view(request):
#     return render(request, 'main/login.html')

# def verify_email(request):
#     return render(request, 'main/verify_email.html')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid() and password_form.is_valid():
            user = form.save()
            user.save()
            password_form.save()
            update_session_auth_hash(request, user)  # Important to update the session with the new password
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
    return render(request, 'main/profile.html', {'form': form, 'password_form': password_form})

@login_required
def change_password(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important to update the session with the new password
            return redirect('profile')
    else:
        password_form = PasswordChangeForm(request.user)
    return render(request, 'main/change_password.html', {'password_form': password_form})

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain
    link = f"http://{domain}/verify-email/?uid={uid}&token={token}"
    mail_subject = 'Activate your account.'
    message = render_to_string('main/verification_email.html', {
        'user': user,
        'link': link,
    })
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_verification_email(user, request)
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})

def verify_email(request):
    uid = request.GET.get('uid')
    token = request.GET.get('token')
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'main/verification_failed.html')

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart.quantity += 1
    cart.save()
    return redirect('cart')

def product_list(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    products = Product.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)

    categories = Category.objects.all()
    return render(request, 'main/product_list.html', {'products': products, 'categories': categories})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'main/login.html', {'form': form})

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def update_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        order = Order.objects.create(user=request.user, total_price=total_price)
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        cart_items.delete()
        return redirect('order_history')
    
    return render(request, 'main/checkout.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'main/order_history.html', {'orders': orders})

def logout_view(request):
    logout(request)
    return redirect('home')