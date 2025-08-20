from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = '__all__'

    def get_plan_name(self, obj):
        return obj.plan.name

class CreateUserSubscriptionSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all(), source='plan')

    class Meta:
        model = UserSubscription
        fields = ['plan_id']

    def create(self, validated_data):
        user = self.context['request'].user
        plan = validated_data['plan']
        return UserSubscription.objects.create(user=user, plan=plan)
