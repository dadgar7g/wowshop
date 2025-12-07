from django.contrib import admin
from . import models
# Register your models here.
# -------------------------------------------------------------------------------------------------
class OrderAdmin(admin.ModelAdmin):
    list_display = ['title', 'buyer', 'show_offers', 'show_expansions', 'show_realms', 'faction', 'region', 'status', 'amount', 'rest']
    list_filter = ['status', 'faction', 'region', 'expansion', 'realm', 'title']
    search_fields = ['title', 'buyer']
    list_editable = ['status', 'amount', 'rest']

    filter_horizontal = ['expansion', 'realm']


    def show_offers(self, obj):
        offers = obj.offers.all()
        if not offers:
            return "-"
        return " | ".join([f"{o.seller.username} ({o.quantity})" for o in offers])

    show_offers.short_description = "Offerها"

    def show_expansions(self, obj):
        return "، ".join([ex.name for ex in obj.expansion.all()])
    show_expansions.short_description = "Expansion"

    def show_realms(self, obj):
        return "، ".join([rl.name for rl in obj.realm.all()])
    show_realms.short_description = "Realm"
admin.site.register(models.Order, OrderAdmin)

# -------------------------------------------------------------------------------------------------
class OfferAdmin(admin.ModelAdmin):
    list_display = ['order__title', 'seller', 'quantity', 'total_price', 'status']
    list_filter = ['status', 'order__expansion', 'order__realm',]
    search_fields = ['order__title', 'seller', 'order__buyer']
    list_editable = ['status']

admin.site.register(models.Offer, OfferAdmin)

# -------------------------------------------------------------------------------------------------
class ExpansionAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(models.Expansion, ExpansionAdmin)

# -------------------------------------------------------------------------------------------------
class RealmAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(models.Realm, RealmAdmin)

# -------------------------------------------------------------------------------------------------
class MethodAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(models.Method, MethodAdmin)

# -------------------------------------------------------------------------------------------------
@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'coach', 'text', 'enable', 'created_at']
    list_editable = ['enable']
    list_filter = ['enable', 'coach']
    search_fields = ['user__username', 'text', 'coach__user__username']
    readonly_fields = ['created_at']
class CommentInline(admin.TabularInline):
    model = models.Comment
    extra = 0
    fields = ('user', 'text', 'enable', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# -------------------------------------------------------------------------------------------------
from django.contrib import admin
from .models import FastSell
@admin.register(FastSell)
class FastSellAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'discord_id',
        'phone_number',
        'created_at',

    )

    def discord_id(self, obj):
        return obj.user.discord_id
    discord_id.short_description = "Discord ID"

    def phone_number(self, obj):
        return obj.user.phone
    phone_number.short_description = "Phone Number"
# -------------------------------------------------------------------------------------------------
@admin.register(models.Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ['user', 'show_expansions', 'show_methods', 'timeplay']
    list_filter = ['expansions', 'methods']
    search_fields = ['user__username']
    inlines = [CommentInline]

    def show_expansions(self, obj):
        return "، ".join([ex.name for ex in obj.expansions.all()])
    show_expansions.short_description = "Expansion"

    def show_methods(self, obj):
        return "، ".join([mt.name for mt in obj.methods.all()])
    show_methods.short_description = "Methods"

# -------------------------------------------------------------------------------------------------

