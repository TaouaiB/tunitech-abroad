from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from apps.analytics.services.admin_metrics import AdminMetricsService

@staff_member_required
def admin_operations_view(request):
    metrics = AdminMetricsService.get_dashboard_metrics()
    context = {
        **metrics,
        'title': 'Operations Dashboard',
        'has_permission': True,
        'site_header': 'TuniTech Abroad Admin',
        'site_title': 'TuniTech Abroad',
    }
    return render(request, 'admin/operations_dashboard.html', context)
