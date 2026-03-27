"""
Analytics views and serializers
"""
from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField
from campaign_os.analytics.models import DashboardSnapshot
from campaign_os.voters.models import Voter
from campaign_os.masters.models import Booth, Constituency, District
from campaign_os.volunteers.models import Volunteer
from campaign_os.campaigns.models import CampaignEvent
from rest_framework import status as drf_status


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
        
        stats = {
            'total_voters': voter_qs.count(),
            'voters_contacted': voter_qs.filter(is_contacted=True).count(),
            'voters_by_sentiment': dict(
                voter_qs.values('sentiment').annotate(count=Count('id')).values_list('sentiment', 'count')
            ),
            'total_booths': Booth.objects.filter(is_active=True).count(),
            'booths_assigned': Booth.objects.filter(is_active=True, primary_agent__isnull=False).count(),
            'active_volunteers': Volunteer.objects.filter(is_active=True, status='active').count(),
            'total_events': CampaignEvent.objects.filter(is_active=True).count(),
            'completed_events': CampaignEvent.objects.filter(is_active=True, status='completed').count(),
        }
        return Response(stats)
    
    @action(detail=False, methods=['GET'])
    def booth_statistics(self, request):
        """Get booth-wise statistics using actual voter record counts"""
        constituency_id = request.query_params.get('constituency_id')

        booths = Booth.objects.filter(is_active=True).select_related('ward', 'ward__constituency')
        if constituency_id:
            booths = booths.filter(ward__constituency_id=constituency_id)

        booths = booths.annotate(
            actual_total=Count('voters', filter=Q(voters__is_active=True), distinct=True),
            actual_contacted=Count('voters', filter=Q(voters__is_active=True, voters__is_contacted=True), distinct=True),
        ).order_by('number')

        stats = []
        for b in booths:
            total = b.actual_total
            contacted = b.actual_contacted
            stats.append({
                'id': b.id,
                'name': b.name,
                'number': b.number,
                'ward_name': b.ward.name if b.ward_id else None,
                'constituency_name': b.ward.constituency.name if b.ward_id and b.ward.constituency_id else None,
                'total_voters': total,
                'voters_contacted': contacted,
                'coverage_percentage': round(contacted * 100 / total, 1) if total > 0 else 0,
            })
        return Response(stats)
    
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
        """Get ward-wise voter statistics"""
        from campaign_os.masters.models import Ward
        constituency_id = request.query_params.get('constituency_id')

        wards = Ward.objects.filter(is_active=True)
        if constituency_id:
            wards = wards.filter(constituency_id=constituency_id)

        result = []
        for ward in wards:
            # Count voters via EITHER the direct village FK OR via the booth's ward FK
            voters = Voter.objects.filter(
                is_active=True
            ).filter(
                Q(village=ward) | Q(booth__ward=ward)
            ).distinct()
            total = voters.count()
            contacted = voters.filter(is_contacted=True).count()
            sentiment = dict(voters.values('sentiment').annotate(cnt=Count('id')).values_list('sentiment', 'cnt'))
            caste_dist = dict(voters.values('caste').annotate(cnt=Count('id')).values_list('caste', 'cnt'))
            # Count distinct booths from both the ward FK and from the voters' booths
            ward_booth_ids = set(ward.booths.filter(is_active=True).values_list('id', flat=True))
            voter_booth_ids = set(voters.values_list('booth', flat=True).distinct())
            all_booth_ids = ward_booth_ids | voter_booth_ids
            result.append({
                'id': ward.id,
                'name': ward.name,
                'constituency_name': ward.constituency.name if ward.constituency_id else '',
                'total_voters': total,
                'voters_contacted': contacted,
                'coverage_pct': round(contacted * 100 / total, 1) if total > 0 else 0,
                'sentiment': sentiment,
                'caste_dist': caste_dist,
                'booth_count': len(all_booth_ids),
            })
        return Response(result)

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
