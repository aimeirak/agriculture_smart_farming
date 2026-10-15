from django import forms
from .models import Farmer,Farm,District,Sector

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

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = [
            "farm_name",
            "farmer",
            "district",
            "sector",
            "area_hectares",
            "status",
        ]

        widgets = {
            "farm_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter farm name",
            }),
            "farmer": forms.Select(attrs={"class": "form-select"}),
            "district": forms.Select(attrs={"class": "form-select"}),
            "sector": forms.Select(attrs={"class": "form-select"}),
            "area_hectares": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter area in hectares",
                "min": "0.01",
                "step": "0.01",
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["farmer"].queryset = Farmer.objects.order_by("first_name", "last_name")
        self.fields["district"].queryset = District.objects.order_by("name")
        self.fields["sector"].queryset = Sector.objects.select_related(
            "district"
        ).order_by("district__name", "name")

    def clean(self):
        cleaned_data = super().clean()
        district = cleaned_data.get("district")
        sector = cleaned_data.get("sector")
        area = cleaned_data.get("area_hectares")

        if district and sector and sector.district_id != district.id:
            self.add_error(
                "sector",
                "Please select a sector belonging to the chosen district.",
            )

        if area is not None and area <= 0:
            self.add_error("area_hectares", "Area must be greater than zero.")

        return cleaned_data