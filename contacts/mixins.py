"""
Mixin classes for query cancellation and timeout support
"""
import threading
import signal
import time
from django.db import connection
from django.core.exceptions import RequestAborted
try:
    from rest_framework.response import Response
    from rest_framework import status
except ImportError:
    # Fallback if DRF is not installed (shouldn't happen in production)
    Response = None
    status = None


class QueryCancellationMixin:
    """
    Mixin to support query cancellation tokens for long-running queries.
    
    Usage:
        class MyViewSet(QueryCancellationMixin, ViewSet):
            query_timeout = 30  # seconds
            
            def list(self, request):
                with self.get_cancellation_context(request):
                    queryset = self.get_queryset()
                    # ... perform queries
    """
    query_timeout = 30  # Default timeout in seconds
    enable_cancellation = True
    
    def get_cancellation_context(self, request):
        """
        Returns a context manager for query cancellation.
        Checks for cancellation token in request and sets query timeout.
        """
        return QueryCancellationContext(
            request=request,
            timeout=self.query_timeout,
            enable_cancellation=self.enable_cancellation
        )
    
    def check_cancellation(self, request):
        """
        Check if the request has been cancelled.
        Raises RequestAborted if cancelled.
        """
        if hasattr(request, '_cancelled') and request._cancelled:
            raise RequestAborted("Request was cancelled")
    
    def _get_query_param(self, request, param_name, default=None):
        """
        Get query parameter from either DRF Request or Django WSGIRequest.
        """
        if hasattr(request, 'query_params'):
            # DRF Request object
            return request.query_params.get(param_name, default)
        else:
            # Django WSGIRequest object
            return request.GET.get(param_name, default)


class QueryCancellationContext:
    """
    Context manager for query cancellation and timeout.
    """
    def __init__(self, request, timeout=30, enable_cancellation=True):
        self.request = request
        self.timeout = timeout
        self.enable_cancellation = enable_cancellation
        self.start_time = None
        self._cancelled = False
        
    def __enter__(self):
        self.start_time = time.time()
        
        # Set database query timeout if supported
        if self.enable_cancellation and self.timeout:
            self._set_query_timeout(self.timeout)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset query timeout
        if self.enable_cancellation:
            self._reset_query_timeout()
        
        # Check if timeout was exceeded
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout:
                raise TimeoutError(f"Query exceeded timeout of {self.timeout} seconds")
        
        # Check if request was cancelled
        if hasattr(self.request, '_cancelled') and self.request._cancelled:
            raise RequestAborted("Request was cancelled")
        
        return False
    
    def _set_query_timeout(self, timeout):
        """
        Set query timeout at database level.
        This works for PostgreSQL. For SQLite, we rely on application-level timeout.
        """
        db_engine = connection.vendor
        with connection.cursor() as cursor:
            if db_engine == 'postgresql':
                # PostgreSQL statement timeout
                cursor.execute(f"SET statement_timeout = {int(timeout * 1000)}")  # milliseconds
            elif db_engine == 'mysql':
                # MySQL query timeout
                cursor.execute(f"SET SESSION max_execution_time = {int(timeout * 1000)}")  # milliseconds
            # SQLite doesn't support statement timeout, so we rely on application-level checks
    
    def _reset_query_timeout(self):
        """
        Reset query timeout to default.
        """
        db_engine = connection.vendor
        with connection.cursor() as cursor:
            if db_engine == 'postgresql':
                cursor.execute("SET statement_timeout = DEFAULT")
            elif db_engine == 'mysql':
                cursor.execute("SET SESSION max_execution_time = DEFAULT")
    
    def check_cancellation(self):
        """
        Check if cancellation was requested.
        """
        if hasattr(self.request, '_cancelled') and self.request._cancelled:
            raise RequestAborted("Request was cancelled")
        
        # Check timeout
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout:
                raise TimeoutError(f"Query exceeded timeout of {self.timeout} seconds")


class AsyncQueryCancellationMixin:
    """
    Mixin for async views with cancellation token support.
    Requires Django 3.1+ with async views.
    """
    query_timeout = 30
    
    async def get_cancellation_context(self, request):
        """
        Returns an async context manager for query cancellation.
        """
        return AsyncQueryCancellationContext(
            request=request,
            timeout=self.query_timeout
        )


class AsyncQueryCancellationContext:
    """
    Async context manager for query cancellation.
    """
    def __init__(self, request, timeout=30):
        self.request = request
        self.timeout = timeout
        self.start_time = None
        
    async def __aenter__(self):
        import asyncio
        self.start_time = time.time()
        self.task = asyncio.current_task()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Check if cancelled
        if hasattr(self.request, '_cancelled') and self.request._cancelled:
            raise RequestAborted("Request was cancelled")
        
        # Check timeout
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout:
                raise TimeoutError(f"Query exceeded timeout of {self.timeout} seconds")
        
        return False

