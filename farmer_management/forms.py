from django import forms
from .models import Farmer,Farm

class FarmerForm(forms.ModelForm):
    class Meta:
        model = Farmer
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "status",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "status": forms.Select(
                attrs={"class": "form-control"}
            ),
        }



class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = [
            "farmer",
            "farm_name",
            "district",
            "sector",
            "area_hectares",
            "status",
        ]

        widgets = {
            "farmer": forms.Select(
                attrs={"class": "form-control"}
            ),
            "farm_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "district": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "sector": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "area_hectares": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-control"}
            ),
        }