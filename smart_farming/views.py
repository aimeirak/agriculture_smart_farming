
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from smart_farming.forms import IrrigationRecordForm, SensorDeviceForm, SensorReadingForm, WeatherRecordForm
from smart_farming.models import IrrigationRecord, SensorDevice, SensorReading, WeatherRecord
from django.db.models import Q, ProtectedError

# Create your views here.


def sensor_device_list(request):
    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_type = request.GET.get("device_type", "").strip()

    devices = SensorDevice.objects.select_related("farm").all()

    if search:
        devices = devices.filter(
            Q(device_code__icontains=search)
            | Q(farm__farm_name__icontains=search)
            | Q(device_type__icontains=search)
            | Q(status__icontains=search)
        )

    if selected_status in SensorDevice.Status.values:
        devices = devices.filter(status=selected_status)

    if selected_type in SensorDevice.DeviceType.values:
        devices = devices.filter(device_type=selected_type)

    context = {
        "sensor_devices": devices,
        "search": search,
        "selected_status": selected_status,
        "selected_type": selected_type,
        "statuses": SensorDevice.Status.choices,
        "device_types": SensorDevice.DeviceType.choices,
        "total_devices": SensorDevice.objects.count(),
        "active_devices": SensorDevice.objects.filter(
            status=SensorDevice.Status.ACTIVE
        ).count(),
        "inactive_devices": SensorDevice.objects.filter(
            status=SensorDevice.Status.INACTIVE
        ).count(),
        "maintenance_devices": SensorDevice.objects.filter(
            status=SensorDevice.Status.MAINTENANCE
        ).count(),
    }

    return render(
        request,
        "smart_farming/sensor_device_list.html",
        context,
    )


def sensor_device_create(request):
    if request.method == "POST":
        form = SensorDeviceForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Sensor device registered successfully."
            )

            return redirect("sensor_device_list")
    else:
        form = SensorDeviceForm()

    return render(
        request,
        "smart_farming/sensor_device_form.html",
        {
            "form": form,
            "page_title": "Register Sensor Device",
            "button_text": "Register Device",
        },
    )


def sensor_device_detail(request, pk):
    sensor_device = get_object_or_404(
        SensorDevice.objects.select_related("farm"),
        pk=pk,
    )

    return render(
        request,
        "smart_farming/sensor_device_detail.html",
        {
            "sensor_device": sensor_device,
        },
    )

def sensor_device_update(request, pk):
    sensor_device = get_object_or_404(
        SensorDevice,
        pk=pk,
    )

    if request.method == "POST":
        form = SensorDeviceForm(
            request.POST,
            instance=sensor_device,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Sensor device updated successfully.",
            )
            return redirect("sensor_device_list")
    else:
        form = SensorDeviceForm(instance=sensor_device)

    return render(
        request,
        "smart_farming/sensor_device_form.html",
        {
            "form": form,
            "sensor_device": sensor_device,
            "page_title": "Update Sensor Device",
            "button_text": "Update Device",
        },
    )


def sensor_device_delete(request, pk):
    sensor_device = get_object_or_404(
        SensorDevice,
        pk=pk,
    )

    try:
        sensor_device.delete()
    except ProtectedError:
        messages.error(
            request,
            "This sensor device cannot be deleted because "
            "it is referenced by another record.",
        )
    else:
        messages.success(
            request,
            "Sensor device deleted successfully.",
        )

    return redirect("sensor_device_list")



def sensor_reading_list(request):
    readings = SensorReading.objects.select_related(
        "device",
        "device__farm",
    )

    search = request.GET.get("search", "").strip()
    selected_device = request.GET.get("device", "").strip()

    if search:
        readings = readings.filter(
            Q(device__device_code__icontains=search)
            | Q(device__farm__farm_name__icontains=search)
        )

    if selected_device:
        readings = readings.filter(device_id=selected_device)

    context = {
        "sensor_readings": readings,
        "search": search,
        "selected_device": selected_device,
        "devices": SensorDevice.objects.select_related("farm").order_by(
            "device_code"
        ),
        "total_readings": readings.count(),
    }

    return render(request, "smart_farming/sensor_reading_list.html", context)




def sensor_reading_create(request):
    if request.method == "POST":
        form = SensorReadingForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Sensor reading recorded successfully.",
            )

            return redirect("sensor_reading_list")
    else:
        form = SensorReadingForm()

    return render(
        request,
        "smart_farming/sensor_reading_form.html",
        {
            "form": form,
            "page_title": "Record Sensor Reading",
            "button_text": "Save Reading",
        },
    )


def sensor_reading_detail(request, pk):
    sensor_reading = get_object_or_404(
        SensorReading.objects.select_related("device", "device__farm"),
        pk=pk,
    )

    return render(
        request,
        "smart_farming/sensor_reading_detail.html",
        {"sensor_reading": sensor_reading},
    )




def sensor_reading_update(request, pk):
    sensor_reading = get_object_or_404(SensorReading, pk=pk)

    if request.method == "POST":
        form = SensorReadingForm(
            request.POST,
            instance=sensor_reading,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Sensor reading updated successfully.",
            )

            return redirect("sensor_reading_detail", pk=sensor_reading.pk)
    else:
        form = SensorReadingForm(instance=sensor_reading)

    return render(
        request,
        "smart_farming/sensor_reading_form.html",
        {
            "form": form,
            "page_title": "Update Sensor Reading",
            "button_text": "Update Reading",
        },
    )

