import csv
import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.products.models import Product, Category, ProductImage


class Command(BaseCommand):
    help = 'Import products from products.csv file'

    def handle(self, *args, **options):
        csv_file = 'products.csv'  # Your actual CSV file name
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} not found in root directory'))
            return

        self.stdout.write(f'Importing products from {csv_file}...')

        # Create default category
        default_category, created = Category.objects.get_or_create(
            name='General',
            defaults={
                'slug': 'general',
                'description': 'General products',
                'is_active': True
            }
        )

        success_count = 0
        error_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Clean up column names (remove empty ones and strip spaces)
            reader.fieldnames = [name.strip() for name in reader.fieldnames if name and name.strip()]
            
            self.stdout.write(f'CSV columns: {reader.fieldnames}')
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Get data from CSV - handle the specific column names from your file
                    model = str(row.get('Model', '')).strip()
                    name = row.get('product Name', '').strip()
                    category_name = row.get('Category', '').strip()  # Note: 'Category' not 'category'
                    pictures = row.get('Pictures', '').strip()
                    description = row.get('Description', '').strip()
                    online = row.get('ონლაინ', '').strip()

                    if not name:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: No product name, skipping'))
                        continue

                    # Get or create category
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={
                                'slug': slugify(category_name),
                                'description': f'Category for {category_name}',
                                'is_active': True
                            }
                        )
                    else:
                        category = default_category

                    # Generate model number if empty
                    if not model:
                        model = slugify(name)[:50]

                    # Generate unique slug
                    slug = slugify(name)
                    original_slug = slug
                    counter = 1
                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{original_slug}-{counter}"
                        counter += 1

                    # Check if product exists
                    product, created = Product.objects.get_or_create(
                        model_number=model,
                        defaults={
                            'name': name,
                            'slug': slug,
                            'category': category,
                            'description': description or f'Description for {name}',
                            'short_description': description[:200] if description else f'Short description for {name}',
                            'price': 100.00,  # Default price
                            'stock_quantity': 10,  # Default stock
                            'is_in_stock': True,
                            'is_active': online.lower() not in ['no', 'false', '0', 'არა'],
                            'is_featured': False,
                        }
                    )

                    if created:
                        # Handle images
                        if pictures:
                            self.add_images(product, pictures)
                        
                        success_count += 1
                        self.stdout.write(f'✓ Created: {product.name}')
                    else:
                        self.stdout.write(f'- Exists: {product.name}')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Row {row_num} error: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\nImport completed!'))
        self.stdout.write(f'Successfully created: {success_count}')
        self.stdout.write(f'Errors: {error_count}')

    def add_images(self, product, pictures):
        """Add images to product"""
        # Split multiple URLs (comma or semicolon separated)
        image_urls = [url.strip() for url in pictures.replace(';', ',').split(',') if url.strip()]
        
        for index, image_url in enumerate(image_urls):
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                # Get file extension
                if image_url.lower().endswith(('.jpg', '.jpeg')):
                    ext = 'jpg'
                elif image_url.lower().endswith('.png'):
                    ext = 'png'
                else:
                    ext = 'jpg'  # Default
                
                # Create image name
                image_name = f"{product.model_number}_{index + 1}.{ext}"
                
                # Create ProductImage
                product_image = ProductImage(
                    product=product,
                    alt_text=f"{product.name} - Image {index + 1}",
                    is_main=(index == 0),  # First image is main
                    order=index
                )
                
                # Save image
                product_image.image.save(
                    image_name,
                    ContentFile(response.content),
                    save=True
                )
                
            except Exception as e:
                self.stdout.write(f'    Image error: {str(e)}')