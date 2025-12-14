from django.shortcuts import render, HttpResponseRedirect, redirect
from django.template.context_processors import request
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from . import models
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from . import forms
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
# from zeep import Client
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.response import Response
from django.core.paginator import Paginator


# Create your views here.
# zarinpal = Client('https://api.zarinpal.com/pg/services/WebGate/wsdl')
mid = '04b20d1c-607c-4097-84e2-110dcd60c4a5'
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"



def get_cart_total_price(cart):
    total = 0
    objects = models.Product.objects.filter(id__in=list(cart.keys()))
    for id,count in cart.items():
        obj = objects.get(id=id)
        total += obj.price * count * (1 - obj.discount / 100)
    return total


def get_cart(request):
    cart = request.session.get('cart', {})
    if not cart or not isinstance (cart, dict):
        cart = {}
    return cart


def add_to_cart(cart, obj):
    if obj.count > 0 and obj.enabled:
        cart[obj.id] = cart.get(str(obj.id), 0) + 1


def remove_from_cart(cart, id):
    if str(id) in cart:
        del cart[str(id)]


class ListProducts(View):
    def get(self, request):
        obj = models.Product.objects.all().order_by('-create_date')

        # فیلتر بر اساس دسته‌بندی
        category = request.GET.get('category')
        if category:
            obj = obj.filter(category_id=category)

        # Pagination
        paginator = Paginator(obj, 3)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # ارسال دسته‌بندی‌ها به قالب
        categories = models.Category.objects.all()

        return render(request, 'core/product_list.html', {
            'page_obj': page_obj,
            'products': obj,
            'categories': categories,
            'selected_category': category
        })



class ProductDetailView(View):
    def get(self, request, id):
        obj = models.Product.objects.get(id=id)
        return render(request, 'core/product_details.html', {'obj': obj})

    def post(self, request, id):
        product = models.Product.objects.get(id=id)

        # ساخت کامنت جدید
        text = request.POST.get("text")
        if text and request.user.is_authenticated:
            comment = models.ShopComment.objects.create(
                user=request.user,
                text=text,
                enable=False  # نیاز به تأیید ادمین
            )
            product.comments.add(comment)

        return redirect("shop:product_detail", id=id)


class AddToCartView(View):
    def get(self, request, id):
        # if request.user.has_perm('core.can_buy'):
            obj = get_object_or_404(models.Product, id=id)
            cart = get_cart(request)
            add_to_cart(cart, obj)
            request.session['cart'] = cart

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
               return JsonResponse(cart)
            return HttpResponseRedirect(reverse('shop:product_list'))
        # else:
        #     return HttpResponseForbidden()


class RemoveFromCartView(View):
    def get(self, request, id):
        cart = get_cart(request)
        remove_from_cart(cart, id)
        request.session['cart'] = cart

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
           return JsonResponse({'total': get_cart_total_price(cart) ,
                                'cart': cart})
        return HttpResponseRedirect(reverse('shop:product_list'))


class EmptyCartView(View):
    def get(self, request,):
        request.session['cart'] = {}

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
           return JsonResponse({})
        return HttpResponseRedirect(reverse('shop:product_list'))


class ShowCartView(View):
    def get(self, request):
        cart = get_cart(request)
        objects = models.Product.objects.filter(id__in=list(cart.keys()))
        cart_objects = {}
        for id, count in cart.items():
            obj = objects.get(id=id)
            cart_objects[id] = {
                'obj': obj,
                'count': count,
                'price': obj.price * count * (1 - obj.discount / 100)
            }
        return render(request, 'core/cart.html', {'cart': cart_objects,
                                                               'total':get_cart_total_price(cart)})