def sensor_reading_delete(request, pk):
    sensor_reading = get_object_or_404(SensorReading, pk=pk)
    try:
        sensor_reading.delete()

        messages.success(
            request,
            "Sensor reading deleted successfully.",
        )
    except ProtectedError:
        messages.error(
            request,
            "This reading cannot be deleted because it is referenced by other records.",
        )

    return redirect("sensor_reading_list")


# weather record views
def weather_record_list(request):
    records = WeatherRecord.objects.select_related("farm")

    search = request.GET.get("search", "").strip()
    selected_source = request.GET.get("source", "").strip()

    if search:
        records = records.filter(
            Q(farm__farm_name__icontains=search)
            | Q(source__icontains=search)
        )

    if selected_source:
        records = records.filter(source=selected_source)

    context = {
        "weather_records": records,
        "search": search,
        "selected_source": selected_source,
        "sources": WeatherRecord.Source.choices,
        "total_records": records.count(),
    }

    return render(
        request,
        "smart_farming/weather_record_list.html",
        context,
    )



def weather_record_create(request):
    if request.method == "POST":
        form = WeatherRecordForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Weather record created successfully.",
            )

            return redirect("weather_record_list")
    else:
        form = WeatherRecordForm()

    return render(
        request,
        "smart_farming/weather_record_form.html",
        {
            "form": form,
            "page_title": "Create Weather Record",
            "button_text": "Save Weather Record",
        },
    )


def weather_record_detail(request, pk):
    weather_record = get_object_or_404(
        WeatherRecord.objects.select_related("farm"),
        pk=pk,
    )

    return render(
        request,
        "smart_farming/weather_record_detail.html",
        {"weather_record": weather_record},
    )


def weather_record_update(request, pk):
    weather_record = get_object_or_404(
        WeatherRecord,
        pk=pk,
    )

    if request.method == "POST":
        form = WeatherRecordForm(
            request.POST,
            instance=weather_record,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Weather record updated successfully.",
            )

            return redirect(
                "weather_record_detail",
                pk=weather_record.pk,
            )
    else:
        form = WeatherRecordForm(instance=weather_record)

    return render(
        request,
        "smart_farming/weather_record_form.html",
        {
            "form": form,
            "page_title": "Update Weather Record",
            "button_text": "Update Weather Record",
        },
    )


def weather_record_delete(request, pk):
    weather_record = get_object_or_404(
        WeatherRecord,
        pk=pk,
    )

    try:
        weather_record.delete()

        messages.success(
            request,
            "Weather record deleted successfully.",
        )
    except ProtectedError:
        messages.error(
            request,
            "This weather record cannot be deleted because it is referenced by other records.",
        )

    return redirect("weather_record_list")

# Irrigation Record Views
def irrigation_record_list(request):
    irrigation_records = (
        IrrigationRecord.objects
        .select_related("farm", "planting", "planting__crop")
        .all()
    )

    search = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search:
        irrigation_records = irrigation_records.filter(
            Q(farm__farm_name__icontains=search)
            | Q(planting__crop__crop_name__icontains=search)
            | Q(method__icontains=search)
        )

    valid_statuses = dict(IrrigationRecord.Status.choices)

    if selected_status in valid_statuses:
        irrigation_records = irrigation_records.filter(
            status=selected_status
        )
    else:
        selected_status = ""

    context = {
        "irrigation_records": irrigation_records,
        "search": search,
        "selected_status": selected_status,
        "statuses": IrrigationRecord.Status.choices,
        "total_records": irrigation_records.count(),
    }

    return render(
        request,
        "smart_farming/irrigation_record_list.html",
        context,
    )


def irrigation_record_create(request):
    if request.method == "POST":
        form = IrrigationRecordForm(request.POST)

        if form.is_valid():
            irrigation_record = form.save()

            messages.success(
                request,
                "Irrigation record created successfully.",
            )

            return redirect(
                "irrigation_record_detail",
                pk=irrigation_record.pk,
            )
    else:
        form = IrrigationRecordForm()

    return render(
        request,
        "smart_farming/irrigation_record_form.html",
        {
            "form": form,
            "page_title": "Create Irrigation Record",
            "button_text": "Save Irrigation Record",
        },
    )


def irrigation_record_detail(request, pk):
    irrigation_record = get_object_or_404(
        IrrigationRecord.objects.select_related(
            "farm",
            "planting",
            "planting__crop",
        ),
        pk=pk,
    )

    return render(
        request,
        "smart_farming/irrigation_record_detail.html",
        {"irrigation_record": irrigation_record},
    )


def irrigation_record_update(request, pk):
    irrigation_record = get_object_or_404(
        IrrigationRecord.objects.select_related(
            "farm",
            "planting",
            "planting__crop",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = IrrigationRecordForm(
            request.POST,
            instance=irrigation_record,
        )

        if form.is_valid():
            irrigation_record = form.save()

            messages.success(
                request,
                "Irrigation record updated successfully.",
            )

            return redirect(
                "irrigation_record_detail",
                pk=irrigation_record.pk,
            )
    else:
        form = IrrigationRecordForm(
            instance=irrigation_record,
        )

    return render(
        request,
        "smart_farming/irrigation_record_form.html",
        {
            "form": form,
            "irrigation_record": irrigation_record,
            "page_title": "Update Irrigation Record",
            "button_text": "Update Irrigation Record",
        },
    )


def irrigation_record_delete(request, pk):
    irrigation_record = get_object_or_404(
        IrrigationRecord,
        pk=pk,
    )

    try:
        irrigation_record.delete()

        messages.success(
            request,
            "Irrigation record deleted successfully.",
        )

    except ProtectedError:
        messages.error(
            request,
            "This irrigation record cannot be deleted because "
            "other records depend on it.",
        )

    return redirect("irrigation_record_list")
