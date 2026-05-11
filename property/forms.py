from django import forms
from .models import UserRegister, BuyerListing, TenantListing
class BuyerListingForm(forms.ModelForm):
    class Meta:
        model = BuyerListing
        fields = '__all__'


class TenantListingForm(forms.ModelForm):
    class Meta:
        model = TenantListing
        fields = '__all__'