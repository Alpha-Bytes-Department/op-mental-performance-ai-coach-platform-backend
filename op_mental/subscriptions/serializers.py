from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'name', 'description', 'features', 'recommended', 'price',
            'currency', 'duration_days', 'stripe_price_id', 'status',
            'created_at', 'updated_at'
        )

    def get_features(self, obj):
        """Split the feature string by newline, filter out empty lines."""
        if obj.features:
            return [feature.strip() for feature in obj.features.split('\n') if feature.strip()]
        return []

    def get_currency(self, obj):
        """Return a fixed currency value."""
        return "USD"

    def get_status(self, obj):
        """Return a fixed status for the plan."""
        return "active"

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
