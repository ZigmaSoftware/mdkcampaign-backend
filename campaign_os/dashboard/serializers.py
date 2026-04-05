from rest_framework import serializers


class DashboardFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    block = serializers.CharField(required=False, allow_blank=True)
    union = serializers.CharField(required=False, allow_blank=True)
    panchayat = serializers.CharField(required=False, allow_blank=True)
    booth = serializers.CharField(required=False, allow_blank=True)
    telecaller = serializers.CharField(required=False, allow_blank=True)
    volunteer_role = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=500)
