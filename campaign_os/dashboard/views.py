import logging

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from campaign_os.dashboard.serializers import DashboardFilterSerializer
from campaign_os.dashboard.services.dashboard_service import DashboardService


logger = logging.getLogger(__name__)


def _validate_filters(request):
    serializer = DashboardFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
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
    try:
        data = DashboardService().get_booth_ranking(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard booth ranking failed')
        return Response({'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_telecallers(request):
    try:
        data = DashboardService().get_telecaller_efficiency(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard telecaller efficiency failed')
        return Response({'rows': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_tasks(request):
    try:
        data = DashboardService().get_task_panel(_validate_filters(request))
        return Response(data)
    except Exception:
        logger.exception('Dashboard task panel failed')
        return Response({'summary': {}, 'items': []}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_filter_options(request):
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
