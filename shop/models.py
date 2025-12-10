from django.db import models
from django.utils.text import slugify
import uuid
# -------------------------------
# from django.contrib.auth.models import User
# from account.models import User
from django.contrib.auth import get_user_model

User = get_user_model()


# -------------------------------
# Create your models here.

class Base(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    create_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    deleted_date = models.DateTimeField(default=None, null=True, blank=True)
    deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class Product(Base):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    price = models.IntegerField(default=0)
    discount = models.FloatField(default=0)
    enabled = models.BooleanField(default=True)
    description = models.TextField()
    image = models.ImageField(upload_to='covers/', null=True, blank=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT,
        related_name='products'
    )
    count = models.IntegerField(default=0)

    # 🔥 حذف ManyToManyField
    # comments = models.ManyToManyField('ShopComment')

    def __str__(self):
        return f"{self.name}"
# class Product(Base):
#     # ------------------------------------------------
#     # STATUS_ENABLED = 0
#     # STATUS_DISABLED = 1
#     # STATUS_DELETED = 2
#     # STATUS_CHOICES = ((STATUS_ENABLED, 'Enabled'),
#     #                   (STATUS_DISABLED, 'Disabled'),
#     #                   (STATUS_DELETED, 'Deleted',))
#     # ------------------------------------------------
#     name = models.CharField(max_length=255)
#     slug = models.SlugField()
#     price = models.IntegerField(default=0)
#     discount = models.FloatField(default=0)
#     enabled = models.BooleanField(default=True)
#     description = models.TextField()
#     image = models.ImageField(upload_to='covers/', null=True, blank=True)
#     category = models.ForeignKey('Category', on_delete=models.PROTECT,
#                                  related_name='products', )
#     count = models.IntegerField(default=0)
#     comments = models.ManyToManyField('ShopComment')
#
#     # old_category = models.ForeignKey('Category', on_delete=models.PROTECT,
#     #                                  related_name='old_products',)
#     # status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ENABLED)
#
#     def __str__(self):
#         return f"{self.name}"




class ShopComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_comment')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    enable = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text}"
# class ShopComment(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_comment')
#     created_at = models.DateTimeField(auto_now_add=True)
#     text = models.TextField()
#     enable = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f"{self.text}"






class Category(Base):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('Category', null=True, blank=True, default=None,
                               on_delete=models.PROTECT,
                               related_name='child')

    def __str__(self):
        return f"{self.name}"


class InvoiceItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    count = models.IntegerField()
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE)
    price = models.IntegerField()
    discount = models.FloatField(default=0)
    name = models.CharField(max_length=255)
    total = models.IntegerField()


class Invoice(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    number = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.IntegerField()
    discount = models.FloatField(default=0)
    description = models.TextField(null=True, blank=True)
    battle_tag = models.CharField(max_length=255)
    vat = models.FloatField(default=0.09)

    def __str__(self):
        return f"{self.user.username} - Invoice={self.id}"


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = ((STATUS_PENDING, 'در انتظار پرداخت'),
                      (STATUS_ERROR, 'پرداخت ناموفق'),
                      (STATUS_DONE, 'پرداخت موفق'))

    invoice = models.OneToOneField(Invoice, on_delete=models.PROTECT)
    total = models.IntegerField()
    ref = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default=STATUS_PENDING)

    authority = models.CharField(max_length=255)
    description = models.TextField()
    user_ip = models.CharField(max_length=255)

    def __str__(self):
        return f"({self.invoice.user.username}), invoice {self.invoice.id}"



