# Django management command to fix empty category slugs
# Save this as: apps/products/management/commands/fix_category_slugs.py

import os
import sys
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category


class Command(BaseCommand):
    help = 'Fix empty category slugs'

    def handle(self, *args, **options):
        self.stdout.write('Checking and fixing category slugs...')
        
        # Find categories with empty or None slugs
        problematic_categories = Category.objects.filter(
            models.Q(slug='') | models.Q(slug__isnull=True)
        )
        
        if not problematic_categories.exists():
            # Check all categories for debugging
            all_categories = Category.objects.all()
            self.stdout.write(f'Found {all_categories.count()} categories:')
            
            for category in all_categories:
                slug_status = f"'{category.slug}'" if category.slug else "EMPTY/NULL"
                self.stdout.write(f"  - {category.name}: slug = {slug_status}")
            
            self.stdout.write(self.style.SUCCESS('No problematic category slugs found.'))
            return
        
        self.stdout.write(f'Found {problematic_categories.count()} categories with empty slugs:')
        
        for category in problematic_categories:
            old_slug = category.slug
            
            # Generate new slug from name
            new_slug = slugify(category.name)
            
            # If slugify returns empty (e.g., for non-Latin characters), create a fallback
            if not new_slug:
                new_slug = f'category-{category.id}'
            
            # Ensure uniqueness
            original_slug = new_slug
            counter = 1
            while Category.objects.filter(slug=new_slug).exclude(id=category.id).exists():
                new_slug = f'{original_slug}-{counter}'
                counter += 1
            
            # Update the category
            category.slug = new_slug
            category.save()
            
            self.stdout.write(
                f"  ✓ Fixed: '{category.name}' - slug: '{old_slug}' → '{new_slug}'"
            )
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {problematic_categories.count()} category slugs.'))