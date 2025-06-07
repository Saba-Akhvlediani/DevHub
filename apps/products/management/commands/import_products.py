# Django management command to import products from CSV
# Save this as: apps/products/management/commands/import_products_csv.py

import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='products.csv',
            help='Path to the CSV file (default: products.csv)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual database changes)'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file "{csv_file}" not found!')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made to the database')
            )

        try:
            with transaction.atomic():
                self.import_products(csv_file, dry_run)
                
                if dry_run:
                    # Rollback transaction in dry-run mode
                    transaction.set_rollback(True)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing products: {str(e)}')
            )

    def import_products(self, csv_file, dry_run):
        """Import products from CSV file"""
        
        products_created = 0
        products_updated = 0
        categories_created = 0
        errors = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Read CSV with proper handling of the BOM and spaces
            reader = csv.DictReader(file)
            
            # Clean up the fieldnames (remove BOM and extra spaces)
            reader.fieldnames = [field.strip().replace('\ufeff', '') for field in reader.fieldnames]
            
            self.stdout.write(f'CSV columns found: {reader.fieldnames}')
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Clean up the row data
                    clean_row = {key.strip(): value.strip() if value else '' for key, value in row.items()}
                    
                    # Extract data from CSV
                    model_number = clean_row.get('Model', '').strip()
                    product_name = clean_row.get('Product Name', '').strip()
                    category_name = clean_row.get('Category', '').strip()
                    description = clean_row.get('Description', '').strip()
                    price_str = clean_row.get('ონლაინ', '').strip()
                    
                    # Skip empty rows
                    if not model_number or not product_name:
                        self.stdout.write(f'Skipping row {row_num}: Missing model number or product name')
                        continue
                    
                    # Parse price
                    try:
                        price = float(price_str) if price_str else 0.0
                    except ValueError:
                        self.stdout.write(f'Warning: Invalid price "{price_str}" for {model_number}, setting to 0')
                        price = 0.0
                    
                    # Create or get category
                    category = None
                    if category_name:
                        # Generate category slug
                        category_slug = slugify(category_name)
                        if not category_slug:
                            # Fallback for Georgian text
                            category_slug = f"category-{len(category_name)}-{abs(hash(category_name)) % 1000}"
                        
                        if not dry_run:
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={
                                    'slug': category_slug,
                                    'description': f'Category for {category_name}',
                                    'is_active': True
                                }
                            )
                            if created:
                                categories_created += 1
                                self.stdout.write(f'Created category: {category_name} (slug: {category_slug})')
                        else:
                            # In dry-run mode, check if category exists
                            try:
                                category = Category.objects.get(name=category_name)
                            except Category.DoesNotExist:
                                self.stdout.write(f'[DRY-RUN] Would create category: {category_name} (slug: {category_slug})')
                                categories_created += 1
                                # Create a mock category for dry-run
                                category = Category(name=category_name, slug=category_slug)
                    
                    # Process description to extract technical specs
                    specs = self.parse_description(description)
                    
                    # Create product slug - handle Georgian text better
                    product_slug = slugify(f"{model_number}-{product_name}")
                    
                    # If slugify fails (Georgian text), create a fallback slug
                    if not product_slug or product_slug == '-':
                        product_slug = f"product-{model_number}"
                    
                    # Ensure slug uniqueness
                    original_slug = product_slug
                    counter = 1
                    while not dry_run and Product.objects.filter(slug=product_slug).exclude(model_number=model_number).exists():
                        product_slug = f'{original_slug}-{counter}'
                        counter += 1
                    
                    # Create or update product
                    if not dry_run:
                        product, created = Product.objects.update_or_create(
                            model_number=model_number,
                            defaults={
                                'name': product_name,
                                'slug': product_slug,
                                'category': category,
                                'description': description,
                                'short_description': f"{product_name} - {model_number}",
                                'price': price,
                                'power': specs.get('power', ''),
                                'voltage': specs.get('voltage', ''),
                                'frequency': specs.get('frequency', ''),
                                'temperature_settings': specs.get('temperature', ''),
                                'air_flow_settings': specs.get('air_flow', ''),
                                'cable_length': specs.get('cable_length', ''),
                                'weight': specs.get('weight', ''),
                                'stock_quantity': 10,  # Default stock
                                'is_in_stock': True,
                                'is_active': True,
                                'is_featured': False,
                            }
                        )
                        
                        if created:
                            products_created += 1
                            self.stdout.write(f'Created product: {model_number} - {product_name} (slug: {product_slug})')
                        else:
                            self.stdout.write(f'Updated product: {model_number} - {product_name} (slug: {product_slug})')
                            products_updated += 1
                    else:
                        # Dry-run mode
                        try:
                            existing_product = Product.objects.get(model_number=model_number)
                            self.stdout.write(f'[DRY-RUN] Would update: {model_number} - {product_name} (slug: {product_slug})')
                            products_updated += 1
                        except Product.DoesNotExist:
                            self.stdout.write(f'[DRY-RUN] Would create: {model_number} - {product_name} (slug: {product_slug})')
                            products_created += 1
                        
                except Exception as e:
                    error_msg = f'Error processing row {row_num}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('IMPORT SUMMARY')
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN MODE - No actual changes made]'))
        
        self.stdout.write(f'Categories created: {categories_created}')
        self.stdout.write(f'Products created: {products_created}')
        self.stdout.write(f'Products updated: {products_updated}')
        
        if errors:
            self.stdout.write(f'\nErrors encountered: {len(errors)}')
            for error in errors:
                self.stdout.write(self.style.ERROR(error))
        else:
            self.stdout.write(self.style.SUCCESS('\nNo errors encountered!'))

    def parse_description(self, description):
        """Parse technical specifications from description text"""
        specs = {}
        
        if not description:
            return specs
        
        lines = description.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse power
            if 'power' in line.lower() and 'w' in line.lower():
                specs['power'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse voltage
            elif 'voltage' in line.lower() and 'v' in line.lower():
                specs['voltage'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse frequency
            elif 'frequency' in line.lower() and 'hz' in line.lower():
                specs['frequency'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse temperature
            elif 'temp' in line.lower() or '°c' in line.lower() or 'temperature' in line.lower():
                specs['temperature'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse air flow
            elif 'air' in line.lower() and ('flow' in line.lower() or 'volume' in line.lower() or 'l/min' in line.lower()):
                specs['air_flow'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse cable length
            elif 'cable' in line.lower() and ('length' in line.lower() or 'm' in line.lower()):
                specs['cable_length'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Parse weight
            elif 'weight' in line.lower() and 'kg' in line.lower():
                specs['weight'] = line.split(':')[-1].strip() if ':' in line else line
        
        return specs