"""
Views for beneficiary management
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Q
from campaign_os.beneficiaries.models import Beneficiary
from campaign_os.beneficiaries.serializers import BeneficiarySerializer
from campaign_os.core.permissions import ScreenPermission
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, to_int, to_str, to_bool


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """Beneficiary management"""
    screen_slug = 'beneficiary'
    queryset = Beneficiary.objects.filter(is_active=True).select_related(
        'booth__panchayat__union__block', 'ward', 'scheme'
    )
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['booth', 'ward', 'benefit_status', 'scheme']

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        search    = params.get('search',    '').strip()
        block     = params.get('block',     '').strip()
        panchayat = params.get('panchayat', '').strip()
        union     = params.get('union',     '').strip()
        if search:
            q = (
                Q(name__icontains=search) |
                Q(voter_id__icontains=search) |
                Q(phone__icontains=search) |
                Q(phone2__icontains=search) |
                Q(scheme_name__icontains=search) |
                Q(benefit_type__icontains=search) |
                Q(block__icontains=search) |
                Q(address__icontains=search) |
                Q(scheme__name__icontains=search) |
                Q(booth__panchayat__name__icontains=search) |
                Q(booth__panchayat__union__name__icontains=search)
            )
            if search.isdigit():
                q |= Q(age=int(search))
            qs = qs.filter(q)
        if block:
            qs = qs.filter(block__iexact=block)
        if panchayat:
            qs = qs.filter(booth__panchayat__name__iexact=panchayat)
        if union:
            qs = qs.filter(booth__panchayat__union__name__iexact=union)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        from campaign_os.masters.models import Booth, Ward, Scheme

        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

        booth_map  = {b.code: b.id for b in Booth.objects.only('id', 'code') if b.code}
        ward_map   = {w.code: w.id for w in Ward.objects.only('id', 'code')  if w.code}
        scheme_map = {s.name.lower(): s.id for s in Scheme.objects.only('id', 'name')}

        result = BulkResult()
        batch  = []
        BATCH_SIZE = 500

        for i, row in enumerate(rows, start=2):
            name = to_str(row.get('name'))
            if not name:
                result.fail(i, 'name is required')
                continue
            try:
                bc = to_str(row.get('booth_code', ''))
                wc = to_str(row.get('ward_code', ''))
                sn = to_str(row.get('scheme_name', '')).lower()
                batch.append(Beneficiary(
                    name           = name,
                    voter_id       = to_str(row.get('voter_id'))       or None,
                    phone          = to_str(row.get('phone'))           or None,
                    phone2         = to_str(row.get('phone2'))          or None,
                    age            = to_int(row.get('age')),
                    gender         = to_str(row.get('gender'))          or None,
                    address        = to_str(row.get('address'))         or None,
                    pincode        = to_str(row.get('pincode'))         or None,
                    booth_id       = booth_map.get(bc),
                    ward_id        = ward_map.get(wc),
                    block          = to_str(row.get('block'))           or None,
                    scheme_id      = scheme_map.get(sn),
                    scheme_name    = to_str(row.get('scheme_name'))     or None,
                    benefit_type   = to_str(row.get('benefit_type'))    or None,
                    benefit_status = to_str(row.get('benefit_status'))  or 'pending',
                    benefit_amount = to_str(row.get('benefit_amount'))  or None,
                    source         = to_str(row.get('source'))          or None,
                    notes          = to_str(row.get('notes'))           or None,
                ))
            except Exception as exc:
                result.fail(i, str(exc))
                continue

            if len(batch) >= BATCH_SIZE:
                try:
                    Beneficiary.objects.bulk_create(batch, ignore_conflicts=True)
                    for _ in batch: result.ok(True)
                except Exception as exc:
                    for _ in batch: result.fail(i, str(exc))
                batch = []

        if batch:
            try:
                Beneficiary.objects.bulk_create(batch, ignore_conflicts=True)
                for _ in batch: result.ok(True)
            except Exception as exc:
                for _ in batch: result.fail(0, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)
