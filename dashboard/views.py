from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from account.models import User
from core.models import Order, Offer, Comment, Coach, FastSell, BuyGold, Expansion, Realm, Method
from shop.models import Product, Category, Invoice, InvoiceItem, ShopComment, Payment


# Helper function - فقط ادمین‌ها دسترسی دارن
def is_admin(user):
    return user.is_staff or user.is_superuser


# Dashboard Home
@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    # آمارهای کلی
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    pending_offers = Offer.objects.filter(status='review').count()

    # آمار این ماه
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = User.objects.filter(date_joined__gte=current_month).count()
    new_orders_this_month = Order.objects.filter(created_at__gte=current_month).count()

    # آخرین سفارشات
    recent_orders = Order.objects.order_by('-created_at')[:5]

    # آخرین آفرها
    recent_offers = Offer.objects.select_related('seller', 'order').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_products': total_products,
        'pending_offers': pending_offers,
        'new_users_this_month': new_users_this_month,
        'new_orders_this_month': new_orders_this_month,
        'recent_orders': recent_orders,
        'recent_offers': recent_offers,
    }

    return render(request, 'dashboard/home.html', context)


# ============ USERS ============
@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    context = {'users': users, 'search': search}
    return render(request, 'dashboard/users/list.html', context)


@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)

    # آمار کاربر
    user_orders = Order.objects.filter(buyer=user.username).count()
    user_offers = Offer.objects.filter(seller=user).count()
    user_invoices = Invoice.objects.filter(user=user)

    # لیست آخرین پیشنهادات کاربر
    user_offers_list = Offer.objects.filter(seller=user).select_related('order').order_by('-created_at')[:5]

    context = {
        'user_obj': user,
        'user_orders': user_orders,
        'user_offers': user_offers,
        'user_invoices': user_invoices,
        'user_offers_list': user_offers_list,
    }
    return render(request, 'dashboard/users/detail.html', context)


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)

    # فقط سوپر یوزر می‌تونه سوپر یوزر دیگه رو ویرایش کنه
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'شما اجازه ویرایش سوپر ادمین را ندارید.')
        return redirect('dashboard:user_detail', pk=pk)

    if request.method == 'POST':
        # دریافت اطلاعات از فرم
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        discord_id = request.POST.get('discord_id', '')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'

        # بررسی یونیک بودن username و email
        if User.objects.filter(username=username).exclude(pk=pk).exists():
            messages.error(request, 'این نام کاربری قبلاً استفاده شده است.')
        elif User.objects.filter(email=email).exclude(pk=pk).exists():
            messages.error(request, 'این ایمیل قبلاً استفاده شده است.')
        else:
            # ذخیره اطلاعات
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.phone = phone
            user.discord_id = discord_id
            user.is_active = is_active

            # فقط سوپر یوزر می‌تونه دسترسی‌ها رو تغییر بده
            if request.user.is_superuser:
                user.is_staff = is_staff
                user.is_superuser = is_superuser

            user.save()

            # ویرایش اطلاعات بانکی
            full_name = request.POST.get('bank_full_name', '')
            card_number = request.POST.get('bank_card_number', '')
            shaba_number = request.POST.get('bank_shaba_number', '')

            if full_name or card_number or shaba_number:
                from account.models import BankAccount
                bank_account, created = BankAccount.objects.get_or_create(user=user)
                bank_account.full_name = full_name
                bank_account.card_number = card_number
                bank_account.shaba_number = shaba_number
                bank_account.save()

            # ویرایش اطلاعات کوچ
            is_coach = request.POST.get('is_coach') == 'on'
            if is_coach:
                coach_description = request.POST.get('coach_description', '')
                coach_timeplay = request.POST.get('coach_timeplay', 0)
                coach_enable = request.POST.get('coach_enable') == 'on'
                coach_expansions = request.POST.getlist('coach_expansions')
                coach_methods = request.POST.getlist('coach_methods')

                # ایجاد یا به‌روزرسانی کوچ
                coach, created = Coach.objects.get_or_create(user=user)
                coach.description = coach_description
                coach.timeplay = int(coach_timeplay) if coach_timeplay else 0
                coach.enable = coach_enable
                coach.save()

                # به‌روزرسانی Expansions و Methods
                coach.expansions.set(coach_expansions)
                coach.methods.set(coach_methods)
            else:
                # اگر چک‌باکس کوچ خاموش شد، کوچ رو حذف کن
                try:
                    Coach.objects.filter(user=user).delete()
                except:
                    pass

            # اگر پسورد جدید وارد شده باشه
            new_password = request.POST.get('new_password', '')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')

            messages.success(request, 'اطلاعات کاربر با موفقیت به‌روزرسانی شد.')
            return redirect('dashboard:user_detail', pk=pk)

    # دریافت اطلاعات بانکی
    try:
        from account.models import BankAccount
        bank_account = BankAccount.objects.get(user=user)
    except:
        bank_account = None

    # دریافت اطلاعات کوچ
    try:
        coach = Coach.objects.get(user=user)
    except Coach.DoesNotExist:
        coach = None

    # دریافت لیست Expansions و Methods
    expansions = Expansion.objects.all()
    methods = Method.objects.all()

    context = {
        'user_obj': user,
        'bank_account': bank_account,
        'coach': coach,
        'expansions': expansions,
        'methods': methods,
    }
    return render(request, 'dashboard/users/edit.html', context)


