"""
Benchmarking utilities to measure API performance with charts and comprehensive testing
"""
import time
import json
import gc
import random
from datetime import datetime
from pathlib import Path
from django.db import connection, reset_queries
from django.db.utils import OperationalError
from django.test.utils import override_settings
from contacts.models import AppUser
from contacts.views import ContactViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend to reduce memory
    import matplotlib.pyplot as plt
    import pandas as pd
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False


class NoPagination(PageNumberPagination):
    """Custom pagination class that returns all results without pagination"""
    def paginate_queryset(self, queryset, request, view=None):
        """Override to return None, which disables pagination"""
        return None


class BenchmarkRunner:
    """Utility class to run performance benchmarks"""
    
    def __init__(self):
        self.factory = APIRequestFactory()
        self.results = []
        self.original_pagination = None
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function with error handling"""
        reset_queries()
        start_time = time.time()
        result_obj = None
        status_code = None
        result_count = None
        
        try:
            result_obj = func(*args, **kwargs)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            query_count = len(connection.queries)
            error = None
            
            # Extract only metadata from response, don't store the full object
            if result_obj is not None:
                if hasattr(result_obj, 'status_code'):
                    status_code = result_obj.status_code
                if hasattr(result_obj, 'data'):
                    results_data = result_obj.data
                    if isinstance(results_data, dict) and 'results' in results_data:
                        result_count = len(results_data.get('results', []))
                    elif isinstance(results_data, list):
                        result_count = len(results_data)
            
            # Clear the response object immediately to free memory
            del result_obj
            result_obj = None
            
        except OperationalError as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            error = str(e)
            # Check if it's a timeout error
            if 'timeout' in error.lower() or 'QueryCanceled' in error:
                error = 'TIMEOUT'
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            error = str(e)
        finally:
            # Always clear query logs to prevent memory buildup
            reset_queries()
            # Force garbage collection to free memory
            gc.collect()
        
        return {
            'execution_time_ms': execution_time,
            'query_count': query_count,
            'status_code': status_code,
            'result_count': result_count,
            'error': error
        }
    
    def _setup_pagination(self, use_pagination, page_size=None):
        """Setup pagination for the viewset. Returns view and params."""
        if use_pagination:
            # Use default pagination
            view = ContactViewSet.as_view({'get': 'list'})
            params = {}
            if page_size:
                params['page_size'] = page_size
            return view, params
        else:
            # Disable pagination by temporarily setting pagination_class to NoPagination
            if self.original_pagination is None:
                self.original_pagination = getattr(ContactViewSet, 'pagination_class', None)
            ContactViewSet.pagination_class = NoPagination
            view = ContactViewSet.as_view({'get': 'list'})
            return view, {}
    
    def _restore_pagination(self):
        """Restore original pagination settings"""
        if self.original_pagination is not None:
            ContactViewSet.pagination_class = self.original_pagination
            self.original_pagination = None
    
    def _cleanup_after_test(self):
        """Clean up resources after each test to prevent memory buildup"""
        reset_queries()
        gc.collect()
    
    def _run_benchmark_with_cleanup(self, benchmark_func, *args, **kwargs):
        """Run a benchmark function and clean up resources afterward"""
        try:
            return benchmark_func(*args, **kwargs)
        finally:
            self._cleanup_after_test()
    
    def _print_result(self, result):
        """Helper method to print benchmark results consistently"""
        print(f"Execution Time: {result['execution_time_ms']:.2f} ms")
        print(f"Query Count: {result['query_count']}")
        
        if result.get('error'):
            if result['error'] == 'TIMEOUT':
                print(f"⚠️  ERROR: Query timed out (exceeded statement timeout)")
            else:
                print(f"⚠️  ERROR: {result['error']}")
        else:
            if result.get('status_code'):
                print(f"Status Code: {result['status_code']}")
            if result.get('result_count') is not None:
                print(f"Results Count: {result['result_count']}")
    
    def benchmark_initial_list(self, page_size=50, use_pagination=True):
        """Benchmark: Load initial list with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Initial List Load ({pagination_label}, page_size={page_size})")
        print(f"{'='*80}")
        
        view, params = self._setup_pagination(use_pagination, page_size)
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'initial_list_load',
            'use_pagination': use_pagination,
            'page_size': page_size,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_filter_by_name(self, name="John", use_pagination=True):
        """Benchmark: Filter by name with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Filter by Name ({pagination_label}, name='{name}')")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {'first_name__icontains': name, **base_params}
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'filter_by_name',
            'use_pagination': use_pagination,
            'filter_value': name,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_sort_by_attribute(self, ordering='-created', use_pagination=True):
        """Benchmark: Sort by attribute with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Sort by Attribute ({pagination_label}, ordering='{ordering}')")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {'ordering': ordering, **base_params}
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'sort_by_attribute',
            'use_pagination': use_pagination,
            'ordering': ordering,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_filter_and_sort(self, filter_field='city', filter_value='New York', ordering='-relationship__points', use_pagination=True):
        """Benchmark: Combined filter and sort with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Filter + Sort ({pagination_label}, filter: {filter_field}={filter_value}, order: {ordering})")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {
            f'address__{filter_field}__icontains': filter_value,
            'ordering': ordering,
            **base_params
        }
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'filter_and_sort',
            'use_pagination': use_pagination,
            'filter_field': filter_field,
            'filter_value': filter_value,
            'ordering': ordering,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_complex_query(self, use_pagination=True):
        """Benchmark: Complex query with multiple filters with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Complex Query ({pagination_label}, multiple filters)")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {
            'gender': 'M',
            'relationship__points__gte': 1000,
            'address__country__icontains': 'United',
            'ordering': '-relationship__last_activity',
            **base_params
        }
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'complex_query',
            'use_pagination': use_pagination,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_multi_field_sort(self, ordering='-relationship__points,last_name,first_name', use_pagination=True):
        """Benchmark: Multi-field sorting with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Multi-Field Sort ({pagination_label}, ordering='{ordering}')")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {'ordering': ordering, **base_params}
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'multi_field_sort',
            'use_pagination': use_pagination,
            'ordering': ordering,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_multiple_filters(self, use_pagination=True):
        """Benchmark: Multiple filters combined with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Multiple Filters ({pagination_label}, gender + points + country)")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {
            'gender': 'M',
            'relationship__points__gte': 5000,
            'address__country__icontains': 'United',
            **base_params
        }
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'multiple_filters',
            'use_pagination': use_pagination,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def benchmark_search(self, search_term="John", use_pagination=True):
        """Benchmark: Search across multiple fields with or without pagination"""
        pagination_label = "with pagination" if use_pagination else "without pagination"
        print(f"\n{'='*80}")
        print(f"Benchmark: Search ({pagination_label}, search='{search_term}')")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(use_pagination)
        params = {'search': search_term, **base_params}
        
        request = self.factory.get('/api/contacts/', params)
        
        def run_query():
            response = view(request)
            return response
        
        result = self.measure_time(run_query)
        self._restore_pagination()
        
        self.results.append({
            'test': 'search',
            'use_pagination': use_pagination,
            'search_term': search_term,
            **result
        })
        
        self._print_result(result)
        
        return result
    
    def _fetch_page(self, view, params, page_num):
        """Helper method to fetch a single page and return metrics"""
        request = self.factory.get('/api/contacts/', params)
        
        reset_queries()
        start_time = time.time()
        response_obj = None
        
        try:
            response_obj = view(request)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            status_code = response_obj.status_code if hasattr(response_obj, 'status_code') else None
            
            # Extract pagination info and result count
            result_count = 0
            total_count = 0
            has_next = False
            
            if hasattr(response_obj, 'data'):
                data = response_obj.data
                if isinstance(data, dict):
                    if 'results' in data:
                        result_count = len(data.get('results', []))
                        has_next = data.get('next') is not None
                        total_count = data.get('count', 0)
                elif isinstance(data, list):
                    result_count = len(data)
            
            error = None
        except OperationalError as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            error = str(e)
            if 'timeout' in error.lower() or 'QueryCanceled' in error:
                error = 'TIMEOUT'
            status_code = None
            result_count = 0
            total_count = 0
            has_next = False
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            error = str(e)
            status_code = None
            result_count = 0
            total_count = 0
            has_next = False
        finally:
            # Clear response and force cleanup
            if response_obj is not None:
                del response_obj
            reset_queries()
            gc.collect()
        
        return {
            'page': page_num,
            'execution_time_ms': execution_time,
            'query_count': query_count,
            'result_count': result_count,
            'status_code': status_code,
            'error': error,
            'total_count': total_count,
            'has_next': has_next,
        }
    
    def benchmark_pagination_all_pages(self, page_size=50, additional_params=None, num_random_pages=10):
        """Benchmark: Fetch first page, middle page, last page, and random pages"""
        print(f"\n{'='*80}")
        print(f"Benchmark: Pagination - Selected Pages (page_size={page_size})")
        print(f"{'='*80}")
        
        view, base_params = self._setup_pagination(True, page_size)
        if additional_params:
            base_params.update(additional_params)
        
        page_results = []
        start_time_total = time.time()
        
        print(f"\nStep 1: Fetching page 1 to determine total pages...")
        
        # Step 1: Fetch page 1 to get total page count
        params = {**base_params, 'page': 1}
        first_page_result = self._fetch_page(view, params, 1)
        
        if first_page_result.get('error'):
            print(f"\n⚠️  Error fetching page 1: {first_page_result['error']}")
            self._restore_pagination()
            return None
        
        page_results.append(first_page_result)
        total_count = first_page_result.get('total_count', 0)
        
        if total_count == 0:
            print(f"\n⚠️  No items found in the database")
            self._restore_pagination()
            return None
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        print(f"Total items: {total_count}, Total pages: {total_pages}")
        
        if total_pages <= 1:
            print(f"\nOnly 1 page available. Skipping additional page tests.")
            self._restore_pagination()
            # Return summary for single page
            summary_result = {
                'test': 'pagination_selected_pages',
                'page_size': page_size,
                'total_pages': 1,
                'total_items': total_count,
                'pages_tested': [1],
                'page_results': page_results,
            }
            self.results.append(summary_result)
            return summary_result
        
        # Determine pages to test
        pages_to_test = [1]  # First page (already fetched)
        
        # Middle page
        middle_page = (total_pages + 1) // 2
        if middle_page != 1:
            pages_to_test.append(middle_page)
        
        # Last page
        last_page = total_pages
        if last_page != 1 and last_page != middle_page:
            pages_to_test.append(last_page)
        
        # Select random pages (excluding first, middle, last)
        available_pages = [p for p in range(2, total_pages + 1) 
                          if p not in pages_to_test]
        
        if len(available_pages) > 0:
            num_random = min(num_random_pages, len(available_pages))
            random_pages = sorted(random.sample(available_pages, num_random))
            pages_to_test.extend(random_pages)
        
        pages_to_test = sorted(set(pages_to_test))  # Remove duplicates and sort
        
        print(f"\nStep 2: Testing selected pages: {pages_to_test}")
        print(f"Pages to test: First (1), Middle ({middle_page}), Last ({last_page}), "
              f"Random ({len(pages_to_test) - 3} pages)")
        
        # Fetch remaining pages
        for page_num in pages_to_test:
            if page_num == 1:
                continue  # Already fetched
            
            params = {**base_params, 'page': page_num}
            page_result = self._fetch_page(view, params, page_num)
            
            if page_result.get('error'):
                print(f"⚠️  Error on page {page_num}: {page_result['error']}")
            else:
                page_results.append(page_result)
                print(f"Page {page_num}: {page_result['execution_time_ms']:.2f} ms, "
                      f"{page_result['result_count']} items, {page_result['query_count']} queries")
            
            # Cleanup after each page
            self._cleanup_after_test()
        
        end_time_total = time.time()
        total_time = (end_time_total - start_time_total) * 1000
        
        self._restore_pagination()
        
        # Generate summary
        if page_results:
            total_queries = sum(r['query_count'] for r in page_results)
            avg_time_per_page = sum(r['execution_time_ms'] for r in page_results) / len(page_results)
            min_time = min(r['execution_time_ms'] for r in page_results)
            max_time = max(r['execution_time_ms'] for r in page_results)
            avg_queries_per_page = total_queries / len(page_results)
            total_items_fetched = sum(r['result_count'] for r in page_results)
            
            print(f"\n{'='*80}")
            print(f"PAGINATION BENCHMARK SUMMARY")
            print(f"{'='*80}")
            print(f"Total Pages Available: {total_pages}")
            print(f"Pages Tested: {len(page_results)} ({', '.join(map(str, pages_to_test))})")
            print(f"Total Items in Database: {total_count}")
            print(f"Total Items Fetched: {total_items_fetched}")
            print(f"Total Time: {total_time:.2f} ms ({total_time/1000:.2f} seconds)")
            print(f"Average Time per Page: {avg_time_per_page:.2f} ms")
            print(f"Min Time per Page: {min_time:.2f} ms")
            print(f"Max Time per Page: {max_time:.2f} ms")
            print(f"Total Queries: {total_queries}")
            print(f"Average Queries per Page: {avg_queries_per_page:.2f}")
            print(f"Average Items per Page: {total_items_fetched / len(page_results):.2f}")
            print(f"{'='*80}")
            
            # Store summary in results
            summary_result = {
                'test': 'pagination_selected_pages',
                'page_size': page_size,
                'total_pages_available': total_pages,
                'pages_tested': pages_to_test,
                'total_items': total_count,
                'total_items_fetched': total_items_fetched,
                'total_time_ms': total_time,
                'avg_time_per_page_ms': avg_time_per_page,
                'min_time_per_page_ms': min_time,
                'max_time_per_page_ms': max_time,
                'total_queries': total_queries,
                'avg_queries_per_page': avg_queries_per_page,
                'page_results': page_results,
            }
            
            self.results.append(summary_result)
            
            return summary_result
        else:
            print(f"\n⚠️  No pages were successfully fetched")
            return None
    
    def run_all_benchmarks(self):
        """Run all benchmark tests with pagination"""
        print("\n" + "="*80)
        print("RUNNING ALL BENCHMARKS (WITH PAGINATION)")
        print("="*80)
        
        # Get sample data from the database (only what we need, not full objects)
        sample_user_first_name = None
        sample_address_city = None
        try:
            sample_user = AppUser.objects.only('first_name').first()
            if sample_user:
                sample_user_first_name = sample_user.first_name
            sample_address = AppUser.objects.select_related('address').only('address__city').exclude(address__isnull=True).first()
            if sample_address and sample_address.address:
                sample_address_city = sample_address.address.city
            # Clear references immediately
            del sample_user, sample_address
            gc.collect()
        except Exception:
            pass
        
        # Run benchmarks
        print("\n" + "="*80)
        print("RUNNING BENCHMARKS")
        print("="*80)
        
        self.benchmark_initial_list(page_size=1000, use_pagination=True)
        
        if sample_user_first_name:
            self.benchmark_filter_by_name(sample_user_first_name, use_pagination=True)
        
        # Single field sorting
        self.benchmark_sort_by_attribute('-created', use_pagination=True)
        self.benchmark_sort_by_attribute('relationship__points', use_pagination=True)
        self.benchmark_sort_by_attribute('address__city', use_pagination=True)
        
        # Multi-field sorting
        self.benchmark_multi_field_sort('-relationship__points,last_name,first_name', use_pagination=True)
        self.benchmark_multi_field_sort('address__country,address__city,-created', use_pagination=True)
        
        if sample_address_city:
            self.benchmark_filter_and_sort('city', sample_address_city, '-relationship__points', use_pagination=True)
        
        # Multiple filters
        self.benchmark_multiple_filters(use_pagination=True)
        
        # Search
        if sample_user_first_name:
            self.benchmark_search(sample_user_first_name, use_pagination=True)
        
        # Complex query
        self.benchmark_complex_query(use_pagination=True)
        
        # Run pagination benchmark (selected pages)
        print("\n" + "="*80)
        print("RUNNING PAGINATION BENCHMARK (SELECTED PAGES)")
        print("="*80)
        self.benchmark_pagination_all_pages(page_size=1000)
        
        # Print summary
        self.print_summary()
        
        # Generate charts and export results
        self.generate_charts()
        self.export_results()
        self.export_pagination_report()
        
        # Final cleanup
        self._cleanup_after_test()
    
    def print_summary(self):
        """Print summary of all benchmark results"""
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        # Group results by test and pagination
        for result in self.results:
            test_name = result.get('test', 'unknown')
            
            # Handle pagination benchmark results differently
            if test_name in ['pagination_all_pages', 'pagination_selected_pages']:
                pagination = "WITH pagination"
                print(f"\n{test_name} ({pagination}):")
                print(f"  Total Pages Available: {result.get('total_pages_available', result.get('total_pages', 'N/A'))}")
                print(f"  Pages Tested: {len(result.get('pages_tested', result.get('page_results', [])))}")
                print(f"  Total Time: {result.get('total_time_ms', 0):.2f} ms")
                print(f"  Average Time per Page: {result.get('avg_time_per_page_ms', 0):.2f} ms")
                print(f"  Total Queries: {result.get('total_queries', 0)}")
                print(f"  Average Queries per Page: {result.get('avg_queries_per_page', 0):.2f}")
                continue
            
            # Handle regular benchmark results
            pagination = "WITH pagination" if result.get('use_pagination', True) else "WITHOUT pagination"
            print(f"\n{test_name} ({pagination}):")
            
            if 'execution_time_ms' in result:
                print(f"  Execution Time: {result['execution_time_ms']:.2f} ms")
            if 'query_count' in result:
                print(f"  Query Count: {result['query_count']}")
            if result.get('error'):
                if result['error'] == 'TIMEOUT':
                    print(f"  ⚠️  Status: TIMEOUT (query exceeded statement timeout)")
                else:
                    print(f"  ⚠️  Status: ERROR - {result['error'][:100]}")
        
        # Calculate averages by pagination type (excluding errors and pagination benchmark results)
        if self.results:
            # Exclude pagination benchmark results from regular averages
            regular_results = [r for r in self.results 
                             if r.get('test') not in ['pagination_all_pages', 'pagination_selected_pages']]
            
            with_pagination = [r for r in regular_results 
                             if r.get('use_pagination', True) and not r.get('error') 
                             and 'execution_time_ms' in r]
            without_pagination = [r for r in regular_results 
                                if not r.get('use_pagination', True) and not r.get('error')
                                and 'execution_time_ms' in r]
            errors = [r for r in self.results if r.get('error')]
            
            print(f"\n{'='*80}")
            if with_pagination:
                avg_time_with = sum(r['execution_time_ms'] for r in with_pagination) / len(with_pagination)
                avg_queries_with = sum(r['query_count'] for r in with_pagination) / len(with_pagination)
                print(f"WITH Pagination - Average Execution Time: {avg_time_with:.2f} ms")
                print(f"WITH Pagination - Average Query Count: {avg_queries_with:.2f}")
            
            if without_pagination:
                avg_time_without = sum(r['execution_time_ms'] for r in without_pagination) / len(without_pagination)
                avg_queries_without = sum(r['query_count'] for r in without_pagination) / len(without_pagination)
                print(f"WITHOUT Pagination - Average Execution Time: {avg_time_without:.2f} ms")
                print(f"WITHOUT Pagination - Average Query Count: {avg_queries_without:.2f}")
            
            if errors:
                timeout_count = len([r for r in errors if r.get('error') == 'TIMEOUT'])
                print(f"\n⚠️  Errors encountered: {len(errors)} ({timeout_count} timeouts)")
            
            # Overall averages (excluding errors and pagination benchmarks)
            successful_results = [r for r in regular_results 
                               if not r.get('error') and 'execution_time_ms' in r]
            if successful_results:
                avg_time = sum(r['execution_time_ms'] for r in successful_results) / len(successful_results)
                avg_queries = sum(r['query_count'] for r in successful_results) / len(successful_results)
                print(f"\nOverall Average Execution Time: {avg_time:.2f} ms (excluding errors and pagination benchmarks)")
                print(f"Overall Average Query Count: {avg_queries:.2f} (excluding errors and pagination benchmarks)")
            print(f"{'='*80}")
    
    def generate_charts(self):
        """Generate charts from benchmark results"""
        if not HAS_PLOTTING:
            print("\n⚠️  matplotlib/pandas not available. Skipping chart generation.")
            print("   Install with: pip install matplotlib pandas")
            return
        
        if not self.results:
            print("\n⚠️  No results to plot.")
            return
        
        df = None
        try:
            # Create output directory
            output_dir = Path('benchmark_results')
            output_dir.mkdir(exist_ok=True)
            
            # Prepare data (only if needed for processing, not stored)
            # We'll work directly with self.results to avoid creating unnecessary DataFrame
            # Exclude pagination benchmark results as they have a different structure
            regular_results = [r for r in self.results 
                             if r.get('test') not in ['pagination_all_pages', 'pagination_selected_pages']]
            with_pagination = [r for r in regular_results 
                            if r.get('use_pagination', True) and not r.get('error') 
                            and 'execution_time_ms' in r]
            without_pagination = [r for r in regular_results 
                                if not r.get('use_pagination', True) and not r.get('error')
                                and 'execution_time_ms' in r]
            errors = [r for r in self.results if r.get('error')]
            
            # Create a larger figure for more charts
            fig = plt.figure(figsize=(18, 12))
            
            # Define variables for all charts to use
            test_names_with = []
            execution_times_with = []
            query_counts_with = []
            
            if with_pagination:
                test_names_with = [f"{r.get('test', 'unknown')}" for r in with_pagination]
                execution_times_with = [r['execution_time_ms'] for r in with_pagination]
                query_counts_with = [r['query_count'] for r in with_pagination]
            
            # Chart 1: Execution Time by Test (With Pagination)
            plt.subplot(3, 3, 1)
            if with_pagination:
                plt.barh(range(len(test_names_with)), execution_times_with, color='blue', alpha=0.7)
                plt.yticks(range(len(test_names_with)), [name[:30] for name in test_names_with], fontsize=8)
                plt.xlabel('Execution Time (ms)')
                plt.title('Execution Time (WITH Pagination)')
            plt.tight_layout()
            
            # Chart 2: Query Count by Test
            plt.subplot(3, 3, 2)
            if with_pagination:
                plt.barh(range(len(test_names_with)), query_counts_with, color='green', alpha=0.7)
                plt.yticks(range(len(test_names_with)), [name[:30] for name in test_names_with], fontsize=8)
                plt.xlabel('Query Count')
                plt.title('Query Count by Test')
            plt.tight_layout()
            
            # Chart 3: Execution Time vs Query Count
            plt.subplot(3, 3, 3)
            if with_pagination:
                plt.scatter(query_counts_with, execution_times_with, alpha=0.6, color='blue', s=50)
                plt.xlabel('Query Count')
                plt.ylabel('Execution Time (ms)')
                plt.title('Execution Time vs Query Count')
                plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Chart 4: Query Count (With Pagination)
            plt.subplot(3, 3, 4)
            if with_pagination:
                query_counts_with = [r['query_count'] for r in with_pagination]
                plt.barh(range(len(test_names_with)), query_counts_with, color='green', alpha=0.7)
                plt.yticks(range(len(test_names_with)), [name[:30] for name in test_names_with], fontsize=8)
                plt.xlabel('Query Count')
                plt.title('Query Count (WITH Pagination)')
            plt.tight_layout()
            
            # Chart 5: Execution Time by Test Type
            plt.subplot(3, 3, 5)
            if with_pagination:
                # Group by test type
                test_types = {}
                for r in with_pagination:
                    test_name = r.get('test', 'unknown')
                    if test_name not in test_types:
                        test_types[test_name] = []
                    test_types[test_name].append(r['execution_time_ms'])
                
                # Calculate average for each test type
                test_names = list(test_types.keys())
                avg_times = [sum(test_types[t]) / len(test_types[t]) for t in test_names]
                
                plt.bar(range(len(test_names)), avg_times, color='purple', alpha=0.7)
                plt.xlabel('Test Type')
                plt.ylabel('Avg Execution Time (ms)')
                plt.title('Average Time by Test Type')
                plt.xticks(range(len(test_names)), [name[:15] for name in test_names], rotation=45, ha='right', fontsize=8)
            plt.tight_layout()
            
            # Chart 6: Execution Time Distribution
            plt.subplot(3, 3, 6)
            all_execution_times = [r['execution_time_ms'] for r in regular_results if 'execution_time_ms' in r]
            if all_execution_times:
                plt.hist(all_execution_times, bins=15, edgecolor='black', alpha=0.7)
                plt.xlabel('Execution Time (ms)')
                plt.ylabel('Frequency')
                plt.title('Execution Time Distribution (All Tests)')
            plt.tight_layout()
            
            # Chart 7: Query Count vs Execution Time (With Pagination)
            plt.subplot(3, 3, 7)
            if with_pagination:
                plt.scatter(query_counts_with, execution_times_with, alpha=0.6, color='blue', label='With Pagination')
                plt.xlabel('Query Count')
                plt.ylabel('Execution Time (ms)')
                plt.title('Query Count vs Execution Time (WITH)')
                plt.legend()
            plt.tight_layout()
            
            # Chart 8: Query Count Distribution
            plt.subplot(3, 3, 8)
            if with_pagination:
                plt.hist(query_counts_with, bins=min(15, len(set(query_counts_with))), edgecolor='black', alpha=0.7, color='orange')
                plt.xlabel('Query Count')
                plt.ylabel('Frequency')
                plt.title('Query Count Distribution')
                plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            
            # Chart 9: Summary Statistics
            plt.subplot(3, 3, 9)
            if with_pagination:
                avg_time = sum(execution_times_with) / len(execution_times_with)
                avg_queries = sum(query_counts_with) / len(query_counts_with)
                min_time = min(execution_times_with)
                max_time = max(execution_times_with)
                
                categories = ['Avg Time\n(ms)', 'Avg Queries', 'Min Time\n(ms)', 'Max Time\n(ms)']
                values = [avg_time, avg_queries, min_time, max_time]
                
                # Normalize values for display (show actual values as text)
                normalized_values = [v / max(values) if max(values) > 0 else 0 for v in values]
                
                bars = plt.bar(range(len(categories)), normalized_values, color='teal', alpha=0.7)
                plt.xlabel('Metric')
                plt.ylabel('Normalized Value')
                plt.title('Summary Statistics')
                plt.xticks(range(len(categories)), categories, fontsize=8)
                
                # Add value labels on bars
                for i, (bar, val) in enumerate(zip(bars, values)):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{val:.1f}' if i != 1 else f'{val:.0f}',
                            ha='center', va='bottom', fontsize=7)
            plt.tight_layout()
            
            # Save chart
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            chart_path = output_dir / f'benchmark_charts_{timestamp}.png'
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close(fig)  # Explicitly close the figure
            plt.clf()  # Clear the current figure
            del fig  # Delete the figure object
            gc.collect()  # Force garbage collection
            
            print(f"\n✅ Charts saved to: {chart_path}")
            
        except Exception as e:
            print(f"\n⚠️  Error generating charts: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure cleanup even if there's an error
            try:
                plt.close('all')  # Close all figures
                gc.collect()
            except:
                pass
    
    def export_results(self):
        """Export benchmark results to JSON and CSV"""
        if not self.results:
            print("\n⚠️  No results to export.")
            return
        
        try:
            # Create output directory
            output_dir = Path('benchmark_results')
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export to JSON
            json_path = output_dir / f'benchmark_results_{timestamp}.json'
            with open(json_path, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"✅ JSON results saved to: {json_path}")
            
            # Export to CSV if pandas is available
            if HAS_PLOTTING:
                df = None
                try:
                    df = pd.DataFrame(self.results)
                    csv_path = output_dir / f'benchmark_results_{timestamp}.csv'
                    df.to_csv(csv_path, index=False)
                    print(f"✅ CSV results saved to: {csv_path}")
                except Exception as e:
                    print(f"⚠️  Error exporting CSV: {e}")
                finally:
                    # Clean up DataFrame
                    if df is not None:
                        del df
                        gc.collect()
            
        except Exception as e:
            print(f"⚠️  Error exporting results: {e}")
        finally:
            # Final cleanup
            gc.collect()
    
    def export_pagination_report(self):
        """Export detailed pagination benchmark report"""
        # Find pagination benchmark results (both old and new test names)
        pagination_results = [r for r in self.results 
                            if r.get('test') in ['pagination_all_pages', 'pagination_selected_pages']]
        
        if not pagination_results:
            print("\n⚠️  No pagination benchmark results to export.")
            return
        
        try:
            # Create output directory
            output_dir = Path('benchmark_results')
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for pag_result in pagination_results:
                page_size = pag_result.get('page_size', 50)
                page_results = pag_result.get('page_results', [])
                
                if not page_results:
                    continue
                
                # Export detailed page-by-page report to JSON
                report_data = {
                    'summary': {
                        'page_size': page_size,
                        'total_pages_available': pag_result.get('total_pages_available', pag_result.get('total_pages', 0)),
                        'pages_tested': pag_result.get('pages_tested', []),
                        'total_items': pag_result.get('total_items', 0),
                        'total_items_fetched': pag_result.get('total_items_fetched', pag_result.get('total_items', 0)),
                        'total_time_ms': pag_result.get('total_time_ms', 0),
                        'avg_time_per_page_ms': pag_result.get('avg_time_per_page_ms', 0),
                        'min_time_per_page_ms': pag_result.get('min_time_per_page_ms', 0),
                        'max_time_per_page_ms': pag_result.get('max_time_per_page_ms', 0),
                        'total_queries': pag_result.get('total_queries', 0),
                        'avg_queries_per_page': pag_result.get('avg_queries_per_page', 0),
                    },
                    'pages': page_results
                }
                
                json_path = output_dir / f'pagination_report_page_size_{page_size}_{timestamp}.json'
                with open(json_path, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                print(f"✅ Pagination report saved to: {json_path}")
                
                # Export to CSV if pandas is available
                if HAS_PLOTTING:
                    try:
                        df_pages = pd.DataFrame(page_results)
                        csv_path = output_dir / f'pagination_report_page_size_{page_size}_{timestamp}.csv'
                        df_pages.to_csv(csv_path, index=False)
                        print(f"✅ Pagination CSV report saved to: {csv_path}")
                        del df_pages
                        gc.collect()
                    except Exception as e:
                        print(f"⚠️  Error exporting pagination CSV: {e}")
                
                # Generate a chart for pagination performance
                if HAS_PLOTTING and page_results:
                    try:
                        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                        
                        # Chart 1: Execution time per page
                        pages = [r['page'] for r in page_results]
                        times = [r['execution_time_ms'] for r in page_results]
                        axes[0, 0].plot(pages, times, marker='o', linestyle='-', color='blue')
                        axes[0, 0].set_xlabel('Page Number')
                        axes[0, 0].set_ylabel('Execution Time (ms)')
                        axes[0, 0].set_title('Execution Time per Page')
                        axes[0, 0].grid(True, alpha=0.3)
                        
                        # Chart 2: Query count per page
                        queries = [r['query_count'] for r in page_results]
                        axes[0, 1].plot(pages, queries, marker='s', linestyle='-', color='green')
                        axes[0, 1].set_xlabel('Page Number')
                        axes[0, 1].set_ylabel('Query Count')
                        axes[0, 1].set_title('Query Count per Page')
                        axes[0, 1].grid(True, alpha=0.3)
                        
                        # Chart 3: Items per page
                        items = [r['result_count'] for r in page_results]
                        axes[1, 0].bar(pages, items, color='orange', alpha=0.7)
                        axes[1, 0].set_xlabel('Page Number')
                        axes[1, 0].set_ylabel('Items Count')
                        axes[1, 0].set_title('Items per Page')
                        axes[1, 0].grid(True, alpha=0.3, axis='y')
                        
                        # Chart 4: Execution time distribution
                        axes[1, 1].hist(times, bins=min(20, len(times)), edgecolor='black', alpha=0.7, color='purple')
                        axes[1, 1].set_xlabel('Execution Time (ms)')
                        axes[1, 1].set_ylabel('Frequency')
                        axes[1, 1].set_title('Execution Time Distribution')
                        axes[1, 1].grid(True, alpha=0.3, axis='y')
                        
                        plt.tight_layout()
                        chart_path = output_dir / f'pagination_charts_page_size_{page_size}_{timestamp}.png'
                        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                        plt.close(fig)
                        plt.clf()
                        del fig
                        gc.collect()
                        
                        print(f"✅ Pagination charts saved to: {chart_path}")
                    except Exception as e:
                        print(f"⚠️  Error generating pagination charts: {e}")
                        import traceback
                        traceback.print_exc()
            
        except Exception as e:
            print(f"⚠️  Error exporting pagination report: {e}")
            import traceback
            traceback.print_exc()
        finally:
            gc.collect()


def run_benchmarks():
    """Convenience function to run all benchmarks"""
    runner = BenchmarkRunner()
    runner.run_all_benchmarks()
    return runner.results

