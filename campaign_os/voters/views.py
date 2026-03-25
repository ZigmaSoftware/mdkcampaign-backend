"""
Voter management views
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Q, Count
from campaign_os.voters.models import Voter, VoterContact, VoterSurvey, VoterPreference, VoterFeedback
from campaign_os.voters.serializers import (
    VoterSerializer, VoterSimpleSerializer, VoterContactSerializer,
    VoterSurveySerializer, VoterPreferenceSerializer, VoterFeedbackSerializer
)
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, resolve_by_code, to_int, to_str, to_bool


class VoterViewSet(viewsets.ModelViewSet):
    """Voter management"""
    queryset = Voter.objects.filter(is_active=True).prefetch_related('booth', 'village', 'preferred_party')
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['booth', 'village', 'sentiment', 'is_contacted', 'gender']
    search_fields = ['name', 'voter_id', 'phone']
    serializer_class = VoterSerializer

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

        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            voter_id = to_str(row.get('voter_id') or row.get('epic') or row.get('epic_no'))
            if not voter_id:
                result.fail(i, 'voter_id is required')
                continue
            try:
                booth_id = resolve_by_code(Booth, row.get('booth_code', ''))
                ward_id  = resolve_by_code(Ward,  row.get('ward_code', ''))

                defaults = {
                    'name':            to_str(row.get('name')),
                    'father_name':     to_str(row.get('father_name')),
                    'gender':          to_str(row.get('gender')) or None,
                    'date_of_birth':   to_str(row.get('date_of_birth')) or None,
                    'age':             to_int(row.get('age')),
                    'phone':           to_str(row.get('phone')) or None,
                    'phone2':          to_str(row.get('phone2')) or None,
                    'email':           to_str(row.get('email')) or None,
                    'address':         to_str(row.get('address')) or None,
                    'booth_id':        booth_id,
                    'village_id':      ward_id,
                    'religion':        to_str(row.get('religion')) or None,
                    'caste':           to_str(row.get('caste')) or None,
                    'sub_caste':       to_str(row.get('sub_caste')) or None,
                    'sentiment':       to_str(row.get('sentiment')) or 'undecided',
                    'education_level': to_str(row.get('education_level')) or None,
                    'occupation':      to_str(row.get('occupation')) or None,
                    'scheme_name':     to_str(row.get('scheme_name')) or None,
                    'issue_name':      to_str(row.get('issue_name')) or None,
                    'notes':           to_str(row.get('notes')) or None,
                }
                _, created = Voter.objects.get_or_create(voter_id=voter_id, defaults=defaults)
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)


class VoterContactViewSet(viewsets.ModelViewSet):
    """Voter contact history tracking"""
    queryset = VoterContact.objects.filter(is_active=True)
    serializer_class = VoterContactSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    queryset = VoterSurvey.objects.filter(is_active=True)
    serializer_class = VoterSurveySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['voter', 'survey_type']


class VoterPreferenceViewSet(viewsets.ModelViewSet):
    queryset = VoterPreference.objects.filter(is_active=True)
    serializer_class = VoterPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]


class VoterFeedbackViewSet(viewsets.ModelViewSet):
    queryset = VoterFeedback.objects.filter(is_active=True)
    serializer_class = VoterFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
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
