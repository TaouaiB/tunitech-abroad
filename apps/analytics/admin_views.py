from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from apps.analytics.services.admin_metrics import AdminMetricsService
from apps.analytics.services.data_quality import AdminDataQualityService

@staff_member_required
def admin_operations_view(request):
    metrics = AdminMetricsService.get_dashboard_metrics()
    context = {
        **metrics,
        'title': 'Operations Dashboard',
        'has_permission': True,
        'site_header': 'TuniAtlas Admin',
        'site_title': 'TuniAtlas',
    }
    return render(request, 'admin/operations_dashboard.html', context)

@staff_member_required
def data_quality_dashboard_view(request):
    context = {
        **AdminDataQualityService.get_dashboard_context(),
        'title': 'Data Quality Dashboard',
        'has_permission': True,
        'site_header': 'TuniAtlas Admin',
        'site_title': 'TuniAtlas',
    }
    return render(request, 'admin/data_quality_dashboard.html', context)
