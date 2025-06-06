# apps/notifications/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class EmailTemplate(models.Model):
    """Email templates for different types of notifications"""
    
    TEMPLATE_TYPES = [
        ('welcome', _('Welcome Email')),
        ('order_confirmation', _('Order Confirmation')),
        ('order_shipped', _('Order Shipped')),
        ('order_delivered', _('Order Delivered')),
        ('password_reset', _('Password Reset')),
        ('product_back_in_stock', _('Product Back in Stock')),
        ('abandoned_cart', _('Abandoned Cart')),
        ('newsletter', _('Newsletter')),
        ('sale_announcement', _('Sale Announcement')),
    ]
    
    name = models.CharField(max_length=200, verbose_name=_("Template Name"))
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=300, verbose_name=_("Email Subject"))
    subject_ka = models.CharField(max_length=300, blank=True, verbose_name=_("Email Subject (Georgian)"))
    
    html_content = models.TextField(verbose_name=_("HTML Content"))
    html_content_ka = models.TextField(blank=True, verbose_name=_("HTML Content (Georgian)"))
    
    text_content = models.TextField(verbose_name=_("Text Content"))
    text_content_ka = models.TextField(blank=True, verbose_name=_("Text Content (Georgian)"))
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailSubscription(models.Model):
    """Email subscription management"""
    
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    is_subscribed = models.BooleanField(default=True)
    
    # Subscription preferences
    newsletter = models.BooleanField(default=True, verbose_name=_("Newsletter"))
    promotions = models.BooleanField(default=True, verbose_name=_("Promotions & Sales"))
    product_updates = models.BooleanField(default=True, verbose_name=_("Product Updates"))
    order_updates = models.BooleanField(default=True, verbose_name=_("Order Updates"))
    
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Email Subscription')
        verbose_name_plural = _('Email Subscriptions')
    
    def __str__(self):
        return self.email


class EmailCampaign(models.Model):
    """Email marketing campaigns"""
    
    CAMPAIGN_STATUS = [
        ('draft', _('Draft')),
        ('scheduled', _('Scheduled')),
        ('sending', _('Sending')),
        ('sent', _('Sent')),
        ('cancelled', _('Cancelled')),
    ]
    
    name = models.CharField(max_length=200)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    
    # Targeting
    target_all_subscribers = models.BooleanField(default=False)
    target_customers_only = models.BooleanField(default=False)
    target_inactive_users = models.BooleanField(default=False)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    emails_sent = models.PositiveIntegerField(default=0)
    emails_delivered = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Campaign')
        verbose_name_plural = _('Email Campaigns')
    
    def __str__(self):
        return self.name
    
    @property
    def open_rate(self):
        if self.emails_delivered > 0:
            return (self.emails_opened / self.emails_delivered) * 100
        return 0
    
    @property
    def click_rate(self):
        if self.emails_delivered > 0:
            return (self.emails_clicked / self.emails_delivered) * 100
        return 0


