from django.shortcuts import render

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Farmer,Farm,District,Sector,Crop,PlantingRecord,AgriculturalInput
from .forms import AgriculturalInputForm, FarmerForm,FarmForm,CropForm, PlantingRecordForm,PlantingInput,PlantingInputForm
from django.db.models import Q, ProtectedError


# def farmer_list(request):
#     farmers = Farmer.objects.all()

#     return render(
#         request,
#         "farmer_management/farmer_list.html",
#         {"farmers": farmers},
# )



def farmer_list(request):
    query = request.GET.get('q', '').strip()

    farmers = Farmer.objects.all()

    if query:
        farmers = farmers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    context = {
        'farmers': farmers,
    }
    

    return render(request, 'farmer_management/farmer_list.html', context)


def farmer_create(request):
    form = FarmerForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        farmer = form.save(commit=False)

        if request.user.is_authenticated:
            farmer.created_by = request.user
            farmer.created_by_username = request.user.get_username()

        farmer.save()

        messages.success(request, "Farmer registered successfully.")
        return redirect("farmer_list")

    return render(
        request,
        "farmer_management/farmer_form.html",
        {"form": form, "title": "Register Farmer"},
    )


def farmer_detail(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)

    return render(
        request,
        "farmer_management/farmer_detail.html",
        {"farmer": farmer},
    )


def farmer_update(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)
    form = FarmerForm(request.POST or None, instance=farmer)

    if request.method == "POST" and form.is_valid():
        farmer = form.save(commit=False)

        if request.user.is_authenticated:
            farmer.updated_by = request.user
            farmer.updated_by_username = request.user.get_username()

        farmer.save()

        messages.success(request, "Farmer updated successfully.")
        return redirect("farmer_list")

    return render(
        request,
        "farmer_management/farmer_form.html",
        {"form": form, "title": "Edit Farmer"},
    )


def farmer_delete(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)

    if request.method == "POST":
        farmer.delete()
        messages.success(request, "Farmer deleted successfully.")
        return redirect("farmer_list")

    return redirect("farmer_list")



# Farms views

def farm_list(request):
    query = request.GET.get("q", "").strip()

    farms = Farm.objects.select_related(
        "farmer",
        "district",
        "sector",
    )

    if query:
        farms = farms.filter(
            Q(farm_name__icontains=query)
            | Q(farmer__first_name__icontains=query)
            | Q(farmer__last_name__icontains=query)
            | Q(district__name__icontains=query)
            | Q(sector__name__icontains=query)
        )

    context = {
        "farms": farms,
        "query": query,
        "total_farms": Farm.objects.count(),
        "active_farms": Farm.objects.filter(
            status=Farm.Status.ACTIVE
        ).count(),
        "inactive_farms": Farm.objects.filter(
            status=Farm.Status.INACTIVE
        ).count(),
    }

    return render(request, "farmer_management/farm_list.html", context)


def farm_create(request):
    form = FarmForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        farm = form.save(commit=False)

        if request.user.is_authenticated:
            farm.created_by = request.user
            farm.created_by_username = request.user.get_username()

        farm.save()
        messages.success(request, "Farm registered successfully.")
        return redirect("farm_list")

    return render(
        request,
        "farmer_management/farm_form.html",
        {"form": form, "title": "Register Farm"},
    )


def farm_detail(request, pk):
    farm = get_object_or_404(
        Farm.objects.select_related("farmer"),
        pk=pk,
    )

    return render(
        request,
        "farmer_management/farm_detail.html",
        {"farm": farm},
    )


def farm_update(request, pk):
    farm = get_object_or_404(Farm, pk=pk)
    form = FarmForm(request.POST or None, instance=farm)

    if request.method == "POST" and form.is_valid():
        farm = form.save(commit=False)

        if request.user.is_authenticated:
            farm.updated_by = request.user
            farm.updated_by_username = request.user.get_username()

        farm.save()
        messages.success(request, "Farm updated successfully.")
        return redirect("farm_list")

    return render(
        request,
        "farmer_management/farm_form.html",
        {"form": form, "title": "Edit Farm"},
    )


def farm_delete(request, pk):
    farm = get_object_or_404(Farm, pk=pk)

    if request.method == "POST":
        farm.delete()
        messages.success(request, "Farm deleted successfully.")
        return redirect("farm_list")

    return render(
        request,
        "farmer_management/farm_confirm_delete.html",
        {"farm": farm},
    )


def get_sectors(request):
    district_id = request.GET.get("district_id")

    if not district_id:
        return JsonResponse({"sectors": []})

    district = get_object_or_404(District, pk=district_id)

    sectors = Sector.objects.filter(
        district=district
    ).order_by("name").values("id", "name")

    return JsonResponse({"sectors": list(sectors)})


#Crop Views 

def crop_list(request):
    search = request.GET.get("search", "").strip()

    crops = Crop.objects.all()

    if search:
        crops = crops.filter(
            Q(crop_name__icontains=search)
            | Q(crop_category__icontains=search)
            | Q(description__icontains=search)
        )

    context = {
        "crops": crops,
        "search": search,
        "total_crops": Crop.objects.count(),
        "active_crops": Crop.objects.filter(is_active=True).count(),
        "inactive_crops": Crop.objects.filter(is_active=False).count(),
    }

    return render(request, "farmer_management/crop_list.html", context)