# class CheckoutView(View):
#     def get(self, request):
#         form = forms.InvoiceForm()
#         cart = get_cart(request)
#         objects = models.Product.objects.filter(id__in=list.html(cart.keys()))
#         cart_objects = {}
#         for id, count in cart.items():
#             obj = objects.get(id=id)
#             cart_objects[id] = {
#                 'obj': obj,
#                 'count': count,
#                 'price': obj.price * count * (1 - obj.discount / 100)
#             }
#         return render(request, 'core/checkout.html',{'form': form,
#                                              'total': get_cart_total_price(cart),
#                                               'cart': cart_objects})
#
#     def post(self, request):
#         form = forms.InvoiceForm(request.POST)
#         if form.is_valid():
#             invoice = form.save(commit=False)
#             invoice.user = request.user
#             cart = get_cart(request)
#             invoice.total = get_cart_total_price(cart)
#             invoice.save()
#             items = models.Product.objects.filter(id__in=list.html(cart.keys()))
#             item_objects = []
#             for item_id, item_count in cart.items():
#                 obj = items.get(id=item_id)
#                 invoice_item_obj = models.InvoiceItem()
#                 invoice_item_obj.invoice = invoice
#                 invoice_item_obj.product = obj
#                 invoice_item_obj.count = item_count
#                 invoice_item_obj.discount = obj.discount
#                 invoice_item_obj.price = obj.price
#                 invoice_item_obj.name = obj.name
#                 invoice_item_obj.total = invoice_item_obj.price * invoice_item_obj.count
#                 invoice_item_obj.total -= invoice_item_obj.total * invoice_item_obj.discount
#                 # invoice_item_obj.save()
#                 item_objects.append(invoice_item_obj)
#             models.InvoiceItem.objects.bulk_create(item_objects)
#             payment = models.Payment()
#             payment.total = invoice.total - invoice.total * invoice.discount
#             payment.total += payment.total * invoice.vat
#             payment.description = 'خرید از سایت ما'
#             payment.user_ip = get_user_ip(request)
#
#
#             callback_url = "http://"+get_current_site(request)+reverse('shop:verify')
#
#             res = zarinpal.service.PaymrntRequest(mid, payment.total,
#                                                   payment.description,
#                                                   invoice.user.email,
#                                                   invoice.user.phone,
#                                                   callback_url)
#             if res.Status == 100:
#                 payment.authority = res.Authority
#                 payment.save()
#                 return redirect(f"https://api.zarinpal.com/pg/StartPay/{payment.authority}")
#             else:
#                 return render(request, 'core/checkout_error.html')
#         return render(request, 'core/checkout.html', {'form': form})


class CheckoutView(LoginRequiredMixin ,View):
    def get(self, request):
        form = forms.InvoiceForm()
        cart = get_cart(request)
        if cart == {}:
            return render(request, 'core/empty_cart_error.html')
        objects = models.Product.objects.filter(id__in=list(cart.keys()))
        cart_objects = {}
        for id, count in cart.items():
            obj = objects.get(id=id)
            cart_objects[id] = {
                'obj': obj,
                'count': count,
                'price': obj.price * count * (1 - obj.discount / 100)
            }
        return render(request, 'core/checkout.html', {
            'form': form,
            'total': get_cart_total_price(cart),
            'cart': cart_objects
        })

    def post(self, request):
        form = forms.InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            try:
                invoice.user = request.user
            except ValueError:
                return redirect(reverse('login'))
            cart = get_cart(request)
            invoice.total = get_cart_total_price(cart)
            invoice.save()

            items = models.Product.objects.filter(id__in=list(cart.keys()))
            item_objects = []
            for item_id, item_count in cart.items():
                obj = items.get(id=item_id)
                invoice_item_obj = models.InvoiceItem(
                    invoice=invoice,
                    product=obj,
                    count=item_count,
                    discount=obj.discount,
                    price=obj.price,
                    name=obj.name,
                    total=obj.price * item_count * (1 - obj.discount / 100)
                )
                item_objects.append(invoice_item_obj)
            models.InvoiceItem.objects.bulk_create(item_objects)
            request.session['cart'] = {}

            payment = models.Payment(
                total=invoice.total - invoice.total * invoice.discount + invoice.total * invoice.vat,
                description='خرید از سایت ما',
                user_ip=get_user_ip(request),
                invoice=invoice
            )
            payment.save()

            # ==========================
            # 🔹 تنظیمات زرین‌پال Sandbox REST API
            # ==========================
            merchant_id = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            # شناسه مرچنت sandbox
            callback_url = "http://" + str(get_current_site(request).domain) + reverse('shop:verify')
            phone = getattr(invoice.user, "phone", "")
            mobile = ''.join(filter(str.isdigit, str(phone))) if phone else "0000000000"
            email = str(getattr(invoice.user, "email", "noemail@example.com"))
            req_data = {
                "merchant_id": merchant_id,
                "amount": round(payment.total),
                "callback_url": callback_url,
                "description": payment.description,
                "metadata": {"email": str(invoice.user.email), "mobile": mobile}
            }

            res = requests.post(
                url="https://sandbox.zarinpal.com/pg/v4/payment/request.json",
                json=req_data,
                headers={"accept": "application/json", "content-type": "application/json"}
            )

            data = res.json()

            if data.get('data') and data['data'].get('code') == 100:
                authority = data['data']['authority']
                payment.authority = authority
                payment.save()
                return redirect(f"https://sandbox.zarinpal.com/pg/StartPay/{authority}")
            else:

                return HttpResponse(f"❌ خطا در اتصال به درگاه پرداخت: {data.get('errors', {}).get('message', '')}")

        return render(request, 'core/checkout.html', {'form': form})




