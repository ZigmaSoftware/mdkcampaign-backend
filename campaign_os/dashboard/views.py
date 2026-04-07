import logging

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from campaign_os.accounts.models import UserScreenPermission
from campaign_os.core.permissions import resolve_user_permission_roles
from campaign_os.dashboard.serializers import DashboardFilterSerializer, TaskDashboardFilterSerializer
from campaign_os.dashboard.services.dashboard_service import DashboardService
from campaign_os.dashboard.services.task_dashboard_service import TaskDashboardService


logger = logging.getLogger(__name__)


def _has_view_access(request, screen_slug):
    user = request.user
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'role', '') == 'admin':
        return True

    roles = resolve_user_permission_roles(user, screen_slug=screen_slug)
    if not roles:
        return False

    return UserScreenPermission.objects.filter(
        role__in=roles,
        user_screen__slug=screen_slug,
        can_view=True,
    ).exists()


def _has_any_view_access(request, screen_slugs):
    for screen_slug in screen_slugs:
        if _has_view_access(request, screen_slug):
            return True
    return False


def _forbidden_response():
    return Response({'detail': 'You do not have permission to view this dashboard.'}, status=status.HTTP_403_FORBIDDEN)


def _validate_filters(request):
    serializer = DashboardFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _validate_task_dashboard_filters(request):
    params = request.query_params.copy()
    if 'from' in params and 'from_date' not in params:
        params['from_date'] = params['from']
    if 'to' in params and 'to_date' not in params:
        params['to_date'] = params['to']
    serializer = TaskDashboardFilterSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    if not _has_any_view_access(request, (
        'activity-dashboard',
        'dashboard-home',
        'report-overview',
        'voter-report',
        'volunteer-report',
        'campaign-report',
        'activity-report',
    )):
        return _forbidden_response()
    try:
        data = DashboardService().get_summary(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard summary failed')
        return Response(
            {
                'filters': {},
                'kpis': {},
                'support_breakdown': [],
                'gender_breakdown': [],
                'age_breakdown': [],
                'awareness_breakdown': [],
                'vote_likelihood_breakdown': [],
                'response_breakdown': [],
                'party_preference_breakdown': [],
            },
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_booths(request):
    if not _has_any_view_access(request, (
        'activity-dashboard',
        'report-overview',
        'voter-report',
        'volunteer-report',
        'campaign-report',
        'activity-report',
    )):
        return _forbidden_response()
    try:
        data = DashboardService().get_booth_ranking(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard booth ranking failed')
        return Response({'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_telecallers(request):
    if not _has_view_access(request, 'activity-dashboard'):
        return _forbidden_response()
    try:
        data = DashboardService().get_telecaller_efficiency(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard telecaller efficiency failed')
        return Response({'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_tasks(request):
    if not _has_view_access(request, 'activity-dashboard'):
        return _forbidden_response()
    try:
        data = DashboardService().get_task_panel(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard task panel failed')
        return Response({'summary': {}, 'items': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_filter_options(request):
    if not _has_view_access(request, 'activity-dashboard'):
        return _forbidden_response()
    try:
        data = DashboardService().get_filter_options()
        return Response(data)
    except Exception:
        logger.exception('Dashboard filter options failed')
        return Response(
            {
                'blocks': [],
                'unions': [],
                'panchayats': [],
                'booths': [],
                'telecallers': [],
                'volunteer_roles': [],
            },
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_dashboard_summary(request):
    if not _has_view_access(request, 'task-dashboard'):
        return _forbidden_response()
    try:
        data = TaskDashboardService().get_summary(_validate_task_dashboard_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Task dashboard summary failed')
        return Response(
            {
                'filters': {},
                'counts': {},
                'derived': {},
                'status_breakdown': [],
                'due_breakdown': [],
            },
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_dashboard_list(request):
    if not _has_view_access(request, 'task-dashboard'):
        return _forbidden_response()
    try:
        data = TaskDashboardService().get_list(_validate_task_dashboard_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Task dashboard list failed')
        return Response({'filters': {}, 'total': 0, 'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_dashboard_type_category(request):
    if not _has_view_access(request, 'task-dashboard'):
        return _forbidden_response()
    try:
        data = TaskDashboardService().get_type_category_analytics(_validate_task_dashboard_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Task dashboard type/category analytics failed')
        return Response(
            {'filters': {}, 'type_distribution': [], 'category_workload': []},
            status=status.HTTP_200_OK,
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_dashboard_campaign_activity_status(request):
    if not _has_view_access(request, 'task-dashboard'):
        return _forbidden_response()
    try:
        data = TaskDashboardService().get_campaign_activity_status(_validate_task_dashboard_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Task dashboard campaign activity status failed')
        return Response({'filters': {}, 'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_dashboard_filter_options(request):
    if not _has_view_access(request, 'task-dashboard'):
        return _forbidden_response()
    try:
        data = TaskDashboardService().get_filter_options()
        return Response(data)
    except Exception:
        logger.exception('Task dashboard filter options failed')
        return Response(
            {
                'modules': [],
                'task_types': [],
                'task_categories': [],
            },
            status=status.HTTP_200_OK,
        )
