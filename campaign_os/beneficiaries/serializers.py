"""
Serializers for beneficiary management
"""
from rest_framework import serializers
from campaign_os.beneficiaries.models import Beneficiary
from campaign_os.masters.models import Booth


class BeneficiarySerializer(serializers.ModelSerializer):
    scheme_display = serializers.CharField(source='scheme.name', read_only=True, default='')
    booth_name     = serializers.CharField(source='booth.name', read_only=True, default='')
    booth_number   = serializers.CharField(source='booth.number', read_only=True, default='')
    ward_name      = serializers.CharField(source='ward.name', read_only=True, default='')
    panchayat_name = serializers.SerializerMethodField()
    union_name     = serializers.SerializerMethodField()

    def get_panchayat_name(self, obj):
        try:
            return obj.booth.panchayat.name or ''
        except AttributeError:
            return ''

    def get_union_name(self, obj):
        try:
            return obj.booth.panchayat.union.name or ''
        except AttributeError:
            return ''

    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'voter_id', 'phone', 'phone2', 'age', 'gender',
            'address', 'pincode',
            'booth', 'booth_name', 'booth_number', 'ward', 'ward_name', 'block',
            'panchayat_name', 'union_name',
            'scheme', 'scheme_display', 'scheme_name', 'benefit_type',
            'benefit_status', 'benefit_amount',
            'source', 'is_contacted', 'notes',
            'is_active', 'created_at', 'updated_at',
        ]
