from rest_framework import serializers
from contacts.models import AppUser, Address, CustomerRelationship


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""
    class Meta:
        model = Address
        fields = "__all__"


class CustomerRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for CustomerRelationship model"""
    class Meta:
        model = CustomerRelationship
        fields = "__all__"


class AppUserSerializer(serializers.ModelSerializer):
    """Serializer for AppUser with related Address and CustomerRelationship"""
    address = AddressSerializer(read_only=True)
    relationship = CustomerRelationshipSerializer(source='relationship', read_only=True)
    
    class Meta:
        model = AppUser
        fields = "__all__"


class ContactListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for list views that includes all fields from all 3 tables
    """
    # Address fields
    address_id = serializers.IntegerField(source='address.id', read_only=True, allow_null=True)
    street = serializers.CharField(source='address.street', read_only=True, allow_null=True)
    street_number = serializers.CharField(source='address.street_number', read_only=True, allow_null=True)
    city_code = serializers.CharField(source='address.city_code', read_only=True, allow_null=True)
    city = serializers.CharField(source='address.city', read_only=True, allow_null=True)
    country = serializers.CharField(source='address.country', read_only=True, allow_null=True)
    
    # CustomerRelationship fields
    relationship_id = serializers.IntegerField(source='relationship.id', read_only=True)
    points = serializers.IntegerField(source='relationship.points', read_only=True)
    relationship_created = serializers.DateTimeField(source='relationship.created', read_only=True)
    last_activity = serializers.DateTimeField(source='relationship.last_activity', read_only=True)
    
    class Meta:
        model = AppUser
        fields = [
            # AppUser fields
            'id', 'first_name', 'last_name', 'gender', 'customer_id',
            'phone_number', 'created', 'birthday', 'last_updated',
            # Address fields
            'address_id', 'street', 'street_number', 'city_code', 'city', 'country',
            # CustomerRelationship fields
            'relationship_id', 'points', 'relationship_created', 'last_activity',
        ]

