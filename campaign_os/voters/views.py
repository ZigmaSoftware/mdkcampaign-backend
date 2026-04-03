"""
Voter management views
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Q, Count
from campaign_os.voters.models import Voter, VoterContact, VoterSurvey, VoterPreference, VoterFeedback
from campaign_os.core.permissions import ScreenPermission
from campaign_os.voters.serializers import (
    VoterSerializer, VoterSimpleSerializer, VoterContactSerializer,
    VoterSurveySerializer, VoterPreferenceSerializer, VoterFeedbackSerializer
)
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, resolve_by_code, to_int, to_str, to_bool


class VoterViewSet(viewsets.ModelViewSet):
    """Voter management"""
    screen_slug = 'voter'
    queryset = Voter.objects.filter(is_active=True).prefetch_related('booth', 'village', 'preferred_party')
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['village', 'sentiment', 'is_contacted', 'gender', 'pincode']
    serializer_class = VoterSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Support comma-separated booth IDs: ?booth=1,2,3
        booth_param = self.request.query_params.get('booth', '')
        if booth_param:
            booth_ids = [b.strip() for b in booth_param.split(',') if b.strip().isdigit()]
            if booth_ids:
                qs = qs.filter(booth_id__in=booth_ids)

        # Support ward filter: ?ward=5 (filters via booth__ward)
        ward_param = self.request.query_params.get('ward', '')
        if ward_param and ward_param.isdigit():
            qs = qs.filter(booth__ward_id=ward_param)

        # Panchayat filter: ?panchayat=12 (filters via booth__panchayat_id)
        panchayat_param = self.request.query_params.get('panchayat', '')
        if panchayat_param and panchayat_param.isdigit():
            qs = qs.filter(booth__panchayat_id=panchayat_param)

        # Union filter: ?union=5 (filters via booth__panchayat__union_id)
        union_param = self.request.query_params.get('union', '')
        if union_param and union_param.isdigit():
            qs = qs.filter(booth__panchayat__union_id=union_param)

        # Block filter: ?block=3 (filters via booth__panchayat__union__block_id)
        block_param = self.request.query_params.get('block', '')
        if block_param and block_param.isdigit():
            qs = qs.filter(booth__panchayat__union__block_id=block_param)

        # Support date filter on created_at: ?created_date=2026-03-28
        created_date = self.request.query_params.get('created_date', '')
        if created_date:
            qs = qs.filter(created_at__date=created_date)

        # Full-text search across all identifiable fields
        search = self.request.query_params.get('search', '').strip()
        if search:
            q = (
                Q(name__icontains=search) |
                Q(voter_id__icontains=search) |
                Q(phone__icontains=search) |
                Q(phone2__icontains=search) |
                Q(alt_phoneno2__icontains=search) |
                Q(alt_phoneno3__icontains=search) |
                Q(aadhaar__icontains=search) |
                Q(father_name__icontains=search) |
                Q(address__icontains=search)
            )
            if search.isdigit():
                q |= Q(age=int(search))
            qs = qs.filter(q)

        # Age group filter: ?age_group=18-25 or ?age_group=18-25,26-35
        age_group_param = self.request.query_params.get('age_group', '').strip()
        if age_group_param:
            from campaign_os.core.utils.age_utils import build_age_filter
            age_q = build_age_filter(age_group_param)
            if age_q:
                qs = qs.filter(age_q)

        # Contact number filter: ?contact_status=with|without
        contact_status = self.request.query_params.get('contact_status', '').strip().lower()
        if contact_status:
            has_contact_q = (
                (Q(phone__isnull=False) & ~Q(phone='')) |
                (Q(phone2__isnull=False) & ~Q(phone2='')) |
                (Q(alt_phoneno2__isnull=False) & ~Q(alt_phoneno2='')) |
                (Q(alt_phoneno3__isnull=False) & ~Q(alt_phoneno3=''))
            )
            if contact_status in {'with', 'yes', 'true', '1'}:
                qs = qs.filter(has_contact_q)
            elif contact_status in {'without', 'no', 'false', '0'}:
                qs = qs.exclude(has_contact_q)

        return qs

    @action(detail=False, methods=['GET'])
    def by_booth(self, request):
        booth_id = request.query_params.get('booth_id')
        if not booth_id:
            return Response({'detail': 'booth_id required'}, status=status.HTTP_400_BAD_REQUEST)
        voters = Voter.objects.filter(booth_id=booth_id, is_active=True)
        return Response(VoterSerializer(voters, many=True).data)

    @action(detail=False, methods=['GET'])
    def by_constituency(self, request):
        const_id = request.query_params.get('constituency_id')
        if not const_id:
            return Response({'detail': 'constituency_id required'}, status=status.HTTP_400_BAD_REQUEST)
        voters = Voter.objects.filter(village__constituency_id=const_id, is_active=True)
        return Response(VoterSerializer(voters, many=True).data)

    @action(detail=False, methods=['GET'])
    def by_sentiment(self, request):
        sentiment = request.query_params.get('sentiment')
        if not sentiment:
            return Response({'detail': 'sentiment required'}, status=status.HTTP_400_BAD_REQUEST)
        voters = Voter.objects.filter(sentiment=sentiment, is_active=True)
        return Response(VoterSimpleSerializer(voters, many=True).data)

    @action(detail=False, methods=['GET'])
    def uncontacted(self, request):
        voters = Voter.objects.filter(is_contacted=False, is_active=True)
        return Response(VoterSimpleSerializer(voters, many=True).data)

    @action(detail=True, methods=['POST'])
    def mark_contacted(self, request, pk=None):
        voter = self.get_object()
        voter.is_contacted  = True
        voter.contact_count = (voter.contact_count or 0) + 1
        from django.utils import timezone
        voter.last_contacted_at = timezone.now()
        voter.save()
        return Response({'detail': 'Voter marked as contacted'})

    @action(detail=True, methods=['GET'])
    def contact_history(self, request, pk=None):
        voter = self.get_object()
        return Response(VoterContactSerializer(voter.contacts.all(), many=True).data)

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        POST /api/v1/voters/voters/bulk-upload/
        Multipart field: file (.csv or .xlsx)

        CSV columns (all optional except voter_id):
          voter_id, name, father_name, gender, date_of_birth, age,
          phone, phone2, email, address, booth_code, ward_code,
          religion, caste, sub_caste, sentiment, education_level, occupation,
          scheme_name, issue_name, notes
        """
        from campaign_os.masters.models import Booth, Ward

        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

        # Build booth/ward lookup maps once (avoid per-row DB hits)
        # Primary lookup by code; secondary by number (CSV may contain numeric booth numbers)
        booths = list(Booth.objects.only('id', 'code', 'number'))
        booth_map = {b.code: b.id for b in booths}
        booth_num_map = {b.number: b.id for b in booths if b.number}
        ward_map      = {w.code: w.id for w in Ward.objects.only('id', 'code')}

        # Find existing voter_ids to skip duplicates
        all_ids = []
        for row in rows:
            vid = to_str(row.get('voter_id') or row.get('epic') or row.get('epic_no'))
            if vid:
                all_ids.append(vid)
        existing_ids = set(
            Voter.objects.filter(voter_id__in=all_ids).values_list('voter_id', flat=True)
        )

        result = BulkResult()
        batch = []
        BATCH_SIZE = 1000

        for i, row in enumerate(rows, start=2):
            voter_id = to_str(row.get('voter_id') or row.get('epic') or row.get('epic_no'))
            if not voter_id:
                result.fail(i, 'voter_id is required')
                continue
            if voter_id in existing_ids:
                result.ok(False)   # skipped (already exists)
                continue
            try:
                bc = to_str(row.get('booth_code', ''))
                wc = to_str(row.get('ward_code', ''))
                booth_id = booth_map.get(bc) or booth_num_map.get(bc)
                if bc and not booth_id:
                    result.fail(i, f'booth_code "{bc}" not found in master — import the booth first')
                    continue
                batch.append(Voter(
                    voter_id       = voter_id,
                    name           = to_str(row.get('name')),
                    father_name    = to_str(row.get('father_name')),
                    gender         = to_str(row.get('gender')) or None,
                    date_of_birth  = to_str(row.get('date_of_birth')) or None,
                    age            = to_int(row.get('age')),
                    phone          = to_str(row.get('phone')) or None,
                    phone2         = to_str(row.get('alt_phone') or row.get('phone2')) or None,
                    alt_phoneno2   = to_str(row.get('alt_phoneno2')) or None,
                    alt_phoneno3   = to_str(row.get('alt_phoneno3')) or None,
                    email          = to_str(row.get('email')) or None,
                    address        = to_str(row.get('address')) or None,
                    booth_id       = booth_id,
                    village_id     = ward_map.get(wc),
                    religion       = to_str(row.get('religion')) or None,
                    caste          = to_str(row.get('caste')) or None,
                    sub_caste      = to_str(row.get('sub_caste')) or None,
                    sentiment      = to_str(row.get('sentiment')) or 'undecided',
                    education_level= to_str(row.get('education_level')) or None,
                    occupation     = to_str(row.get('occupation')) or None,
                    scheme_name    = to_str(row.get('scheme_name')) or None,
                    issue_name     = to_str(row.get('issue_name')) or None,
                    notes          = to_str(row.get('notes')) or None,
                ))
                existing_ids.add(voter_id)   # prevent duplicates within same file
            except Exception as exc:
                result.fail(i, str(exc))
                continue

            if len(batch) >= BATCH_SIZE:
                try:
                    Voter.objects.bulk_create(batch, ignore_conflicts=True)
                    for _ in batch:
                        result.ok(True)
                except Exception as exc:
                    for _ in batch:
                        result.fail(i, str(exc))
                batch = []

        if batch:
            try:
                Voter.objects.bulk_create(batch, ignore_conflicts=True)
                for _ in batch:
                    result.ok(True)
            except Exception as exc:
                for b in batch:
                    result.fail(0, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)


