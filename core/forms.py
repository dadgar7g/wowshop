from django import forms
from .models import Coach, FastSell, BuyGold
class CoachForm(forms.ModelForm):
    class Meta:
        model = Coach
        fields = ['expansions', 'methods', 'description', 'timeplay']

        widgets = {
            'expansions': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'methods': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'timeplay': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'expansions': 'اکسپنشن‌ها',
            'methods': 'نوع فعالیت',
            'description': 'توضیحات',
            'timeplay': 'تایم پلی (ماه)',
        }

class FastSellForm(forms.ModelForm):
    class Meta:
        model = FastSell
        fields = ['text']
        widgets = {
            'text': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'پیام خود را وارد کنید...'}),
        }


class BuyGold(forms.ModelForm):
    class Meta:
        model = BuyGold
        exclude = ['user', 'created_at',]

        widgets = {
            'character_name': forms.TextInput(attrs={'class': 'form-control'}),
            'expansions': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'methods': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),


        }

        labels = {
            'character_name': 'نام کاراکتر',
            'expansions': 'اکسپنشن‌ها',
            'methods': 'نوع فعالیت',
            'description': 'توضیحات',

        }

