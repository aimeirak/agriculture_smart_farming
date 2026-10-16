from django import forms
from .models import Farmer,Farm,District,Sector, Crop,AgriculturalInput,PlantingRecord,PlantingInput

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


#Crop Model Form
class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = [
            "crop_name",
            "crop_category",
            "description",
            "is_active",
        ]

        widgets = {
            "crop_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter crop name",
                "autofocus": True,
            }),
            "crop_category": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter crop description (optional)",
                "rows": 4,
            }),
           "is_active": forms.Select(
                choices=[
                    (True, "Active"),
                    (False, "Inactive"),
                ],
                attrs={
                    "class": "form-select",
                },
            ),
        }

        labels = {
            "crop_name": "Crop Name",
            "crop_category": "Crop Category",
            "description": "Description",
            "is_active": "Active Crop",
        }

        help_texts = {
            "crop_name": "Enter a unique name for this crop.",
            "crop_category": "Select the appropriate crop category.",
            "description": "Provide additional information if needed.",
            "is_active": "Inactive crops will not be available for new selections if your views enforce this rule.",
        }

    def clean_crop_name(self):
        crop_name = self.cleaned_data["crop_name"].strip()

        if not crop_name:
            raise forms.ValidationError("Crop name is required.")

        return crop_name



class AgriculturalInputForm(forms.ModelForm):
    class Meta:
        model = AgriculturalInput
        fields = [
            "input_name",
            "input_type",
            "unit_of_measure",
            "description",
            "status",
        ]

        widgets = {
            "input_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter input name",
            }),
            "input_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "unit_of_measure": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. kg, litre, packet",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter description (optional)",
                "rows": 4,
            }),
            "status": forms.Select(
                choices=[
                    ("ACTIVE", "Active"),
                    ("INACTIVE", "Inactive"),
                ],
                attrs={"class": "form-select"},
            ),
        }

        labels = {
            "input_name": "Input Name",
            "input_type": "Input Type",
            "unit_of_measure": "Unit of Measure",
            "description": "Description",
            "status": "Status",
        }

    def clean_input_name(self):
        input_name = self.cleaned_data["input_name"].strip()

        if not input_name:
            raise forms.ValidationError("Input name is required.")

        return input_name



# planting Record Form
class PlantingRecordForm(forms.ModelForm):
    class Meta:
        model = PlantingRecord

        fields = [
            "farm",
            "crop",
            "planting_date",
            "expected_harvest_date",
            "season",
            "area_planted_hectares",
            "quantity_planted",
            "quantity_unit",
            "status",
            "notes",
        ]

        widgets = {
            "farm": forms.Select(attrs={"class": "form-select"}),
            "crop": forms.Select(attrs={"class": "form-select"}),
            "planting_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "expected_harvest_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "season": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Season A 2026",
            }),
            "area_planted_hectares": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter planted area in hectares",
                "min": "0.01",
                "step": "0.01",
            }),
            "quantity_planted": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter quantity planted",
                "min": "0.01",
                "step": "0.01",
            }),
            "quantity_unit": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. kg, seeds, seedlings",
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Additional notes (optional)",
                "rows": 4,
            }),
        }

        labels = {
            "farm": "Farm",
            "crop": "Crop",
            "planting_date": "Planting Date",
            "expected_harvest_date": "Expected Harvest Date",
            "season": "Growing Season",
            "area_planted_hectares": "Area Planted (hectares)",
            "quantity_planted": "Quantity Planted",
            "quantity_unit": "Quantity Unit",
            "status": "Planting Status",
            "notes": "Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["farm"].queryset = Farm.objects.all()
        self.fields["crop"].queryset = Crop.objects.all()

        self.fields["farm"].empty_label = "Select a farm"
        self.fields["crop"].empty_label = "Select a crop"

        self.fields["area_planted_hectares"].help_text = (
            "Must not exceed the total area of the selected farm."
        )

        self.fields["quantity_planted"].required = False
        self.fields["quantity_unit"].required = False
        self.fields["notes"].required = False

        if not self.instance.pk and not self.initial.get("quantity_unit"):
            self.initial["quantity_unit"] = "kg"



# planting Input Form
class PlantingInputForm(forms.ModelForm):
    class Meta:
        model = PlantingInput

        fields = [
            "planting",
            "agricultural_input",
            "quantity_used",
            "application_date",
            "notes",
        ]

        widgets = {
            "planting": forms.Select(attrs={
                "class": "form-select",
            }),
            "agricultural_input": forms.Select(attrs={
                "class": "form-select",
            }),
            "quantity_used": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter quantity used",
                "min": "0.001",
                "step": "0.001",
            }),
            "application_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Additional application details (optional)",
                "rows": 4,
            }),
        }

        labels = {
            "planting": "Planting Record",
            "agricultural_input": "Agricultural Input",
            "quantity_used": "Quantity Used",
            "application_date": "Application Date",
            "notes": "Additional Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["planting"].queryset = (
            PlantingRecord.objects.select_related("farm", "crop").all()
        )

        self.fields["agricultural_input"].queryset = (
            AgriculturalInput.objects.all()
        )

        self.fields["planting"].empty_label = (
            "Select a planting record"
        )
        self.fields["agricultural_input"].empty_label = (
            "Select an agricultural input"
        )

        self.fields["notes"].required = False

    def clean_quantity_used(self):
        quantity = self.cleaned_data.get("quantity_used")

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError(
                "Quantity used must be greater than zero."
            )

        return quantity