def crop_create(request):
    if request.method == "POST":
        form = CropForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Crop registered successfully.")
            return redirect("crop_list")
    else:
        form = CropForm()

    return render(
        request,
        "farmer_management/crop_form.html",
        {
            "form": form,
            "page_title": "Register Crop",
            "button_text": "Save Crop",
        },
    )

def crop_detail(request, pk):
    crop = get_object_or_404(Crop, pk=pk)

    return render(
        request,
        "farmer_management/crop_detail.html",
        {"crop": crop},
    )

def crop_update(request, pk):
    crop = get_object_or_404(Crop, pk=pk)

    if request.method == "POST":
        form = CropForm(request.POST, instance=crop)

        if form.is_valid():
            form.save()
            messages.success(request, "Crop updated successfully.")
            return redirect("crop_list")
    else:
        form = CropForm(instance=crop)

    return render(
        request,
        "farmer_management/crop_form.html",
        {
            "form": form,
            "crop": crop,
            "page_title": "Update Crop",
            "button_text": "Update Crop",
        },
    )


def crop_delete(request, pk):
    crop = get_object_or_404(Crop, pk=pk)

    if PlantingRecord.objects.filter(crop=crop).exists():
        messages.error(
            request,
            "This crop cannot be deleted because it is used in planting records.",
        )
    else:
        crop.delete()
        messages.success(request, "Crop deleted successfully.")

    return redirect("crop_list")


#Agricultural Input Views

def agricultural_input_list(request):
    search = request.GET.get("search", "").strip()
    selected_type = request.GET.get("input_type", "").strip()
    status = request.GET.get("status", "").strip()

    inputs = AgriculturalInput.objects.all()

    if search:
        inputs = inputs.filter(
            Q(input_name__icontains=search)
            | Q(input_type__icontains=search)
            | Q(unit_of_measure__icontains=search)
            | Q(description__icontains=search)
        )

    if selected_type in AgriculturalInput.InputType.values:
        inputs = inputs.filter(input_type=selected_type)

    if status in AgriculturalInput.Status.values:
        inputs = inputs.filter(status=status)

    context = {
        "agricultural_inputs": inputs,
        "search": search,
        "selected_type": selected_type,
        "status": status,
        "input_types": AgriculturalInput.InputType.choices,
        "total_inputs": AgriculturalInput.objects.count(),
        "active_inputs": AgriculturalInput.objects.filter(
            status="ACTIVE"
        ).count(),
        "inactive_inputs": AgriculturalInput.objects.filter(
            status="INACTIVE"
        ).count(),
    }

    return render(
        request,
        "farmer_management/agricultural_input_list.html",
        context,
    )


def agricultural_input_create(request):
    if request.method == "POST":
        form = AgriculturalInputForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Agricultural input registered successfully.",
            )
            return redirect("agricultural_input_list")
    else:
        form = AgriculturalInputForm()

    return render(
        request,
        "farmer_management/agricultural_input_form.html",
        {
            "form": form,
            "page_title": "Register Agricultural Input",
            "button_text": "Register Input",
        },
    )


def agricultural_input_detail(request, pk):
    agricultural_input = get_object_or_404(
        AgriculturalInput,
        pk=pk,
    )

    return render(
        request,
        "farmer_management/agricultural_input_detail.html",
        {"agricultural_input": agricultural_input},
    )


def agricultural_input_update(request, pk):
    agricultural_input = get_object_or_404(
        AgriculturalInput,
        pk=pk,
    )

    if request.method == "POST":
        form = AgriculturalInputForm(
            request.POST,
            instance=agricultural_input,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Agricultural input updated successfully.",
            )
            return redirect("agricultural_input_list")
    else:
        form = AgriculturalInputForm(instance=agricultural_input)

    return render(
        request,
        "farmer_management/agricultural_input_form.html",
        {
            "form": form,
            "agricultural_input": agricultural_input,
            "page_title": "Update Agricultural Input",
            "button_text": "Update Input",
        },
    )

def agricultural_input_delete(request, pk):
    agricultural_input = get_object_or_404(
        AgriculturalInput,
        pk=pk,
    )

    try:
        agricultural_input.delete()
    except ProtectedError:
        messages.error(
            request,
            "Cannot delete this agricultural input because "
            "it is being used by another record.",
        )
    else:
        messages.success(
            request,
            "Agricultural input deleted successfully.",
        )

    return redirect("agricultural_input_list")


# Planting Record Views

