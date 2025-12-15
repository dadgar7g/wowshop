from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.views.decorators.http import require_POST
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
# ============ COACHES ============
@login_required
@user_passes_test(is_admin)
def coach_list(request):
    coaches = Coach.objects.select_related('user').prefetch_related('expansions', 'methods').order_by('-id')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        coaches = coaches.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(description__icontains=search)
        )

    # فیلتر وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter == 'enabled':
        coaches = coaches.filter(enable=True)
    elif status_filter == 'disabled':
        coaches = coaches.filter(enable=False)

    context = {
        'coaches': coaches,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/coaches/list.html', context)


@login_required
@user_passes_test(is_admin)
def coach_detail(request, pk):
    coach = get_object_or_404(
        Coach.objects.select_related('user').prefetch_related('expansions', 'methods', 'comments'),
        pk=pk
    )

    # دریافت کامنت‌های کوچ
    comments = Comment.objects.filter(coach=coach).select_related('user').order_by('-created_at')[:10]

    # آمار کوچ
    total_comments = Comment.objects.filter(coach=coach).count()
    approved_comments = Comment.objects.filter(coach=coach, enable=True).count()

    context = {
        'coach': coach,
        'comments': comments,
        'total_comments': total_comments,
        'approved_comments': approved_comments,
    }
    return render(request, 'dashboard/coaches/detail.html', context)


@login_required
@user_passes_test(is_admin)
def coach_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        description = request.POST.get('description', '').strip()
        timeplay = request.POST.get('timeplay', 0)
        enable = request.POST.get('enable') == 'on'
        expansions = request.POST.getlist('expansions')
        methods = request.POST.getlist('methods')

        if not user_id:
            messages.error(request, 'انتخاب کاربر الزامی است.')
        elif not description:
            messages.error(request, 'توضیحات الزامی است.')
        else:
            try:
                user = User.objects.get(id=user_id)

                # بررسی که قبلاً کوچ نباشه
                if Coach.objects.filter(user=user).exists():
                    messages.error(request, 'این کاربر قبلاً به عنوان کوچ ثبت شده است.')
                else:
                    # ایجاد کوچ
                    coach = Coach.objects.create(
                        user=user,
                        description=description,
                        timeplay=int(timeplay) if timeplay else 0,
                        enable=enable
                    )

                    # اضافه کردن Expansions و Methods
                    if expansions:
                        coach.expansions.set(expansions)
                    if methods:
                        coach.methods.set(methods)

                    messages.success(request, 'کوچ با موفقیت ایجاد شد.')
                    return redirect('dashboard:coach_detail', pk=coach.id)

            except User.DoesNotExist:
                messages.error(request, 'کاربر یافت نشد.')

    # کاربرانی که هنوز کوچ نیستند
    coach_user_ids = Coach.objects.values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=coach_user_ids).order_by('username')

    expansions = Expansion.objects.all()
    methods = Method.objects.all()

    context = {
        'available_users': available_users,
        'expansions': expansions,
        'methods': methods,
    }
    return render(request, 'dashboard/coaches/create.html', context)


@login_required
@user_passes_test(is_admin)
def coach_edit(request, pk):
    coach = get_object_or_404(Coach.objects.select_related('user').prefetch_related('expansions', 'methods'), pk=pk)

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        timeplay = request.POST.get('timeplay', 0)
        enable = request.POST.get('enable') == 'on'
        expansions = request.POST.getlist('expansions')
        methods = request.POST.getlist('methods')

        if not description:
            messages.error(request, 'توضیحات الزامی است.')
        else:
            # ویرایش کوچ
            coach.description = description
            coach.timeplay = int(timeplay) if timeplay else 0
            coach.enable = enable
            coach.save()

            # به‌روزرسانی Expansions و Methods
            coach.expansions.set(expansions)
            coach.methods.set(methods)

            messages.success(request, 'اطلاعات کوچ با موفقیت به‌روزرسانی شد.')
            return redirect('dashboard:coach_detail', pk=pk)

    expansions = Expansion.objects.all()
    methods = Method.objects.all()

    context = {
        'coach': coach,
        'expansions': expansions,
        'methods': methods,
    }
    return render(request, 'dashboard/coaches/edit.html', context)


