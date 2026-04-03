"""
Analytics views and serializers
"""
import logging
from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField
from django.db.models.functions import Trim, Upper
from campaign_os.analytics.models import DashboardSnapshot
from campaign_os.voters.models import Voter
from campaign_os.masters.models import Booth, Constituency, District
from campaign_os.volunteers.models import Volunteer
from campaign_os.beneficiaries.models import Beneficiary
from campaign_os.campaigns.models import CampaignEvent
from campaign_os.activities.models import FieldSurvey
from rest_framework import status as drf_status

logger = logging.getLogger(__name__)


def _norm_voter_id(value):
    if not value:
        return ''
    return str(value).strip().upper()


class DashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSnapshot
        fields = '__all__'


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Analytics and dashboard APIs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['GET'])
    def dashboard_stats(self, request):
        """Get overall dashboard statistics"""
        constituency_id = request.query_params.get('constituency_id')
        
        # Base filters
        voter_qs = Voter.objects.filter(is_active=True)
        if constituency_id:
            voter_qs = voter_qs.filter(village__constituency_id=constituency_id)
        
        contacted_qs = voter_qs.filter(is_contacted=True)
        stats = {
            'total_voters': voter_qs.count(),
            'voters_contacted': contacted_qs.count(),
            'voters_by_sentiment': dict(
                voter_qs.values('sentiment').annotate(count=Count('id')).values_list('sentiment', 'count')
            ),
            'contacted_by_sentiment': dict(
                contacted_qs.values('sentiment').annotate(count=Count('id')).values_list('sentiment', 'count')
            ),
            'total_booths': Booth.objects.filter(is_active=True).count(),
            'booths_assigned': Booth.objects.filter(is_active=True, primary_agent__isnull=False).count(),
            'active_volunteers': Volunteer.objects.filter(is_active=True, status='active').count(),
            'total_events': CampaignEvent.objects.filter(is_active=True).count(),
            'completed_events': CampaignEvent.objects.filter(is_active=True, status='completed').count(),
            'surveys_conducted': FieldSurvey.objects.filter(is_active=True).count(),
            'surveys_positive':  FieldSurvey.objects.filter(is_active=True, support_level='positive').count(),
            'surveys_negative':  FieldSurvey.objects.filter(is_active=True, support_level='negative').count(),
            'surveys_neutral':   FieldSurvey.objects.filter(is_active=True, support_level='neutral').count(),
        }
        return Response(stats)
    
    @action(detail=False, methods=['GET'])
    def booth_statistics(self, request):
        """Get booth-wise statistics using actual voter record counts."""
        constituency_id = request.query_params.get('constituency_id')

        booths = Booth.objects.filter(is_active=True).select_related(
            'panchayat', 'panchayat__union', 'panchayat__union__block'
        )
        if constituency_id:
            booths = booths.filter(panchayat__union__block__constituency_id=constituency_id)

        _contacted = Q(voters__is_active=True, voters__is_contacted=True)
        booths = booths.annotate(
            actual_total=Count('voters', filter=Q(voters__is_active=True), distinct=True),
            actual_contacted=Count('voters', filter=_contacted, distinct=True),
            vol_count=Count('volunteers', filter=Q(volunteers__is_active=True), distinct=True),
            cnt_positive=Count('voters', filter=_contacted & Q(voters__sentiment='positive'), distinct=True),
            cnt_neutral =Count('voters', filter=_contacted & Q(voters__sentiment='neutral'),  distinct=True),
            cnt_negative=Count('voters', filter=_contacted & Q(voters__sentiment='negative'), distinct=True),
        ).order_by('number')

        stats = []
        for b in booths:
            # Use actual FK-linked count; fall back to the stored total_voters when
            # voters haven't been linked to this booth via FK yet (data import gap).
            total     = b.actual_total or b.total_voters or 0
            contacted = b.actual_contacted
            pos, neu, neg = b.cnt_positive, b.cnt_neutral, b.cnt_negative
            sentiment_base = pos + neu + neg
            panchayat = b.panchayat
            union  = panchayat.union  if panchayat else None
            block  = union.block      if union     else None

            stats.append({
                'id': b.id,
                'name': b.name,
                'number': b.number,
                'address': b.address or '',
                'constituency_name': None,
                'panchayat_name': panchayat.name if panchayat else '',
                'union_name':     union.name     if union     else '',
                'block_name':     block.name     if block     else '',
                'total_voters':       total,
                'voters_contacted':   contacted,
                'coverage_percentage': round(contacted * 100 / total, 1) if total > 0 else 0,
                'volunteer_count':    b.vol_count,
                'positive_pct': round(pos * 100 / sentiment_base, 1) if sentiment_base > 0 else 0,
                'neutral_pct':  round(neu * 100 / sentiment_base, 1) if sentiment_base > 0 else 0,
                'negative_pct': round(neg * 100 / sentiment_base, 1) if sentiment_base > 0 else 0,
            })
        return Response(stats)

    @action(detail=False, methods=['GET'])
    def booth_volunteers(self, request, booth_id=None):
        """Return volunteers assigned to a booth, grouped by role."""
        volunteers = Volunteer.objects.filter(
            is_active=True
        ).filter(
            Q(booth_id=booth_id) | Q(booths__id=booth_id)
        ).distinct().values('id', 'name', 'phone', 'phone2', 'skills', 'role', 'status')
        return Response(list(volunteers))

    @action(detail=False, methods=['GET'])
    def booth_voters_list(self, request, booth_id=None):
        """Return voters for a specific booth with basic details."""
        logger.info(
            "booth_voters_list called booth_id=%s params=%s user=%s",
            booth_id,
            dict(request.GET),
            getattr(request.user, 'id', None),
        )

        base_rows = list(
            Voter.objects.filter(is_active=True, booth_id=booth_id)
            .order_by('village__name', 'name')
            .values(
                'id', 'voter_id', 'name', 'age', 'gender',
                'sentiment', 'is_contacted', 'phone',
                ward_name=F('village__name'),
            )
        )
        if not base_rows:
            return Response([])

        voter_ids = [row.get('voter_id') for row in base_rows if row.get('voter_id')]
        normalized_voter_ids = {
            _norm_voter_id(voter_id)
            for voter_id in voter_ids
            if _norm_voter_id(voter_id)
        }
        volunteer_ids = set()
        beneficiary_ids = set()

        if normalized_voter_ids:
            volunteer_ids = set(
                Volunteer.objects.filter(is_active=True, voter_id__isnull=False)
                .annotate(norm_voter_id=Upper(Trim(F('voter_id'))))
                .filter(norm_voter_id__in=normalized_voter_ids)
                .values_list('norm_voter_id', flat=True)
            )
            beneficiary_ids = set(
                Beneficiary.objects.filter(is_active=True, voter_id__isnull=False)
                .annotate(norm_voter_id=Upper(Trim(F('voter_id'))))
                .filter(norm_voter_id__in=normalized_voter_ids)
                .values_list('norm_voter_id', flat=True)
            )

        voters = []
        for row in base_rows:
            voter_id = _norm_voter_id(row.get('voter_id'))
            is_volunteer = bool(voter_id and voter_id in volunteer_ids)
            is_beneficiary = bool(voter_id and voter_id in beneficiary_ids)

            if is_volunteer:
                voter_type = 'Volunteer'
            elif is_beneficiary:
                voter_type = 'Beneficiary'
            else:
                voter_type = None

            voters.append({
                'id': row.get('id'),
                'voter_id': row.get('voter_id'),
                'name': row.get('name'),
                'age': row.get('age'),
                'gender': row.get('gender'),
                'sentiment': row.get('sentiment'),
                'is_contacted': row.get('is_contacted'),
                'phone': row.get('phone'),
                'ward_name': row.get('ward_name'),
                'voter_type': voter_type,
                'is_volunteer_type': is_volunteer,
                'is_beneficiary_type': is_beneficiary,
            })

        return Response(voters)
    
    @action(detail=False, methods=['GET'])
    def constituency_stats(self, request):
        """Get constituency-wise statistics"""
        stats = Constituency.objects.filter(is_active=True).annotate(
            total_voters=Sum('wards__booths__total_voters'),
            voters_contacted=Count('wards__booths__voters', filter=Q(wards__booths__voters__is_contacted=True)),
            booths=Count('wards__booths'),
            volunteers=Count('wards__volunteers')
        ).values('id', 'name', 'total_voters', 'voters_contacted', 'booths', 'volunteers')
        return Response(list(stats))
    
    @action(detail=False, methods=['GET'])
    def volunteer_performance(self, request):
        """Get volunteer performance metrics"""
        volunteers = Volunteer.objects.filter(is_active=True).values(
            'id', 'user__first_name', 'user__last_name', 'booth__name'
        ).annotate(
            voters_contacted=F('voters_contacted'),
            performance_score=F('performance_score')
        )
        return Response(list(volunteers))
    
    @action(detail=False, methods=['GET'])
    def sentiment_distribution(self, request):
        """Get voter sentiment distribution"""
        constituency_id = request.query_params.get('constituency_id')
        
        voters = Voter.objects.filter(is_active=True)
        if constituency_id:
            voters = voters.filter(village__constituency_id=constituency_id)
        
        distribution = voters.values('sentiment').annotate(
            count=Count('id'),
            percentage=Case(
                When(Q(), then=Count('id') * 100 / voters.count()),
                default=0,
                output_field=IntegerField()
            )
        )
        return Response(list(distribution))
    
    @action(detail=False, methods=['GET'])
    def event_analytics(self, request):
        """Get event attendance and success metrics"""
        events = CampaignEvent.objects.filter(is_active=True).values(
            'id', 'title', 'event_type', 'scheduled_date'
        ).annotate(
            expected=F('expected_attendees'),
            actual=F('actual_attendees'),
            success_score=F('success_score')
        )
        return Response(list(events))
    
    @action(detail=False, methods=['GET'])
    def geographic_coverage(self, request):
        """Get geographic coverage statistics by district"""
        coverage = District.objects.filter(is_active=True).annotate(
            total_booths=Count('constituencies__wards__booths'),
            assigned_booths=Count('constituencies__wards__booths', filter=Q(constituencies__wards__booths__primary_agent__isnull=False)),
            total_voters=Sum('constituencies__wards__booths__total_voters'),
            contacted_voters=Count('constituencies__wards__booths__voters', filter=Q(constituencies__wards__booths__voters__is_contacted=True))
        ).values('id', 'name', 'total_booths', 'assigned_booths', 'total_voters', 'contacted_voters')
        return Response(list(coverage))

    @action(detail=False, methods=['GET'])
    def ward_statistics(self, request):
        """Get ward-wise voter statistics — uses bulk SQL aggregations to avoid N+1."""
        from campaign_os.masters.models import Ward
        from collections import defaultdict

        constituency_id = request.query_params.get('constituency_id')

        # Fast pre-check: find ward IDs that actually have voters via either path.
        # If none exist yet (data not linked), return empty immediately.
        direct_ward_ids = set(
            Voter.objects.filter(is_active=True, village__isnull=False)
            .values_list('village_id', flat=True).distinct()
        )
        booth_ward_ids = set(
            Voter.objects.filter(is_active=True, booth__ward__isnull=False)
            .values_list('booth__ward_id', flat=True).distinct()
        )
        relevant_ward_ids = direct_ward_ids | booth_ward_ids
        if not relevant_ward_ids:
            return Response([])

        # Fetch only wards that have data, with SQL-level annotations
        ward_qs = Ward.objects.filter(is_active=True, id__in=relevant_ward_ids)
        if constituency_id:
            ward_qs = ward_qs.filter(constituency_id=constituency_id)

        ward_qs = ward_qs.select_related('constituency').annotate(
            direct_voters=Count('voters', filter=Q(voters__is_active=True), distinct=True),
            direct_contacted=Count('voters', filter=Q(voters__is_active=True, voters__is_contacted=True), distinct=True),
            vol_count=Count('volunteers', filter=Q(volunteers__is_active=True), distinct=True),
            active_booth_count=Count('booths', filter=Q(booths__is_active=True), distinct=True),
        )
        ward_map = {w.id: w for w in ward_qs}
        if not ward_map:
            return Response([])

        active_ids = set(ward_map.keys())

        # Bulk: booth-based voter counts grouped by ward (single query)
        booth_voters_by_ward: dict = defaultdict(lambda: {'total': 0, 'contacted': 0})
        for row in (
            Voter.objects.filter(is_active=True, booth__ward_id__in=active_ids)
            .values('booth__ward_id')
            .annotate(
                total=Count('id', distinct=True),
                contacted=Count('id', filter=Q(is_contacted=True), distinct=True),
            )
        ):
            wid = row['booth__ward_id']
            booth_voters_by_ward[wid]['total'] = row['total']
            booth_voters_by_ward[wid]['contacted'] = row['contacted']

        # Bulk: sentiment — direct voters
        sentiment_by_ward: dict = defaultdict(lambda: defaultdict(int))
        for row in (
            Voter.objects.filter(is_active=True, village_id__in=active_ids)
            .values('village_id', 'sentiment')
            .annotate(cnt=Count('id'))
        ):
            sentiment_by_ward[row['village_id']][row['sentiment'] or ''] += row['cnt']
        # Bulk: sentiment — booth-based voters
        for row in (
            Voter.objects.filter(is_active=True, booth__ward_id__in=active_ids)
            .values('booth__ward_id', 'sentiment')
            .annotate(cnt=Count('id'))
        ):
            sentiment_by_ward[row['booth__ward_id']][row['sentiment'] or ''] += row['cnt']

        # Build result in Python
        result = []
        for wid, w in ward_map.items():
            direct_v = w.direct_voters
            direct_c = w.direct_contacted
            booth_v  = booth_voters_by_ward[wid]['total']
            booth_c  = booth_voters_by_ward[wid]['contacted']
            total     = max(direct_v, booth_v)
            contacted = max(direct_c, booth_c)
            result.append({
                'id': wid,
                'name': w.name,
                'constituency_name': w.constituency.name if w.constituency_id else '',
                'total_voters': total,
                'voters_contacted': contacted,
                'coverage_pct': round(contacted * 100 / total, 1) if total > 0 else 0,
                'sentiment': dict(sentiment_by_ward[wid]),
                'caste_dist': {},
                'booth_count': w.active_booth_count,
                'volunteer_count': w.vol_count,
            })

        result.sort(key=lambda x: x['name'])
        return Response(result)

    @action(detail=False, methods=['GET'])
    def ward_volunteers(self, request, ward_id=None):
        """Return volunteers assigned to a ward, grouped by role."""
        volunteers = Volunteer.objects.filter(
            is_active=True, ward_id=ward_id
        ).values('id', 'name', 'phone', 'phone2', 'skills', 'role', 'status')
        return Response(list(volunteers))

    @action(detail=False, methods=['GET'])
    def age_breakdown(self, request):
        """Age group breakdown for voters, volunteers, or beneficiaries.

        Query params:
          type     — 'voter' (default) | 'volunteer' | 'beneficiary'
          booth_id — optional int, filter by booth
          ward_id  — optional int, filter by ward / village
        """
        from campaign_os.core.utils.age_utils import AGE_GROUPS, age_group_q

        model_type = request.query_params.get('type', 'voter')
        booth_id   = request.query_params.get('booth_id', '').strip()
        ward_id    = request.query_params.get('ward_id',  '').strip()

        if model_type == 'volunteer':
            qs = Volunteer.objects.filter(is_active=True)
            if booth_id and booth_id.isdigit():
                qs = qs.filter(Q(booth_id=booth_id) | Q(booths__id=booth_id)).distinct()
            if ward_id and ward_id.isdigit():
                qs = qs.filter(ward_id=ward_id)
        elif model_type == 'beneficiary':
            qs = Beneficiary.objects.filter(is_active=True)
            if booth_id and booth_id.isdigit():
                qs = qs.filter(booth_id=booth_id)
            if ward_id and ward_id.isdigit():
                qs = qs.filter(ward_id=ward_id)
        else:
            qs = Voter.objects.filter(is_active=True)
            if booth_id and booth_id.isdigit():
                qs = qs.filter(booth_id=booth_id)
            if ward_id and ward_id.isdigit():
                qs = qs.filter(village_id=ward_id)

        total   = qs.count()
        unknown = qs.filter(age__isnull=True).count()

        breakdown = []
        for group in AGE_GROUPS:
            count = qs.filter(age_group_q(group)).count()
            breakdown.append({'age_group': group, 'count': count})
        breakdown.append({'age_group': 'Unknown', 'count': unknown})

        return Response({'total': total, 'breakdown': breakdown})

    @action(detail=False, methods=['POST'])
    def fix_links(self, request):
        """Bulk-populate booth.ward and voter.village FKs from existing data.
        Safe: only links booths to a ward when there is exactly 1 ward in the
        constituency (or 1 ward total), so no data is guessed incorrectly."""
        from campaign_os.masters.models import Ward
        from campaign_os.masters.models import Constituency as Con

        fixed_booths = 0
        fixed_voters = 0

        # Step 1: If exactly 1 active ward exists, link all unlinked booths to it.
        # (Safe: only acts when there is no ambiguity about which ward to use.)
        active_wards = Ward.objects.filter(is_active=True)
        if active_wards.count() == 1:
            single_ward = active_wards.first()
            fixed_booths = Booth.objects.filter(is_active=True, ward__isnull=True).update(ward=single_ward)

        # Step 2: For voters with no village, populate from their booth's ward
        voters_fixed = Voter.objects.filter(
            is_active=True, village__isnull=True, booth__ward__isnull=False
        ).update(village=F('booth__ward'))
        fixed_voters = voters_fixed

        return Response({
            'fixed_booths': fixed_booths,
            'fixed_voters': fixed_voters,
        }, status=drf_status.HTTP_200_OK)