def planting_record_list(request):
    search = request.GET.get("search", "").strip()
    farm_id = request.GET.get("farm", "").strip()
    crop_id = request.GET.get("crop", "").strip()
    selected_status = request.GET.get("status", "").strip()

    records = PlantingRecord.objects.select_related(
        "farm",
        "crop",
    )

    if search:
        records = records.filter(
            Q(farm__farm_name__icontains=search)
            | Q(crop__crop_name__icontains=search)
            | Q(status__icontains=search)
        )

    if farm_id:
        records = records.filter(farm_id=farm_id)

    if crop_id:
        records = records.filter(crop_id=crop_id)

    if selected_status in PlantingRecord.Status.values:
        records = records.filter(status=selected_status)

    context = {
        "planting_records": records,
        "search": search,
        "selected_farm": farm_id,
        "selected_crop": crop_id,
        "selected_status": selected_status,
        "farms": Farm.objects.all(),
        "crops": Crop.objects.all(),
        "statuses": PlantingRecord.Status.choices,
        "total_records": PlantingRecord.objects.count(),
        "planned_records": PlantingRecord.objects.filter(
            status="PLANNED"
        ).count(),
        "growing_records": PlantingRecord.objects.filter(
            status="GROWING"
        ).count(),
        "harvested_records": PlantingRecord.objects.filter(
            status="HARVESTED"
        ).count(),
    }

    return render(
        request,
        "farmer_management/planting_record_list.html",
        context,
    )


def planting_record_create(request):
    if request.method == "POST":
        form = PlantingRecordForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Planting record registered successfully.",
            )
            return redirect("planting_record_list")
    else:
        form = PlantingRecordForm()

    return render(
        request,
        "farmer_management/planting_record_form.html",
        {
            "form": form,
            "page_title": "Register Planting Record",
            "button_text": "Register Planting",
        },
    )

def planting_record_detail(request, pk):
    planting_record = get_object_or_404(
        PlantingRecord.objects.select_related("farm", "crop"),
        pk=pk,
    )

    return render(
        request,
        "farmer_management/planting_record_detail.html",
        {
            "planting_record": planting_record,
        },
    )


def planting_record_update(request, pk):
    planting_record = get_object_or_404(
        PlantingRecord,
        pk=pk,
    )

    if request.method == "POST":
        form = PlantingRecordForm(
            request.POST,
            instance=planting_record,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Planting record updated successfully.",
            )
            return redirect("planting_record_list")
    else:
        form = PlantingRecordForm(instance=planting_record)

    return render(
        request,
        "farmer_management/planting_record_form.html",
        {
            "form": form,
            "planting_record": planting_record,
            "page_title": "Update Planting Record",
            "button_text": "Update Planting",
        },
    )


def planting_record_delete(request, pk):
    planting_record = get_object_or_404(
        PlantingRecord,
        pk=pk,
    )

    try:
        planting_record.delete()
    except ProtectedError:
        messages.error(
            request,
            "This planting record cannot be deleted because "
            "it is being used by another record.",
        )
    else:
        messages.success(
            request,
            "Planting record deleted successfully.",
        )

    return redirect("planting_record_list")


# Planting Input Views

def planting_input_list(request):
    search = request.GET.get("search", "").strip()

    records = PlantingInput.objects.select_related(
        "planting__farm",
        "planting__crop",
        "agricultural_input",
    ).all()

    if search:
        records = records.filter(
            Q(agricultural_input__input_name__icontains=search)
            | Q(planting__farm__farm_name__icontains=search)
            | Q(planting__crop__crop_name__icontains=search)
        )

    context = {
        "planting_inputs": records,
        "search": search,
        "total_records": PlantingInput.objects.count(),
    }

    return render(
        request,
        "farmer_management/planting_input_list.html",
        context,
    )

def planting_input_create(request):
    if request.method == "POST":
        form = PlantingInputForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Planting input recorded successfully.",
            )
            return redirect("planting_input_list")
    else:
        form = PlantingInputForm()

    return render(
        request,
        "farmer_management/planting_input_form.html",
        {
            "form": form,
            "page_title": "Record Agricultural Input Usage",
            "button_text": "Save Planting Input",
        },
    )


def planting_input_detail(request, pk):
    planting_input = get_object_or_404(
        PlantingInput.objects.select_related(
            "planting__farm",
            "planting__crop",
            "agricultural_input",
        ),
        pk=pk,
    )

    return render(
        request,
        "farmer_management/planting_input_detail.html",
        {
            "planting_input": planting_input,
        },
    )

def planting_input_update(request, pk):
    planting_input = get_object_or_404(
        PlantingInput,
        pk=pk,
    )

    if request.method == "POST":
        form = PlantingInputForm(
            request.POST,
            instance=planting_input,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Planting input updated successfully.",
            )
            return redirect("planting_input_list")
    else:
        form = PlantingInputForm(instance=planting_input)

    return render(
        request,
        "farmer_management/planting_input_form.html",
        {
            "form": form,
            "planting_input": planting_input,
            "page_title": "Update Planting Input",
            "button_text": "Update Planting Input",
        },
    )

def planting_input_delete(request, pk):
    planting_input = get_object_or_404(
        PlantingInput,
        pk=pk,
    )

    try:
        planting_input.delete()
    except ProtectedError:
        messages.error(
            request,
            "This planting input cannot be deleted because "
            "another record depends on it.",
        )
    else:
        messages.success(
            request,
            "Planting input deleted successfully.",
        )

    return redirect("planting_input_list")