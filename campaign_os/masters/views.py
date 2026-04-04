"""
Views for master data management
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, IntegerField
from django.db.models.functions import Cast
from campaign_os.masters.models import (
    Country, State, District, Constituency, Ward, Booth, PollingArea,
    Candidate, Party, Scheme, Issue, Achievement, TaskType, TaskCategory, CampaignActivityType, VolunteerRole, VolunteerType, Panchayat, Union
)
from campaign_os.masters.serializers import (
    CountrySerializer, StateSerializer, DistrictSimpleSerializer, DistrictDetailSerializer,
    ConstituencySimpleSerializer, ConstituencyDetailSerializer,
    WardSimpleSerializer, WardDetailSerializer,
    BoothSimpleSerializer, BoothDetailSerializer, PollingAreaSerializer,
    PartySerializer, CandidateDetailSerializer, CandidateSimpleSerializer,
    SchemeSerializer, IssueSerializer, AchievementSerializer, TaskTypeSerializer, TaskCategorySerializer,
    CampaignActivityTypeSerializer, VolunteerRoleSerializer, VolunteerTypeSerializer, PanchayatSerializer, UnionSerializer
)
from campaign_os.core.utils.bulk_upload import (
    parse_upload, BulkResult, resolve_by_code, to_int, to_str, to_bool
)
from campaign_os.core.permissions import ScreenPermission


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticated]


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['country']
    search_fields = ['name', 'code']


class DistrictViewSet(viewsets.ModelViewSet):
    screen_slug = "district"
    queryset = District.objects.filter(is_active=True).select_related('state')
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['state']
    search_fields = ['name', 'code']
    ordering = ['name']

    def get_serializer_class(self):
        return DistrictDetailSerializer if self.action == 'retrieve' else DistrictSimpleSerializer

    @action(detail=True, methods=['GET'])
    def constituencies(self, request, pk=None):
        district = self.get_object()
        return Response(ConstituencySimpleSerializer(
            district.constituencies.filter(is_active=True), many=True
        ).data)

    @action(detail=True, methods=['GET'])
    def booths(self, request, pk=None):
        district = self.get_object()
        booths = Booth.objects.filter(
            ward__constituency__district=district, is_active=True
        ).select_related('ward')
        return Response(BoothSimpleSerializer(booths, many=True).data)


class ConstituencyViewSet(viewsets.ModelViewSet):
    screen_slug = "constituency"
    queryset = Constituency.objects.filter(is_active=True).select_related('district')
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['district', 'election_type']
    search_fields = ['name', 'code']
    ordering = ['name']

    def get_serializer_class(self):
        return ConstituencyDetailSerializer if self.action == 'retrieve' else ConstituencySimpleSerializer

    @action(detail=True, methods=['GET'])
    def wards(self, request, pk=None):
        const = self.get_object()
        return Response(WardSimpleSerializer(const.wards.filter(is_active=True), many=True).data)

    @action(detail=True, methods=['GET'])
    def candidates(self, request, pk=None):
        const = self.get_object()
        return Response(CandidateSimpleSerializer(const.candidates.filter(is_active=True), many=True).data)

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns: name, code (required), district_code, election_type
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            code = to_str(row.get('code'))
            if not code:
                result.fail(i, 'code is required'); continue
            try:
                district_id = resolve_by_code(District, row.get('district_code', ''))
                _, created = Constituency.objects.get_or_create(
                    code=code,
                    defaults={
                        'name':          to_str(row.get('name')) or None,
                        'district_id':   district_id,
                        'election_type': to_str(row.get('election_type')) or 'assembly',
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class WardViewSet(viewsets.ModelViewSet):
    screen_slug = "ward"
    queryset = Ward.objects.filter(is_active=True).select_related('constituency')
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['constituency', 'booths']
    search_fields = ['name', 'code']

    def get_serializer_class(self):
        return WardDetailSerializer if self.action == 'retrieve' else WardSimpleSerializer

    @action(detail=True, methods=['GET'])
    def booths(self, request, pk=None):
        ward = self.get_object()
        return Response(BoothDetailSerializer(ward.booths.filter(is_active=True), many=True).data)

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns: name, code, constituency_code
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            name = to_str(row.get('name'))
            code = to_str(row.get('code'))
            if not (name or code):
                result.fail(i, 'name or code is required'); continue
            try:
                const_id = resolve_by_code(Constituency, row.get('constituency_code', ''))
                _, created = Ward.objects.get_or_create(
                    constituency_id=const_id,
                    code=code or name[:5],
                    defaults={'name': name, 'constituency_id': const_id}
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class BoothViewSet(viewsets.ModelViewSet):
    screen_slug = "booth-master"
    queryset = (
        Booth.objects.filter(is_active=True)
             .select_related('panchayat', 'primary_agent', 'ward', 'ward__constituency')
             .prefetch_related('agents')
             .annotate(number_int=Cast('number', output_field=IntegerField()))
             .order_by('number_int')
    )
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['status', 'sentiment']
    search_fields = ['name', 'number', 'code', 'address']
    ordering = ['number_int']

    def get_permissions(self):
        # Many entry screens need booth options for dropdowns/filters even when
        # the user is not allowed to manage Booth Master itself. Keep the list
        # lookup broadly available to authenticated users, while edit actions
        # still require booth-master screen permissions.
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'retrieve']:
            return BoothDetailSerializer
        return BoothSimpleSerializer

    @action(detail=True, methods=['GET'])
    def voters(self, request, pk=None):
        booth = self.get_object()
        from campaign_os.voters.models import Voter
        from campaign_os.voters.serializers import VoterSerializer
        return Response(VoterSerializer(booth.voters.filter(is_active=True), many=True).data)

    @action(detail=True, methods=['POST'])
    def assign_agent(self, request, pk=None):
        booth    = self.get_object()
        agent_id = request.data.get('agent_id')
        if not agent_id:
            return Response({'detail': 'agent_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        from campaign_os.accounts.models import User
        try:
            booth.primary_agent = User.objects.get(id=agent_id)
            booth.save()
            return Response({'detail': 'Agent assigned successfully'})
        except User.DoesNotExist:
            return Response({'detail': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'])
    def nearby(self, request, pk=None):
        booth = self.get_object()
        if not booth.latitude or not booth.longitude:
            return Response({'detail': 'Booth location not available'})
        nearby = Booth.objects.filter(
            panchayat=booth.panchayat,
            is_active=True
        ).exclude(id=booth.id)[:10]
        return Response(BoothSimpleSerializer(nearby, many=True).data)

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns:
          code (required), number, name,
          address, village, total_voters, male_voters, female_voters,
          third_gender_voters, status, sentiment, notes, volunteer_name
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            code = to_str(row.get('code'))
            if not code:
                result.fail(i, 'code is required'); continue
            try:
                # resolve primary_volunteer by name
                vol_name = to_str(row.get('volunteer_name'))
                primary_volunteer_id = None
                if vol_name:
                    from campaign_os.volunteers.models import Volunteer as Vol
                    v = Vol.objects.filter(name=vol_name, is_active=True).first()
                    if v:
                        primary_volunteer_id = v.id
                _, created = Booth.objects.get_or_create(
                    code=code,
                    defaults={
                        'number':               to_str(row.get('number'))  or None,
                        'name':                 to_str(row.get('name'))    or None,
                        'address':              to_str(row.get('address')) or None,
                        'village':              to_str(row.get('village')) or None,
                        'total_voters':         to_int(row.get('total_voters'))         or 0,
                        'male_voters':          to_int(row.get('male_voters'))          or 0,
                        'female_voters':        to_int(row.get('female_voters'))        or 0,
                        'third_gender_voters':  to_int(row.get('third_gender_voters'))  or 0,
                        'status':               to_str(row.get('status'))    or 'pending',
                        'sentiment':            to_str(row.get('sentiment')) or 'neutral',
                        'notes':                to_str(row.get('notes'))     or None,
                        'primary_volunteer_id': primary_volunteer_id,
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class PollingAreaViewSet(viewsets.ModelViewSet):
    screen_slug = "area"
    queryset = PollingArea.objects.filter(is_active=True).select_related('constituency')
    serializer_class = PollingAreaSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['constituency']
    search_fields = ['name', 'code']


class PartyViewSet(viewsets.ModelViewSet):
    screen_slug = "party"
    queryset = Party.objects.filter(is_active=True)
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    search_fields = ['name', 'code', 'abbreviation']
    ordering = ['name']

    @action(detail=True, methods=['GET'])
    def candidates(self, request, pk=None):
        party = self.get_object()
        return Response(CandidateSimpleSerializer(party.candidates.filter(is_active=True), many=True).data)

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns: name, code, abbreviation (all required as unique keys),
          primary_color, secondary_color, headquarters, president_name, founded_year
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            code = to_str(row.get('code'))
            if not code:
                result.fail(i, 'code is required'); continue
            try:
                abbr = to_str(row.get('abbreviation')) or code
                _, created = Party.objects.get_or_create(
                    code=code,
                    defaults={
                        'name':            to_str(row.get('name'))           or code,
                        'abbreviation':    abbr,
                        'primary_color':   to_str(row.get('primary_color'))  or None,
                        'secondary_color': to_str(row.get('secondary_color'))or None,
                        'headquarters':    to_str(row.get('headquarters'))   or None,
                        'president_name':  to_str(row.get('president_name')) or None,
                        'founded_year':    to_int(row.get('founded_year')),
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class CandidateViewSet(viewsets.ModelViewSet):
    screen_slug = "candidate"
    queryset = Candidate.objects.filter(is_active=True).select_related('party', 'constituency')
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['party', 'constituency', 'is_incumbent']
    search_fields = ['name', 'father_name']
    ordering = ['name']

    def get_serializer_class(self):
        return CandidateDetailSerializer if self.action == 'retrieve' else CandidateSimpleSerializer

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns:
          name (required), party_code, constituency_code,
          gender (m/f/o), phone, email, is_incumbent (true/false)
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            name = to_str(row.get('name'))
            if not name:
                result.fail(i, 'name is required'); continue
            try:
                party_id = resolve_by_code(Party, row.get('party_code', ''))
                const_id = resolve_by_code(Constituency, row.get('constituency_code', ''))
                _, created = Candidate.objects.get_or_create(
                    name=name,
                    party_id=party_id,
                    constituency_id=const_id,
                    defaults={
                        'gender':       to_str(row.get('gender')) or None,
                        'phone':        to_str(row.get('phone'))  or None,
                        'email':        to_str(row.get('email'))  or None,
                        'is_incumbent': to_bool(row.get('is_incumbent')) or False,
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class SchemeViewSet(viewsets.ModelViewSet):
    screen_slug = "scheme"
    queryset = Scheme.objects.filter(is_active=True).select_related('constituency')
    serializer_class = SchemeSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['scheme_type', 'constituency']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        CSV columns:
          name (required), description, scheme_type, constituency_code,
          launch_date (YYYY-MM-DD), responsible_ministry
        """
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            name = to_str(row.get('name'))
            if not name:
                result.fail(i, 'name is required'); continue
            try:
                const_id = resolve_by_code(Constituency, row.get('constituency_code', ''))
                _, created = Scheme.objects.get_or_create(
                    name=name,
                    defaults={
                        'description':         to_str(row.get('description'))         or None,
                        'scheme_type':         to_str(row.get('scheme_type'))         or None,
                        'constituency_id':     const_id,
                        'launch_date':         to_str(row.get('launch_date'))         or None,
                        'responsible_ministry':to_str(row.get('responsible_ministry'))or None,
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))
        return Response(result.summary())