@login_required
@user_passes_test(is_admin)
def coach_delete(request, pk):
    coach = get_object_or_404(Coach, pk=pk)

    if request.method == 'POST':
        # بررسی کامنت‌ها
        comments_count = Comment.objects.filter(coach=coach).count()

        # حذف کوچ (کامنت‌ها با CASCADE حذف میشن)
        coach_username = coach.user.username
        coach.delete()

        messages.success(request, f'کوچ {coach_username} با موفقیت حذف شد.')
        return redirect('dashboard:coach_list')

    # شمارش کامنت‌ها
    comments_count = Comment.objects.filter(coach=coach).count()

    context = {
        'coach': coach,
        'comments_count': comments_count,
    }
    return render(request, 'dashboard/coaches/delete.html', context)


@login_required
@user_passes_test(is_admin)
def coach_toggle(request, pk):
    """تغییر وضعیت فعال/غیرفعال کوچ"""
    if request.method == 'POST':
        coach = get_object_or_404(Coach, pk=pk)
        coach.enable = not coach.enable
        coach.save()

        status = 'فعال' if coach.enable else 'غیرفعال'
        messages.success(request, f'وضعیت کوچ به {status} تغییر کرد.')

        return redirect('dashboard:coach_detail', pk=pk)

    return redirect('dashboard:coach_list')


# این رو به آخر فایل views.py اضافه کن:


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


#============= Fastsell ===========
@login_required
@user_passes_test(is_admin)
def fastsell_list(request):
    # 1. دریافت پارامترهای فیلتر از درخواست GET
    search = request.GET.get('search', '').strip() # از .strip() برای حذف فاصله‌های اضافی استفاده کنید
    is_read_filter = request.GET.get('is_read') # نام متغیر را تغییر دادیم تا با نام فیلد درگیری نداشته باشد

    # شروع کوئری
    fastSells = FastSell.objects.all().order_by('-created_at') # بهتر است ترتیب نمایش را مشخص کنید

    # 2. اعمال فیلتر جستجوی کلی (Search)
    if search:
        # فرض بر این است که مدل FastSell دارای فیلد 'number' است
        fastSells = fastSells.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(id__icontains=search)  | # جستجو بر اساس ID
            Q(text__icontains=search) # اضافه کردن جستجو در متن پیام
        )


    # 5. اعمال فیلتر وضعیت خوانده شدن (is_read)
    if is_read_filter:
        # تبدیل مقدار رشته‌ای به بولی برای فیلتر دیتابیس
        if is_read_filter == 'read':
            fastSells = fastSells.filter(is_read=True)
        elif is_read_filter == 'unread':
            fastSells = fastSells.filter(is_read=False)


    # 6. ارسال پارامترها به Context برای حفظ وضعیت فیلترها در فرم
    context = {
        'fastsells': fastSells,
        'search': search,
        'is_read': is_read_filter, # ارسال متغیر فیلتر جدید
    }
    return render(request, 'dashboard/fastsell/list.html', context)


@login_required
@user_passes_test(is_admin)
def fastsell_detail(request, pk):
    """نمایش جزئیات یک پیام FastSell و علامت زدن آن به عنوان خوانده شده."""

    fastsell = get_object_or_404(FastSell.objects.select_related('user'), pk=pk)

    # # *** منطق کلیدی: علامت زدن به عنوان خوانده شده هنگام مشاهده ***
    # if not fastsell.is_read:
    #     fastsell.is_read = True
    #     fastsell.save()
    # # **********************************************

    context = {
        'fastsell': fastsell,
    }
    return render(request, 'dashboard/fastsell/detail.html', context)


@login_required
@user_passes_test(is_admin)

@require_POST  # تضمین می کند که این View فقط با متد POST اجرا شود
def fastsell_toggle_read(request, pk):
    """تغییر وضعیت is_read (دیده شده/دیده نشده) برای یک پیام FastSell."""

    fastsell = get_object_or_404(FastSell, pk=pk)

    # تغییر وضعیت is_read به مقدار مخالف فعلی
    fastsell.is_read = not fastsell.is_read
    fastsell.save()

    # افزودن پیام موفقیت (اختیاری)
    # messages.success(request, f"وضعیت پیام #{pk} با موفقیت به {'خوانده شده' if fastsell.is_read else 'خوانده نشده'} تغییر یافت.")

    # بازگشت به صفحه جزئیات
    return redirect(reverse('dashboard:fastsell_detail', kwargs={'pk': pk}))