class VerifyView(LoginRequiredMixin ,View):
    def get(self, request):
        status = request.GET.get('Status')
        authority = request.GET.get('Authority')

        
        if status != 'OK':
            return render(request, 'core/payment_failed.html', {
                'error': 'پرداخت لغو شد یا کاربر منصرف شد.'
            })

        try:
            payment = models.Payment.objects.get(
                authority=authority,
                status=models.Payment.STATUS_PENDING
            )
        except models.Payment.DoesNotExist:
            return render(request, 'core/payment_failed.html', {
                'error': 'تراکنش یافت نشد.'
            })

        # ==========================
        # 🔹 مرحله تایید پرداخت (REST API)
        # ==========================
        merchant_id = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # ← مرچنت آی‌دی خودت
        verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        req_data = {
            "merchant_id": merchant_id,
            "amount": round(payment.total),
            "authority": authority
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        try:
            res = requests.post(verify_url, json=req_data, headers=headers)
            data = res.json()
        except Exception as e:
            payment.status = models.Payment.STATUS_ERROR
            payment.save()
            return render(request, 'core/payment_failed.html', {
                'error': f'خطا در ارتباط با زرین‌پال: {e}'
            })

        # ==========================
        # 🔹 بررسی پاسخ زرین‌پال
        # ==========================
        result = data.get('data', {})
        code = result.get('code')

        if code == 100:
            # ✅ پرداخت موفق
            ref_id = str(result.get('ref_id'))
            payment.ref = ref_id
            payment.status = models.Payment.STATUS_DONE
            payment.save()
            return render(request, 'core/payment_done.html', {'refid': ref_id})

        elif code == 101:
            # ⚠️ پرداخت قبلاً تایید شده
            payment.status = models.Payment.STATUS_DONE
            payment.save()
            return render(request, 'core/payment_done.html', {
                'refid': payment.ref,
                'message': 'این تراکنش قبلاً تایید شده بود.'
            })

        else:
            # ❌ پرداخت ناموفق
            payment.status = models.Payment.STATUS_ERROR
            payment.save()
            error_msg = data.get('errors', {}).get('message', 'پرداخت ناموفق بود.')
            return render(request, 'core/payment_failed.html', {'error': error_msg})


# class VerifyView(View):
#     def get(self, request):
#         status = request.GET.get('Status')
#         authority = request.GET.get('Authority')
#         if status == 'OK':
#             try:
#                 payment = models.Payment.objects.get(models.Payment, authority=authority, status=models.Payment.STATUS_PENDING)
#                 res = zarinpal.service.PaymentVerification(mid, authority, payment.total)
#                 if res.Status == 100:
#                     refid = str(res.Refid)
#                     payment.ref = refid
#                     payment.status = models.Payment.STATUS_DONE
#                     payment.save()
#                     return render(request, 'core/payment_done.html',{'refid': refid})
#                 elif res.Status == 101:
#                     return render(request, 'core/payment_failed.html')
#                 else:
#                     payment.status = models.Payment.STATUS_ERROR
#                     payment.save()
#                     return render(request, 'core/payment_failed.html')
#             except models.Payment.DoesNotExist:
#                 return render(request, 'core/payment_failed.html')
#
#         else:
#             return render(request, 'core/payment_failed.html')



def get_user_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if not ip:
        ip = request.META.get('REMOTE_ADDR')
    return ip




def decrease_from_cart(cart, obj):
    id = str(obj.id)
    if id in cart:
        if cart[id] > 1:
            cart[id] -= 1
        else:
            del cart[id]


class DecreaseFromCartView(View):
    def get(self, request, id):
        obj = get_object_or_404(models.Product, id=id)
        cart = get_cart(request)

        decrease_from_cart(cart, obj)
        request.session['cart'] = cart

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'total': get_cart_total_price(cart),
                'cart': cart
            })

        return HttpResponseRedirect(reverse('shop:cart_detail'))









