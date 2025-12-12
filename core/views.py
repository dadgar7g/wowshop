from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from . import models
from django.contrib import messages
from . import forms
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import timedelta


# Create your views here.


from shop.models import Product
class AboutView(View):
    def get(self, request):
        return render(request, "core/about.html")
class HomeView(View):
    def get(self, request, *args, **kwargs):
        orders = models.Order.objects.filter(status='available')[:3]
        products = Product.objects.all()[:6]

        context = {
            'orders': orders,
            'products': products,
        }
        return render(request, 'core/home.html', context)

class OredersView(View):
    def get(self, request):
        obj = models.Order.objects.all().order_by('-created_at')


        # فیلتر GET
        status = request.GET.get('status')
        if status:
            obj = obj.filter(status=status)

        faction = request.GET.get('faction')
        if faction:
            obj = obj.filter(faction=faction)

        region = request.GET.get('region')
        if region:
            obj = obj.filter(region=region)

        expansion = request.GET.get('expansion')
        if expansion:
            obj = obj.filter(expansion__id=expansion)


        expansions = models.Expansion.objects.all()

        paginator = Paginator(obj, 3)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'core/orders.html', {
            'page_obj': page_obj,
            'obj': obj,
            'expansions': expansions,
        })


@method_decorator(login_required, name="dispatch")
class OredersDetailView(View):
    def get(self, request, id):
        order = models.Order.objects.get(id=id)
        active_offer = models.Offer.objects.filter(
            order=order,
            seller=request.user,
            status__in=['review', 'pending', 'Awaiting_payment']
        ).first()

        return render(request, "core/order_details.html", {
            "order": order,
            "active_offer": active_offer
        })

    def post(self, request, id):
        order = models.Order.objects.get(id=id)


        if "gold_amount" in request.POST:
            gold = int(request.POST.get("gold_amount"))

            if gold < order.min_reserve or gold > order.rest:
                messages.error(request, "مقدار وارد شده معتبر نیست!")
                return redirect("core:order_detail", id=order.id)

            if gold % order.min_reserve != 0:
                messages.error(request, "مقدار باید ضریبی از حداقل رزرو باشد.")
                return redirect("core:order_detail", id=order.id)


            offer = models.Offer.objects.create(
                order=order,
                seller=request.user,
                quantity=gold,
                price_per_1k=order.price_per_1k,
                total_price=(gold / 1000) * order.price_per_1k,
                status="pending"
            )

            order.rest -= offer.quantity
            order.save()

            return redirect("core:order_detail", id=order.id)

        if "video" in request.FILES:
            video = request.FILES["video"]

            # چک نوع فایل
            allowed_types = ["video/mp4", "video/mpeg", "video/avi", "video/mov", "video/webm"]
            if video.content_type not in allowed_types:
                messages.error(request, "فقط فایل ویدیویی قابل قبول است.")
                return redirect("core:order_detail", id=order.id)

            # چک حجم
            max_size = 30 * 1024 * 1024
            if video.size > max_size:
                messages.error(request, "حجم ویدیو نباید بیشتر از ۳۰ مگابایت باشد.")
                return redirect("core:order_detail", id=order.id)

            offer = models.Offer.objects.filter(order=order, seller=request.user).last()
            if not offer:
                messages.error(request, "پیشنهاد یافت نشد.")
                return redirect("core:order_detail", id=order.id)

            offer.proof = video
            offer.status = "review"
            offer.save()

            return redirect("core:order_detail", id=order.id)


        messages.error(request, "درخواست نامعتبر است.")
        return redirect("core:order_detail", id=order.id)



from .forms import CoachForm, FastSellForm


@method_decorator(login_required, name="dispatch")
class CoachRegisterView(View):
    def get(self, request):
        if hasattr(request.user, "coach"):
            messages.error(request, "شما قبلا ثبت نام کرده اید، لطفا اگر قصد تغییری دارید اطلاعات خود را ویرایش کنید")
            return redirect("core:coach_edit")

        form = CoachForm()
        return render(request, "core/coach_register.html", {"form": form})

    def post(self, request):
        if hasattr(request.user, "coach"):
            messages.error(request, "شما قبلا ثبت نام کرده اید، لطفا اگر قصد تغییری دارید اطلاعات خود را ویرایش کنید")
            return redirect("core:coach_edit")

        form = CoachForm(request.POST)
        if form.is_valid():
            coach = form.save(commit=False)
            coach.user = request.user
            coach.save()

            form.save_m2m()
            return redirect("core:coach_list")

        return render(request, "core/coach_register.html", {"form": form})




class CoachListView(View):
    def get(self, request):
        coaches = models.Coach.objects.all().prefetch_related("expansions", "methods", "user")
        return render(request, "core/coach_list.html", {"coaches": coaches})


@method_decorator(login_required, name="dispatch")
class CoachDetailView(View):
    def get(self, request, user):
        try:
            coach = models.Coach.objects.get(user__username=user)
            if coach.enable == False:
                messages.error(request,"مربی مورد نظر یافت نشد لطفا از میان لیست مربیان مربی خود را پیدا کنید")
                return redirect("core:coach_list")
        except models.Coach.DoesNotExist:
            messages.error(request, "مربی یافت نشد.")
            return redirect("core:coach_list")

        return render(request, "core/coahc_details.html", {
            "coach": coach
        })

    def post(self, request, user):
        try:
            coach = models.Coach.objects.get(user__username=user)
        except models.Coach.DoesNotExist:
            messages.error(request, "مربی یافت نشد.")
            return redirect("core:coach_list")


        text = request.POST.get("text")
        if text and request.user.is_authenticated:
            comment = models.Comment.objects.create(
                user=request.user,
                text=text,
                enable=False
            )
            coach.comments.add(comment)

        return redirect("core:coach_detail", user=user)

@method_decorator(login_required, name="dispatch")
class CoachEditView(LoginRequiredMixin, View):
    def get(self, request):
        if not hasattr(request.user, "coach"):
            messages.error(request, "لطفا ابتدا اطلاعات خود را وارد کنید.")
            return redirect("core:coach_register")

        coach = request.user.coach
        form = CoachForm(instance=coach)
        return render(request, "core/coach_register.html", {"form": form, "edit": True})

    def post(self, request):
        if not hasattr(request.user, "coach"):
            messages.error(request, "لطفا ابتدا اطلاعات خود را وارد کنید.")
            return redirect("core:coach_register")

        coach = request.user.coach
        form = CoachForm(request.POST, instance=coach)
        if form.is_valid():
            form.save()
            return redirect("account:dashboard")

        return render(request, "core/coach_register.html", {"form": form, "edit": True})


@method_decorator(login_required, name="dispatch")
class FastSellView(LoginRequiredMixin,View):
    def get(self, request):
        form = FastSellForm()
        return render(request, 'core/fastsell.html', {'form': form})

    def post(self, request):
        last_message = models.FastSell.objects.filter(user=request.user).order_by('-created_at').first()
        if last_message and timezone.now() - last_message.created_at < timedelta(minutes=5):
            messages.error(request, "شما اخیراً درخواست ارسال کرده‌اید. لطفاً کمی صبر کنید.")
            return redirect('core:fast_sell')

        form = FastSellForm(request.POST)
        if form.is_valid():
            fastsell = form.save(commit=False)
            fastsell.user = request.user
            fastsell.save()

            return redirect('core:fastsell_success')

        return render(request, "core/fastsell.html", {'form': form})

class FastSellSuccess(View):
    def get(self, request):
        return render(request, 'core/fastsell_success.html')