class VoterContactViewSet(viewsets.ModelViewSet):
    """Voter contact history tracking"""
    screen_slug = 'voter'
    queryset = VoterContact.objects.filter(is_active=True)
    serializer_class = VoterContactSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['voter', 'method']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        voter = serializer.instance.voter
        if voter:
            voter.is_contacted  = True
            voter.contact_count = (voter.contact_count or 0) + 1
            from django.utils import timezone
            voter.last_contacted_at = timezone.now()
            voter.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VoterSurveyViewSet(viewsets.ModelViewSet):
    screen_slug = 'voter-survey'
    queryset = VoterSurvey.objects.filter(is_active=True)
    serializer_class = VoterSurveySerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['voter', 'survey_type']


class VoterPreferenceViewSet(viewsets.ModelViewSet):
    screen_slug = 'voter'
    queryset = VoterPreference.objects.filter(is_active=True)
    serializer_class = VoterPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]


class VoterFeedbackViewSet(viewsets.ModelViewSet):
    screen_slug = 'feedback'
    queryset = VoterFeedback.objects.filter(is_active=True)
    serializer_class = VoterFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['voter', 'feedback_type', 'status', 'issue']
    search_fields = ['subject', 'description']
    ordering = ['-created_at']

    @action(detail=True, methods=['POST'])
    def assign(self, request, pk=None):
        feedback = self.get_object()
        assigned_to_id = request.data.get('assigned_to_id')
        if not assigned_to_id:
            return Response({'detail': 'assigned_to_id required'}, status=status.HTTP_400_BAD_REQUEST)
        from campaign_os.accounts.models import User
        try:
            user = User.objects.get(id=assigned_to_id)
            feedback.assigned_to = user
            feedback.status = 'assigned'
            feedback.save()
            return Response({'detail': 'Feedback assigned'})
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['POST'])
    def resolve(self, request, pk=None):
        feedback   = self.get_object()
        resolution = request.data.get('resolution', '')
        if not resolution:
            return Response({'detail': 'resolution required'}, status=status.HTTP_400_BAD_REQUEST)
        feedback.status     = 'resolved'
        feedback.resolution = resolution
        from django.utils import timezone
        feedback.resolved_at = timezone.now()
        feedback.save()
        return Response({'detail': 'Feedback resolved'})