@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, pk):
    """تغییر وضعیت فعال/غیرفعال کاربر"""
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)

        # نمی‌شه سوپر ادمین رو غیرفعال کرد
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'شما نمی‌توانید سوپر ادمین را غیرفعال کنید.')
        else:
            user.is_active = not user.is_active
            user.save()

            status = 'فعال' if user.is_active else 'غیرفعال'
            messages.success(request, f'کاربر {status} شد.')

        return redirect('dashboard:user_detail', pk=pk)

    return redirect('dashboard:user_list')


@login_required
@user_passes_test(is_admin)
def user_toggle_staff(request, pk):
    """تغییر دسترسی ادمین"""
    if request.method == 'POST' and request.user.is_superuser:
        user = get_object_or_404(User, pk=pk)
        user.is_staff = not user.is_staff
        user.save()

        status = 'اضافه' if user.is_staff else 'حذف'
        messages.success(request, f'دسترسی ادمین {status} شد.')

        return redirect('dashboard:user_detail', pk=pk)

    return redirect('dashboard:user_list')


# ============ ORDERS ============
@login_required
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')

    # فیلتر وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # جستجو
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            Q(title__icontains=search) |
            Q(buyer__icontains=search)
        )

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'dashboard/orders/list.html', context)


@login_required
@user_passes_test(is_admin)
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    offers = order.offers.all().select_related('seller')

    context = {'order': order, 'offers': offers}
    return render(request, 'dashboard/orders/detail.html', context)


@login_required
@user_passes_test(is_admin)
def order_create(request):
    if request.method == 'POST':
        # اینجا فرم رو پردازش می‌کنیم
        pass

    expansions = Expansion.objects.all()
    realms = Realm.objects.all()

    context = {
        'expansions': expansions,
        'realms': realms,
        'faction_choices': Order.FACTION_CHOICES,
        'region_choices': Order.REGION_CHOICES,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'dashboard/orders/create.html', context)


@login_required
@user_passes_test(is_admin)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        # پردازش فرم
        pass

    expansions = Expansion.objects.all()
    realms = Realm.objects.all()

    context = {
        'order': order,
        'expansions': expansions,
        'realms': realms,
        'faction_choices': Order.FACTION_CHOICES,
        'region_choices': Order.REGION_CHOICES,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'dashboard/orders/edit.html', context)


@login_required
@user_passes_test(is_admin)
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.delete()
        messages.success(request, 'سفارش با موفقیت حذف شد.')
        return redirect('dashboard:order_list')

    return render(request, 'dashboard/orders/delete.html', {'order': order})


# ============ OFFERS ============
@login_required
@user_passes_test(is_admin)
def offer_list(request):
    offers = Offer.objects.select_related('seller', 'order').order_by('-created_at')

    # فیلتر وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter:
        offers = offers.filter(status=status_filter)

    # فیلتر بر اساس فروشنده
    seller_id = request.GET.get('seller', '')
    if seller_id:
        offers = offers.filter(seller_id=seller_id)
        try:
            seller = User.objects.get(id=seller_id)
        except User.DoesNotExist:
            seller = None
    else:
        seller = None

    context = {
        'offers': offers,
        'status_filter': status_filter,
        'status_choices': Offer.STATUS_CHOICES,
        'seller': seller,
    }
    return render(request, 'dashboard/offers/list.html', context)


@login_required
@user_passes_test(is_admin)
def offer_detail(request, pk):
    offer = get_object_or_404(Offer.objects.select_related('seller', 'order'), pk=pk)

    context = {'offer': offer}
    return render(request, 'dashboard/offers/detail.html', context)


@login_required
@user_passes_test(is_admin)
def offer_update_status(request, pk):
    if request.method == 'POST':
        offer = get_object_or_404(Offer, pk=pk)
        new_status = request.POST.get('status')

        if new_status in dict(Offer.STATUS_CHOICES):
            offer.status = new_status
            offer.save()
            messages.success(request, 'وضعیت آفر به‌روزرسانی شد.')

        return redirect('dashboard:offer_detail', pk=pk)

    return redirect('dashboard:offer_list')


# ============ PRODUCTS ============
@login_required
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.select_related('category').order_by('-create_date')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        products = products.filter(name__icontains=search)

    context = {'products': products, 'search': search}
    return render(request, 'dashboard/products/list.html', context)