class AchievementViewSet(viewsets.ModelViewSet):
    screen_slug = "achievement"
    queryset = Achievement.objects.filter(is_active=True).select_related('panchayat', 'booth')
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['panchayat', 'booth']
    search_fields = ['name', 'description']
    ordering = ['-created_at']



class TaskTypeViewSet(viewsets.ModelViewSet):
    # Reuse task-category screen permissions so non-admin users who can manage
    # task masters can also access task types without new permission seeding.
    screen_slug = 'task-category'
    queryset = TaskType.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = TaskTypeSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class TaskCategoryViewSet(viewsets.ModelViewSet):
    screen_slug = "task-category"
    queryset = TaskCategory.objects.filter(is_active=True).select_related('task_type')
    serializer_class = TaskCategorySerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['task_type']
    search_fields = ['name']
    ordering = ['priority', 'name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class CampaignActivityTypeViewSet(viewsets.ModelViewSet):
    screen_slug = 'campaign-activity'
    """Campaign Activity Type master — drives the activity dropdown in Campaign Entry"""
    queryset = CampaignActivityType.objects.all().order_by('order', 'name')
    serializer_class = CampaignActivityTypeSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['event_type', 'is_active']


class VolunteerTypeViewSet(viewsets.ModelViewSet):
    screen_slug = 'volunteer-type'
    """Volunteer Type master — drives the volunteer type dropdown in Volunteer Entry"""
    queryset = VolunteerType.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = VolunteerTypeSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class VolunteerRoleViewSet(viewsets.ModelViewSet):
    screen_slug = 'volunteer-role'
    """Volunteer Role master — drives the role dropdown in Volunteer Entry"""
    queryset = VolunteerRole.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = VolunteerRoleSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class UnionViewSet(viewsets.ModelViewSet):
    screen_slug = 'union'
    queryset = Union.objects.filter(is_active=True).select_related('block').order_by('name')
    serializer_class = UnionSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'code']
    filterset_fields = ['block']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class PanchayatViewSet(viewsets.ModelViewSet):
    screen_slug = 'panchayat'
    queryset = Panchayat.objects.filter(is_active=True).select_related('union').order_by('name')
    serializer_class = PanchayatSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'code']
    filterset_fields = ['union']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
