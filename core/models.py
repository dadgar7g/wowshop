import os
from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
def _get_avatar_upload_path(obj, filename):
    now = timezone.now()
    base_path = 'media'
    ext = os.path.splitext(filename)[1]
    new_filename = str(uuid.uuid5(uuid.NAMESPACE_URL, str(obj.pk)))
    path = os.path.join(base_path, now.strftime("%Y/%m"), f"{new_filename}{ext}")
    return path


from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class Expansion(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Method(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Realm(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name




class Order(models.Model):
    #------------------------------------------
    STATUS_CHOICES = [
        ('available', 'در دسترس'),
        ('Done', 'به اتمام رسیده'),
        ('cansel', 'لغو شده'),
        ('pending', 'در حال بررسی'),




    ]

    FACTION_CHOICES = [
        ('horde', 'Horde'),
        ('alliance', 'Alliance')
    ]


    REGION_CHOICES = [
        ('eu', 'EU'),
        ('us', 'US')
    ]
    # ------------------------------------------
    title = models.CharField('Title', max_length=255)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    buyer = models.CharField('Buyer', max_length=255)
    expansion = models.ManyToManyField(Expansion,)
    faction = models.CharField('Faction', max_length=255, choices=FACTION_CHOICES)
    realm = models.ManyToManyField(Realm,)
    region = models.CharField('Region', max_length=255, choices=REGION_CHOICES)
    min_reserve = models.IntegerField('Min. Reserve')
    price_per_1k = models.IntegerField('Price per 1k')
    amount = models.IntegerField('Amount')
    status = models.CharField('Status', max_length=255, choices=STATUS_CHOICES)
    rest = models.IntegerField('Rest', default=0)
    # price = models.IntegerField('Price')

    def __str__(self):
        return f"{self.title}"




class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار تکمیل'),
        ('review', 'در انتظار بررسی'),
        ('Awaiting_payment', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('nptapprove', 'تایید نشد')
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='offers')  # هر Offer به یک Order وصل است
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')  # فروشنده
    quantity = models.PositiveIntegerField()
    price_per_1k = models.IntegerField()
    total_price = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    proof = models.FileField(upload_to=_get_avatar_upload_path, null=True, blank=True)


    def __str__(self):
        return f"Offer by {self.seller.username} for {self.order.title}"




class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_comment')
    coach = models.ForeignKey('Coach', on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    enable = models.BooleanField(default=False)

class Coach(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    expansions = models.ManyToManyField(Expansion)
    methods = models.ManyToManyField(Method)
    description = models.TextField()
    timeplay = models.PositiveIntegerField()



class FastSell(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    text = models.TextField("متن پیام")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")

    def __str__(self):
        return f"پیام {self.user.username} در {self.created_at.strftime('%Y-%m-%d %H:%M')}"



class BuyGold(models.Model):
    FACTION_CHOICES = [
        ('horde', 'Horde'),
        ('alliance', 'Alliance')
    ]

    REGION_CHOICES = [
        ('eu', 'EU'),
        ('us', 'US')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    character_name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    expansion = models.ManyToManyField(Expansion, )
    faction = models.CharField('Faction', max_length=255, choices=FACTION_CHOICES)
    realm = models.ManyToManyField(Realm, )
    region = models.CharField('Region', max_length=255, choices=REGION_CHOICES)
    amount = models.IntegerField('Amount')

    def __str__(self):
        return f"پیام {self.user.username} در {self.created_at.strftime('%Y-%m-%d %H:%M')}"