@login_required
@user_passes_test(is_admin)
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)

    context = {'product': product}
    return render(request, 'dashboard/products/detail.html', context)


@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        # پردازش فرم
        pass

    categories = Category.objects.all()
    users = User.objects.filter(is_staff=True)

    context = {'categories': categories, 'users': users}
    return render(request, 'dashboard/products/create.html', context)


@login_required
@user_passes_test(is_admin)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        # پردازش فرم
        pass

    categories = Category.objects.all()

    context = {'product': product, 'categories': categories}
    return render(request, 'dashboard/products/edit.html', context)


@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'محصول با موفقیت حذف شد.')
        return redirect('dashboard:product_list')

    return render(request, 'dashboard/products/delete.html', {'product': product})


# ============ COMMENTS ============
@login_required
@user_passes_test(is_admin)
def comment_list(request):
    # کامنت‌های فروشگاه و کوچ
    shop_comments = ShopComment.objects.select_related('user', 'product').order_by('-created_at')
    core_comments = Comment.objects.select_related('user', 'coach').order_by('-created_at')

    context = {
        'shop_comments': shop_comments,
        'core_comments': core_comments,
    }
    return render(request, 'dashboard/comments/list.html', context)


@login_required
@user_passes_test(is_admin)
def comment_toggle(request, pk):
    comment_type = request.GET.get('type', 'shop')

    if comment_type == 'shop':
        comment = get_object_or_404(ShopComment, pk=pk)
    else:
        comment = get_object_or_404(Comment, pk=pk)

    comment.enable = not comment.enable
    comment.save()

    messages.success(request, 'وضعیت کامنت تغییر کرد.')
    return redirect('dashboard:comment_list')


# ============ COACHES ============
@login_required
@user_passes_test(is_admin)
def coach_list(request):
    coaches = Coach.objects.select_related('user').prefetch_related('expansions', 'methods')

    context = {'coaches': coaches}
    return render(request, 'dashboard/coaches/list.html', context)


@login_required
@user_passes_test(is_admin)
def coach_toggle(request, pk):
    coach = get_object_or_404(Coach, pk=pk)
    coach.enable = not coach.enable
    coach.save()

    messages.success(request, 'وضعیت کوچ تغییر کرد.')
    return redirect('dashboard:coach_list')


# ============ INVOICES ============
@login_required
@user_passes_test(is_admin)
def invoice_list(request):
    # 1. دریافت پارامترهای فیلتر از درخواست GET
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    payment_status = request.GET.get('payment_status')

    # شروع کوئری
    invoices = Invoice.objects.select_related('user', 'payment').order_by('-date')

    # 2. اعمال فیلتر جستجوی کلی (Search)
    if search:
        # جستجو در username، email، شماره فاکتور، و battle_tag
        invoices = invoices.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(number__icontains=search) |
            Q(id__icontains=search) | # برای اطمینان از جستجو بر اساس ID در صورت نبود number
            Q(battle_tag__icontains=search)
        )

    # 3. اعمال فیلتر تاریخ (Date Range)
    if date_from:
        invoices = invoices.filter(date__gte=date_from)
    if date_to:
        invoices = invoices.filter(date__lte=date_to)

    # 4. اعمال فیلتر مبلغ (Amount Range)
    if min_amount:
        try:
            min_amount_val = float(min_amount)
            invoices = invoices.filter(total__gte=min_amount_val)
        except ValueError:
            pass # در صورت نامعتبر بودن ورودی، نادیده گرفته می شود

    if max_amount:
        try:
            max_amount_val = float(max_amount)
            invoices = invoices.filter(total__lte=max_amount_val)
        except ValueError:
            pass # در صورت نامعتبر بودن ورودی، نادیده گرفته می شود

    # 5. اعمال فیلتر وضعیت پرداخت (Payment Status)
    if payment_status:
        # توجه: ما فرض می کنیم فیلد status در مدل Payment است.
        invoices = invoices.filter(payment__status=payment_status)


    # 6. ارسال پارامترها به Context برای حفظ وضعیت فیلترها در فرم
    context = {
        'invoices': invoices,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'payment_status': payment_status,
        # توجه: URL برای پاک کردن فیلترها باید وجود داشته باشد.
        # در تمپلیت: {% url 'dashboard:invoice_list' %}
    }
    return render(request, 'dashboard/invoices/list.html', context)
# def invoice_list(request):
#     invoices = Invoice.objects.select_related('user').order_by('-date')
#
#     context = {'invoices': invoices}
#     return render(request, 'dashboard/invoices/list.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('user'), pk=pk)
    items = InvoiceItem.objects.filter(invoice=invoice).select_related('product')

    try:
        payment = Payment.objects.get(invoice=invoice)
    except Payment.DoesNotExist:
        payment = None

    context = {
        'invoice': invoice,
        'items': items,
        'payment': payment,
    }
    return render(request, 'dashboard/invoices/detail.html', context)