# apps/notifications/services.py
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import EmailTemplate, EmailSubscription, EmailCampaign
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_template_email(template_type, recipient_email, context_data, language='en'):
        """Send email using template"""
        try:
            # Get template
            template = EmailTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
            
            # Select content based on language
            if language == 'ka' and template.subject_ka:
                subject = template.subject_ka
                html_content = template.html_content_ka
                text_content = template.text_content_ka
            else:
                subject = template.subject
                html_content = template.html_content
                text_content = template.text_content
            
            # Render templates with context
            subject_template = Template(subject)
            html_template = Template(html_content)
            text_template = Template(text_content)
            
            context = Context(context_data)
            
            rendered_subject = subject_template.render(context)
            rendered_html = html_template.render(context)
            rendered_text = text_template.render(context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(rendered_html, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {recipient_email} using template {template_type}")
            return True
            
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template {template_type} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email"""
        context = {
            'order': order,
            'customer_name': order.full_billing_name,
            'order_items': order.items.all(),
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        
        return EmailService.send_template_email(
            template_type='order_confirmation',
            recipient_email=order.email,
            context_data=context,
            language='ka'  # Default to Georgian
        )
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new users"""
        context = {
            'user': user,
            'customer_name': user.get_full_name() or user.username,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        
        return EmailService.send_template_email(
            template_type='welcome',
            recipient_email=user.email,
            context_data=context
        )
    
    @staticmethod
    def send_abandoned_cart_email(user, cart_items):
        """Send abandoned cart reminder"""
        context = {
            'user': user,
            'customer_name': user.get_full_name() or user.username,
            'cart_items': cart_items,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'cart_url': f"{settings.SITE_URL}/cart/",
        }
        
        return EmailService.send_template_email(
            template_type='abandoned_cart',
            recipient_email=user.email,
            context_data=context
        )


class CampaignService:
    """Service for managing email campaigns"""
    
    @staticmethod
    def send_campaign(campaign_id):
        """Send email campaign"""
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            
            if campaign.status != 'scheduled':
                logger.error(f"Campaign {campaign_id} is not scheduled for sending")
                return False
            
            # Update status
            campaign.status = 'sending'
            campaign.sent_at = timezone.now()
            campaign.save()
            
            # Get recipients
            recipients = CampaignService._get_campaign_recipients(campaign)
            
            sent_count = 0
            for email in recipients:
                success = EmailService.send_template_email(
                    template_type=campaign.template.template_type,
                    recipient_email=email,
                    context_data={
                        'site_name': settings.SITE_NAME,
                        'site_url': settings.SITE_URL,
                        'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/{email}/",
                    }
                )
                
                if success:
                    sent_count += 1
            
            # Update campaign stats
            campaign.emails_sent = sent_count
            campaign.status = 'sent'
            campaign.save()
            
            logger.info(f"Campaign {campaign_id} sent to {sent_count} recipients")
            return True
            
        except EmailCampaign.DoesNotExist:
            logger.error(f"Campaign {campaign_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to send campaign {campaign_id}: {str(e)}")
            return False
    
    @staticmethod
    def _get_campaign_recipients(campaign):
        """Get list of email recipients for campaign"""
        emails = []
        
        if campaign.target_all_subscribers:
            emails.extend(
                EmailSubscription.objects.filter(
                    is_subscribed=True,
                    newsletter=True
                ).values_list('email', flat=True)
            )
        
        if campaign.target_customers_only:
            emails.extend(
                User.objects.filter(
                    is_active=True,
                    orders__isnull=False
                ).distinct().values_list('email', flat=True)
            )
        
        if campaign.target_inactive_users:
            inactive_date = timezone.now() - timezone.timedelta(days=90)
            emails.extend(
                User.objects.filter(
                    is_active=True,
                    last_login__lt=inactive_date
                ).values_list('email', flat=True)
            )
        
        return list(set(emails))  # Remove duplicates


# apps/notifications/tasks.py (for Celery background tasks)
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from apps.cart.models import Cart
from .services import EmailService, CampaignService

@shared_task
def send_abandoned_cart_emails():
    """Send abandoned cart emails to users who haven't completed their purchase"""
    
    # Find carts that were updated 24 hours ago but no recent orders
    cutoff_time = timezone.now() - timezone.timedelta(hours=24)
    
    abandoned_carts = Cart.objects.filter(
        user__isnull=False,
        updated_at__lt=cutoff_time,
        items__isnull=False
    ).select_related('user').prefetch_related('items__product').distinct()
    
    for cart in abandoned_carts:
        # Check if user has placed an order since cart was updated
        recent_orders = cart.user.orders.filter(
            created_at__gt=cart.updated_at
        ).exists()
        
        if not recent_orders:
            EmailService.send_abandoned_cart_email(
                user=cart.user,
                cart_items=cart.items.all()
            )

@shared_task
def send_scheduled_campaigns():
    """Send scheduled email campaigns"""
    
    scheduled_campaigns = EmailCampaign.objects.filter(
        status='scheduled',
        scheduled_at__lte=timezone.now()
    )
    
    for campaign in scheduled_campaigns:
        CampaignService.send_campaign(campaign.id)