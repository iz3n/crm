# Generated manually to enable pg_trgm extension

from django.db import migrations, connection


def enable_pg_trgm_extension(apps, schema_editor):
    """
    Enable pg_trgm extension if it doesn't exist.
    If permission is denied, the extension may need to be created manually
    by a database superuser.
    """
    with connection.cursor() as cursor:
        # Check if extension already exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            try:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
            except Exception as e:
                # If permission denied, provide helpful error message
                if 'permission denied' in str(e).lower() or 'insufficientprivilege' in str(e).lower():
                    raise Exception(
                        "Permission denied to create pg_trgm extension. "
                        "Please run this SQL as a database superuser:\n"
                        "  CREATE EXTENSION IF NOT EXISTS pg_trgm;\n\n"
                        "Or grant the necessary permissions to your database user:\n"
                        "  GRANT CREATE ON DATABASE your_database_name TO your_user;"
                    ) from e
                raise


def disable_pg_trgm_extension(apps, schema_editor):
    """Disable pg_trgm extension."""
    with connection.cursor() as cursor:
        cursor.execute('DROP EXTENSION IF EXISTS pg_trgm;')


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_remove_address_address_city_co_84058d_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(
            enable_pg_trgm_extension,
            reverse_code=disable_pg_trgm_extension,
        ),
    ]

