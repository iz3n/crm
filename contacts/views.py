"""
API views for contacts with filtering, sorting, and pagination
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.core.exceptions import RequestAborted
from contacts.models import AppUser, Address, CustomerRelationship
from contacts.serializers import ContactListSerializer
from contacts.mixins import QueryCancellationMixin


class ContactViewSet(QueryCancellationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving contacts with filtering, sorting, and pagination.
    
    Features:
    - Filtering by any field from AppUser, Address, or CustomerRelationship
    - Single and multi-field sorting (comma-separated fields)
    - Pagination support
    - Query cancellation and timeout
    
    Sorting Examples:
    - Single field: ?ordering=-created
    - Multiple fields: ?ordering=-relationship__points,last_name,first_name
    - Mix ascending/descending: ?ordering=-points,created (points DESC, then created ASC)
    """
    queryset = AppUser.objects.select_related('address', 'relationship').all()
    serializer_class = ContactListSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    query_timeout = 30  # Query timeout in seconds (configurable)
    
    # Define filterable fields from all 3 tables
    filterset_fields = {
        # AppUser fields
        'id': ['exact'],
        'first_name': ['icontains'],
        'last_name': ['icontains'],
        'gender': ['exact'],
        'customer_id': ['icontains'],
        'phone_number': ['exact', 'icontains'],
        'created': ['exact', 'gte', 'lte', 'gt', 'lt'],
        'birthday': ['exact', 'gte', 'lte'],
        'last_updated': ['exact', 'gte', 'lte', 'gt', 'lt'],
        # Address fields (via ForeignKey relationship)
        'address__id': ['exact'],
        'address__street': ['exact', 'icontains'],
        'address__city': ['exact', 'icontains'],
        'address__city_code': ['exact', 'icontains'],
        'address__country': ['exact', 'icontains'],
        # CustomerRelationship fields (via relationship)
        'relationship__points': ['exact', 'gte', 'lte', 'gt', 'lt'],
        'relationship__created': ['exact', 'gte', 'lte', 'gt', 'lt'],
        'relationship__last_activity': ['exact', 'gte', 'lte', 'gt', 'lt'],
    }
    
    # Define searchable fields (for search parameter)
    search_fields = [
        'first_name', 'last_name', 'customer_id', 'phone_number',
        'address__street', 'address__city', 'address__country',
    ]
    
    # Define sortable fields (supports single and multi-field sorting)
    # Example: ?ordering=-relationship__points,last_name,first_name
    ordering_fields = [
        # AppUser fields
        'id', 'first_name', 'last_name', 'gender', 'customer_id',
        'phone_number', 'created', 'birthday', 'last_updated',
        # Address fields
        'address__city', 'address__country', 'address__city_code',
        # CustomerRelationship fields
        'relationship__points', 'relationship__created', 'relationship__last_activity',
    ]
    ordering = ['-created']  # Default ordering (can be list for multi-field default)
    
    def get_queryset(self):
        """
        Optimize queryset with select_related to avoid N+1 queries.
        Includes cancellation token support.
        """
        # Check for cancellation before executing query
        self.check_cancellation(self.request)
        
        queryset = AppUser.objects.select_related('address', 'relationship').all()
        
        # Additional custom filtering can be added here if needed
        # For example, filtering by name combination
        name_filter = self.request.query_params.get('name', None)
        if name_filter:
            queryset = queryset.filter(
                Q(first_name__icontains=name_filter) | Q(last_name__icontains=name_filter)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to add cancellation context.
        """
        # Check for cancellation token
        cancellation_token = self._get_query_param(request, '_cancel')
        if cancellation_token:
            request._cancelled = True
            return Response(
                {'detail': 'Request cancelled'},
                status=499  # Client Closed Request
            )
        
        with self.get_cancellation_context(request):
            return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to add cancellation context.
        """
        # Check for cancellation token
        cancellation_token = self._get_query_param(request, '_cancel')
        if cancellation_token:
            request._cancelled = True
            return Response(
                {'detail': 'Request cancelled'},
                status=499  # Client Closed Request
            )
        
        with self.get_cancellation_context(request):
            return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint to get statistics about the contacts.
        Includes cancellation support.
        """
        # Check for cancellation token
        cancellation_token = self._get_query_param(request, '_cancel')
        if cancellation_token:
            request._cancelled = True
            return Response(
                {'detail': 'Request cancelled'},
                status=499  # Client Closed Request
            )
        
        with self.get_cancellation_context(request):
            total_count = AppUser.objects.count()
            with_address = AppUser.objects.exclude(address__isnull=True).count()
            with_relationship = AppUser.objects.exclude(relationship__isnull=True).count()
            
            return Response({
                'total_contacts': total_count,
                'contacts_with_address': with_address,
                'contacts_with_relationship': with_relationship,
            })

