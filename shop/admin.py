from django.contrib import admin
from . import models
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.
class ShopCommentInline(admin.TabularInline):
    model = models.ShopComment
    extra = 0
    fields = ('user', 'text', 'enable', 'created_at')
    readonly_fields = ('created_at', 'user', 'text',)
    ordering = ('-created_at',)
class ShopCommentAdmin(admin.ModelAdmin):
    list_display = ['user__username', 'text', 'product', 'enable']
    list_editable = ['enable']
    list_filter = ['enable']
    search_fields = ['user__username', 'text']
admin.site.register(models.ShopComment, ShopCommentAdmin)
#-------------------------------------------------------------------------------------------------
class InvoiceItemInline(admin.TabularInline):
    model = models.InvoiceItem
    extra = 0
    readonly_fields = ['product']  # ریدانلی
    fields = ['product', 'count', 'price', 'discount', 'total',]

#-------------------------------------------------------------------------------------------------
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'count', 'price', 'category', 'enabled']
    list_editable = ['count', 'enabled']
    search_fields = ['name']
    list_filter = ['category','enabled','discount',]
    inlines = [ShopCommentInline]



admin.site.register(models.Product, ProductAdmin)

#-------------------------------------------------------------------------------------------------
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    search_fields = ['name']


admin.site.register(models.Category, CategoryAdmin)

#-------------------------------------------------------------------------------------------------
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = ['__str__', 'user', 'battle_tag', 'total', 'date', 'payment__status', 'payment__ref',]
    list_filter = ['payment__status', 'user',]
    search_fields = ['user', 'battle_tag', 'payment__ref',]

admin.site.register(models.Invoice, InvoiceAdmin)

#-------------------------------------------------------------------------------------------------

# class ShopCommentAdmin(admin.ModelAdmin):
#     list_display = ['user__username', 'text', 'show_products', 'enable']
#     list_editable = ['enable']
#     list_filter = ['enable']
#     search_fields = ['user__username', 'text']
#
#     def show_products(self, obj):
#         products = models.Product.objects.filter(comments=obj)
#
#         if not products:
#             return "-"
#
#         links = []
#         for p in products:
#             url = reverse('admin:shop_product_change', args=[p.id])
#             links.append(f'<a href="{url}" target="_blank">{p.name}</a>')
#
#         return format_html(", ".join(links))
#
#     show_products.short_description = "محصول مرتبط"
#
#
# admin.site.register(models.ShopComment, ShopCommentAdmin)


#-------------------------------------------------------------------------------------------------
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['__str__','status', 'ref', 'total']
    list_filter = ['status']
    search_fields = ['ref']
    list_editable = ['status']
    readonly_fields = ['ref', 'total', 'invoice', 'authority', 'description', 'user_ip']

admin.site.register(models.Payment, PaymentAdmin)

#-------------------------------------------------------------------------------------------------















