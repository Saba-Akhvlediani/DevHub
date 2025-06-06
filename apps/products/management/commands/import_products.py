# apps/products/management/commands/import_products.py
import csv
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from apps.products.models import Product, Category

class Command(BaseCommand):
    help = 'Import products from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The CSV file to import')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do a dry run without saving to database',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write('Running in dry-run mode - no changes will be saved')

        try:
            with open(csv_file_path, 'r') as file:
                # Read the first line to get headers
                headers = next(csv.reader(file))
                # Strip whitespace from headers
                headers = [h.strip() for h in headers]
                # Go back to start of file
                file.seek(0)
                
                # Create a CSV reader with cleaned headers
                reader = csv.DictReader(file, fieldnames=headers)
                # Skip the header row since we already processed it
                next(reader)
                
                # Display the available columns
                self.stdout.write('\nAvailable columns in CSV:')
                for col in headers:
                    self.stdout.write(f'- "{col}"')

                success_count = 0
                error_count = 0

                # Process each row
                for row_number, row in enumerate(reader, start=1):
                    try:
                        # Get or create category
                        category_name = row.get('category', 'Default Category')
                        category, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={
                                'slug': slugify(category_name),
                                'description': f'Category for {category_name}'
                            }
                        )

                        # Debug print for row data
                        if dry_run:
                            self.stdout.write("Row data:")
                            for key, value in row.items():
                                self.stdout.write(f"  {key}: {value}")

                        # Prepare product data
                        product_data = {
                            'model_number': row.get('Model', '').strip(),
                            'name': row.get('product Nam', '').strip(),
                            'price': float(row.get('საცალო', 0)),
                            'category': category,
                            'description': row.get('Description', ''),
                            'short_description': row.get('short_description', ''),
                            'power': row.get('power', ''),
                            'voltage': row.get('voltage', ''),
                            'frequency': row.get('frequency', ''),
                            'weight': row.get('weight', ''),
                            'material': row.get('material', ''),
                            'stock_quantity': int(row.get('stock_quantity', 0)),
                            'is_active': True,
                            'slug': slugify(f"{row.get('product Nam', '')}-{row.get('Model', '')}")
                        }

                        # Validate required fields
                        if not product_data['model_number']:
                            raise ValueError(f"Missing Model number (column 'Model')")
                        if not product_data['name']:
                            raise ValueError(f"Missing product Name (column 'product Nam')")
                        if not product_data['price']:
                            raise ValueError(f"Missing price (column 'საცალო')")

                        if dry_run:
                            self.stdout.write(f"Would create product: {product_data['name']} ({product_data['model_number']}) - {product_data['price']}₾")
                        else:
                            product = Product.objects.create(**product_data)
                            self.stdout.write(self.style.SUCCESS(
                                f"Created product: {product.name} ({product.model_number}) - {product.price}₾"
                            ))
                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        self.stderr.write(self.style.ERROR(
                            f"Error in row {row_number}: {str(e)}"
                        ))

                # Print summary
                self.stdout.write('\nImport Summary:')
                self.stdout.write(f"Successful: {success_count}")
                self.stdout.write(f"Errors: {error_count}")

        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_file_path}")
        except Exception as e:
            raise CommandError(f"Error reading file: {str(e)}")