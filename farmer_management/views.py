from django.shortcuts import render

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Farmer,Farm,District,Sector
from .forms import FarmerForm,FarmForm
from django.db.models import Q


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

