"""
Management command to run performance benchmarks
Usage: python manage.py benchmark [--no-charts] [--no-export]
"""
from django.core.management.base import BaseCommand
from contacts.benchmarks import BenchmarkRunner


class Command(BaseCommand):
    help = 'Run performance benchmarks for the contacts API with charts and comprehensive testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-charts',
            action='store_true',
            help='Skip chart generation',
        )
        parser.add_argument(
            '--no-export',
            action='store_true',
            help='Skip exporting results to files',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive benchmarks...'))
        self.stdout.write('This will test:')
        self.stdout.write('  - Initial list loads (pagination)')
        self.stdout.write('  - Single field filtering')
        self.stdout.write('  - Multiple filters')
        self.stdout.write('  - Single field sorting')
        self.stdout.write('  - Multi-field sorting')
        self.stdout.write('  - Combined filter + sort')
        self.stdout.write('  - Search functionality')
        self.stdout.write('  - Complex queries')
        self.stdout.write('')
        
        runner = BenchmarkRunner()
        runner.run_all_benchmarks()
        
        # Generate charts unless disabled
        if not options.get('no_charts', False):
            runner.generate_charts()
        else:
            self.stdout.write(self.style.WARNING('Skipping chart generation'))
        
        # Export results unless disabled
        if not options.get('no_export', False):
            runner.export_results()
        else:
            self.stdout.write(self.style.WARNING('Skipping result export'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Benchmarks completed!'))
        self.stdout.write('Check benchmark_results/ directory for charts and exported data.')

