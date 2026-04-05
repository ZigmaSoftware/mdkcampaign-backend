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


class TaskDashboardFilterSerializer(serializers.Serializer):
    from_date = serializers.DateField(required=False)
    to_date = serializers.DateField(required=False)
    task_type = serializers.CharField(required=False, allow_blank=True)
    task_category = serializers.CharField(required=False, allow_blank=True)
    module = serializers.ChoiceField(required=False, choices=['task', 'campaign'], allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=200)
