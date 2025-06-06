import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Clear existing products and reimport from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='products.csv',
            help='Path to the CSV file (default: products.csv)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of existing products'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        confirm = options['confirm']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file "{csv_file}" not found!')
            )
            return

        if not confirm:
            self.stdout.write(
                self.style.WARNING('This will DELETE ALL existing products and categories!')
            )
            self.stdout.write(
                self.style.WARNING('Run with --confirm flag if you are sure.')
            )
            return

        try:
            with transaction.atomic():
                self.clear_existing_data()
                self.import_products(csv_file)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during import: {str(e)}')
            )

    def clear_existing_data(self):
        """Clear existing products and categories"""
        self.stdout.write('Clearing existing data...')
        
        products_count = Product.objects.count()
        categories_count = Category.objects.count()
        
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        self.stdout.write(f'Deleted {products_count} products and {categories_count} categories')

    def import_products(self, csv_file):
        """Import products from CSV file"""
        
        products_created = 0
        categories_created = 0
        errors = []
        category_cache = {}

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
                    
                    # Create or get category (use cache for performance)
                    category = None
                    if category_name:
                        if category_name in category_cache:
                            category = category_cache[category_name]
                        else:
                            # Generate category slug
                            category_slug = slugify(category_name)
                            if not category_slug:
                                # Fallback for Georgian text - create a simple slug
                                category_slug = f"category-{len(category_name)}-{abs(hash(category_name)) % 1000}"
                            
                            # Ensure category slug uniqueness
                            original_slug = category_slug
                            counter = 1
                            while Category.objects.filter(slug=category_slug).exists():
                                category_slug = f'{original_slug}-{counter}'
                                counter += 1
                            
                            category = Category.objects.create(
                                name=category_name,
                                slug=category_slug,
                                description=f'Category for {category_name}',
                                is_active=True
                            )
                            category_cache[category_name] = category
                            categories_created += 1
                            self.stdout.write(f'Created category: {category_name} (slug: {category_slug})')
                    
                    # Process description to extract technical specs
                    specs = self.parse_description(description)
                    
                    # Create product slug - handle Georgian text better
                    product_slug = slugify(f"{model_number}-{product_name}")
                    
                    # If slugify fails (Georgian text), create a fallback slug
                    if not product_slug or product_slug == '-':
                        product_slug = f"product-{model_number}"
                    
                    # Ensure product slug uniqueness
                    original_slug = product_slug
                    counter = 1
                    while Product.objects.filter(slug=product_slug).exists():
                        product_slug = f'{original_slug}-{counter}'
                        counter += 1
                    
                    # Create product
                    product = Product.objects.create(
                        model_number=model_number,
                        name=product_name,
                        slug=product_slug,
                        category=category,
                        description=description,
                        short_description=f"{product_name} - {model_number}",
                        price=price,
                        power=specs.get('power', ''),
                        voltage=specs.get('voltage', ''),
                        frequency=specs.get('frequency', ''),
                        temperature_settings=specs.get('temperature', ''),
                        air_flow_settings=specs.get('air_flow', ''),
                        cable_length=specs.get('cable_length', ''),
                        weight=specs.get('weight', ''),
                        stock_quantity=10,  # Default stock
                        is_in_stock=True,
                        is_active=True,
                        is_featured=False,
                    )
                    
                    products_created += 1
                    self.stdout.write(f'Created product: {model_number} - {product_name} (slug: {product_slug})')
                    
                except Exception as e:
                    error_msg = f'Error processing row {row_num}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('IMPORT SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Categories created: {categories_created}')
        self.stdout.write(f'Products created: {products_created}')
        
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