# ============ COMMENTS ============
@login_required
@user_passes_test(is_admin)
def shop_comment_list(request):
    # کامنت‌های فروشگاه
    comments = ShopComment.objects.select_related('user', 'product').order_by('-created_at')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        comments = comments.filter(
            Q(text__icontains=search) |
            Q(user__username__icontains=search) |
            Q(product__name__icontains=search)
        )

    # فیلتر وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter == 'enabled':
        comments = comments.filter(enable=True)
    elif status_filter == 'disabled':
        comments = comments.filter(enable=False)

    context = {
        'comments': comments,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/comments/shop_list.html', context)


@login_required
@user_passes_test(is_admin)
def shop_comment_toggle(request, pk):
    comment = get_object_or_404(ShopComment, pk=pk)
    comment.enable = not comment.enable
    comment.save()

    messages.success(request, f'وضعیت کامنت به {"تایید شده" if comment.enable else "رد شده"} تغییر کرد.')
    return redirect('dashboard:shop_comment_list')


@login_required
@user_passes_test(is_admin)
def coach_comment_list(request):
    # کامنت‌های کوچ
    comments = Comment.objects.select_related('user', 'coach__user').order_by('-created_at')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        comments = comments.filter(
            Q(text__icontains=search) |
            Q(user__username__icontains=search) |
            Q(coach__user__username__icontains=search)
        )

    # فیلتر وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter == 'enabled':
        comments = comments.filter(enable=True)
    elif status_filter == 'disabled':
        comments = comments.filter(enable=False)

    context = {
        'comments': comments,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/comments/coach_list.html', context)


@login_required
@user_passes_test(is_admin)
def coach_comment_toggle(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.enable = not comment.enable
    comment.save()

    messages.success(request, f'وضعیت کامنت به {"تایید شده" if comment.enable else "رد شده"} تغییر کرد.')
    return redirect('dashboard:coach_comment_list')


# این رو به آخر فایل views.py اضافه کن:

# ============ EXPANSIONS ============
@login_required
@user_passes_test(is_admin)
def expansion_list(request):
    expansions = Expansion.objects.all().order_by('name')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        expansions = expansions.filter(name__icontains=search)

    context = {
        'expansions': expansions,
        'search': search,
    }
    return render(request, 'dashboard/expansions/list.html', context)


@login_required
@user_passes_test(is_admin)
def expansion_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Expansion الزامی است.')
        elif Expansion.objects.filter(name=name).exists():
            messages.error(request, 'این Expansion قبلاً ثبت شده است.')
        else:
            Expansion.objects.create(name=name)
            messages.success(request, 'Expansion با موفقیت ایجاد شد.')
            return redirect('dashboard:expansion_list')

    return render(request, 'dashboard/expansions/create.html')


@login_required
@user_passes_test(is_admin)
def expansion_edit(request, pk):
    expansion = get_object_or_404(Expansion, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Expansion الزامی است.')
        elif Expansion.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, 'این Expansion قبلاً ثبت شده است.')
        else:
            expansion.name = name
            expansion.save()
            messages.success(request, 'Expansion با موفقیت ویرایش شد.')
            return redirect('dashboard:expansion_list')

    context = {'expansion': expansion}
    return render(request, 'dashboard/expansions/edit.html', context)


@login_required
@user_passes_test(is_admin)
def expansion_delete(request, pk):
    expansion = get_object_or_404(Expansion, pk=pk)

    if request.method == 'POST':
        # بررسی اینکه آیا استفاده شده یا نه
        if Order.objects.filter(expansion=expansion).exists():
            messages.error(request, 'این Expansion در سفارشات استفاده شده و نمی‌توان حذف کرد.')
        elif Coach.objects.filter(expansions=expansion).exists():
            messages.error(request, 'این Expansion در کوچ‌ها استفاده شده و نمی‌توان حذف کرد.')
        else:
            expansion.delete()
            messages.success(request, 'Expansion با موفقیت حذف شد.')
            return redirect('dashboard:expansion_list')

    context = {'expansion': expansion}
    return render(request, 'dashboard/expansions/delete.html', context)


# ============ REALMS ============
@login_required
@user_passes_test(is_admin)
def realm_list(request):
    realms = Realm.objects.all().order_by('name')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        realms = realms.filter(name__icontains=search)

    context = {
        'realms': realms,
        'search': search,
    }
    return render(request, 'dashboard/realms/list.html', context)


@login_required
@user_passes_test(is_admin)
def realm_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Realm الزامی است.')
        elif Realm.objects.filter(name=name).exists():
            messages.error(request, 'این Realm قبلاً ثبت شده است.')
        else:
            Realm.objects.create(name=name)
            messages.success(request, 'Realm با موفقیت ایجاد شد.')
            return redirect('dashboard:realm_list')

    return render(request, 'dashboard/realms/create.html')
    return render(request, 'dashboard/realms/create.html')


@login_required
@user_passes_test(is_admin)
def realm_edit(request, pk):
    realm = get_object_or_404(Realm, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Realm الزامی است.')
        elif Realm.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, 'این Realm قبلاً ثبت شده است.')
        else:
            realm.name = name
            realm.save()
            messages.success(request, 'Realm با موفقیت ویرایش شد.')
            return redirect('dashboard:realm_list')

    context = {'realm': realm}
    return render(request, 'dashboard/realms/edit.html', context)


@login_required
@user_passes_test(is_admin)
def realm_delete(request, pk):
    realm = get_object_or_404(Realm, pk=pk)

    if request.method == 'POST':
        # بررسی اینکه آیا استفاده شده یا نه
        if Order.objects.filter(realm=realm).exists():
            messages.error(request, 'این Realm در سفارشات استفاده شده و نمی‌توان حذف کرد.')
        else:
            realm.delete()
            messages.success(request, 'Realm با موفقیت حذف شد.')
            return redirect('dashboard:realm_list')

    context = {'realm': realm}
    return render(request, 'dashboard/realms/delete.html', context)


# ============ METHODS ============
@login_required
@user_passes_test(is_admin)
def method_list(request):
    methods = Method.objects.all().order_by('name')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        methods = methods.filter(name__icontains=search)

    context = {
        'methods': methods,
        'search': search,
    }
    return render(request, 'dashboard/methods/list.html', context)


@login_required
@user_passes_test(is_admin)
def method_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Method الزامی است.')
        elif Method.objects.filter(name=name).exists():
            messages.error(request, 'این Method قبلاً ثبت شده است.')
        else:
            Method.objects.create(name=name)
            messages.success(request, 'Method با موفقیت ایجاد شد.')
            return redirect('dashboard:method_list')

    return render(request, 'dashboard/methods/create.html')


@login_required
@user_passes_test(is_admin)
def method_edit(request, pk):
    method = get_object_or_404(Method, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'نام Method الزامی است.')
        elif Method.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, 'این Method قبلاً ثبت شده است.')
        else:
            method.name = name
            method.save()
            messages.success(request, 'Method با موفقیت ویرایش شد.')
            return redirect('dashboard:method_list')

    context = {'method': method}
    return render(request, 'dashboard/methods/edit.html', context)


@login_required
@user_passes_test(is_admin)
def method_delete(request, pk):
    method = get_object_or_404(Method, pk=pk)

    if request.method == 'POST':
        # بررسی اینکه آیا استفاده شده یا نه
        if Coach.objects.filter(methods=method).exists():
            messages.error(request, 'این Method در کوچ‌ها استفاده شده و نمی‌توان حذف کرد.')
        else:
            method.delete()
            messages.success(request, 'Method با موفقیت حذف شد.')
            return redirect('dashboard:method_list')

    context = {'method': method}
    return render(request, 'dashboard/methods/delete.html', context)


# ============ CATEGORIES ============
@login_required
@user_passes_test(is_admin)
def category_list(request):
    # دریافت تمام دسته‌بندی‌ها
    categories = Category.objects.filter(deleted=False).select_related('parent', 'user').order_by('name')

    # جستجو
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)

    # فیلتر بر اساس Parent (فقط دسته‌های اصلی یا فقط زیردسته‌ها)
    filter_type = request.GET.get('filter', '')
    if filter_type == 'parent':
        categories = categories.filter(parent__isnull=True)
    elif filter_type == 'child':
        categories = categories.filter(parent__isnull=False)

    context = {
        'categories': categories,
        'search': search,
        'filter_type': filter_type,
    }
    return render(request, 'dashboard/categories/list.html', context)


@login_required
@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        parent_id = request.POST.get('parent', None)

        if not name:
            messages.error(request, 'نام دسته‌بندی الزامی است.')
        else:
            # بررسی تکراری بودن
            if Category.objects.filter(name=name, deleted=False).exists():
                messages.error(request, 'این دسته‌بندی قبلاً ثبت شده است.')
            else:
                # ایجاد دسته‌بندی
                parent = None
                if parent_id:
                    try:
                        parent = Category.objects.get(id=parent_id, deleted=False)
                    except Category.DoesNotExist:
                        messages.error(request, 'دسته‌بندی والد یافت نشد.')
                        return render(request, 'dashboard/categories/create.html', {
                            'parents': Category.objects.filter(parent__isnull=True, deleted=False)
                        })

                Category.objects.create(
                    name=name,
                    parent=parent,
                    user=request.user
                )
                messages.success(request, 'دسته‌بندی با موفقیت ایجاد شد.')
                return redirect('dashboard:category_list')

    # دسته‌بندی‌های اصلی برای انتخاب به عنوان Parent
    parents = Category.objects.filter(parent__isnull=True, deleted=False).order_by('name')

    context = {'parents': parents}
    return render(request, 'dashboard/categories/create.html', context)


@login_required
@user_passes_test(is_admin)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, deleted=False)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        parent_id = request.POST.get('parent', None)

        if not name:
            messages.error(request, 'نام دسته‌بندی الزامی است.')
        else:
            # بررسی تکراری بودن
            if Category.objects.filter(name=name, deleted=False).exclude(pk=pk).exists():
                messages.error(request, 'این دسته‌بندی قبلاً ثبت شده است.')
            else:
                # ویرایش دسته‌بندی
                parent = None
                if parent_id:
                    try:
                        parent = Category.objects.get(id=parent_id, deleted=False)

                        # جلوگیری از انتخاب خودش یا فرزندانش به عنوان Parent
                        if parent.id == category.id:
                            messages.error(request, 'نمی‌توانید دسته‌بندی را به عنوان والد خودش انتخاب کنید.')
                            parents = Category.objects.filter(parent__isnull=True, deleted=False).exclude(pk=pk)
                            return render(request, 'dashboard/categories/edit.html', {
                                'category': category,
                                'parents': parents
                            })

                        # بررسی که parent از فرزندان category نباشه
                        if parent.parent and parent.parent.id == category.id:
                            messages.error(request, 'نمی‌توانید فرزند دسته‌بندی را به عنوان والد آن انتخاب کنید.')
                            parents = Category.objects.filter(parent__isnull=True, deleted=False).exclude(pk=pk)
                            return render(request, 'dashboard/categories/edit.html', {
                                'category': category,
                                'parents': parents
                            })

                    except Category.DoesNotExist:
                        messages.error(request, 'دسته‌بندی والد یافت نشد.')
                        parents = Category.objects.filter(parent__isnull=True, deleted=False).exclude(pk=pk)
                        return render(request, 'dashboard/categories/edit.html', {
                            'category': category,
                            'parents': parents
                        })

                category.name = name
                category.parent = parent
                category.save()

                messages.success(request, 'دسته‌بندی با موفقیت ویرایش شد.')
                return redirect('dashboard:category_list')

    # دسته‌بندی‌های اصلی برای انتخاب به عنوان Parent (به جز خودش)
    parents = Category.objects.filter(parent__isnull=True, deleted=False).exclude(pk=pk).order_by('name')

    context = {
        'category': category,
        'parents': parents
    }
    return render(request, 'dashboard/categories/edit.html', context)


@login_required
@user_passes_test(is_admin)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, deleted=False)

    if request.method == 'POST':
        # بررسی اینکه آیا محصولی دارد یا نه
        if Product.objects.filter(category=category, deleted=False).exists():
            messages.error(request, 'این دسته‌بندی دارای محصول است و نمی‌توان حذف کرد.')
        # بررسی اینکه آیا زیردسته دارد یا نه
        elif Category.objects.filter(parent=category, deleted=False).exists():
            messages.error(request, 'این دسته‌بندی دارای زیردسته است و نمی‌توان حذف کرد.')
        else:
            # Soft Delete
            category.deleted = True
            category.deleted_date = timezone.now()
            category.save()

            messages.success(request, 'دسته‌بندی با موفقیت حذف شد.')
            return redirect('dashboard:category_list')

    # شمارش محصولات و زیردسته‌ها
    products_count = Product.objects.filter(category=category, deleted=False).count()
    children_count = Category.objects.filter(parent=category, deleted=False).count()

    context = {
        'category': category,
        'products_count': products_count,
        'children_count': children_count,
    }
    return render(request, 'dashboard/categories/delete.html', context)