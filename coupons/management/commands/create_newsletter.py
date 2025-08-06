from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from coupons.models import Coupon, NewsletterSubscriber
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Create and send newsletter to all active subscribers'
    
    def add_arguments(self, parser):
        parser.add_argument('--subject', type=str, help='Subject of the newsletter')
        parser.add_argument('--preview', action='store_true', help='Preview newsletter without sending')
        parser.add_argument('--featured-only', action='store_true', help='Include only featured coupons')
    
    def handle(self, *args, **options):
        # Get latest coupons for the newsletter
        days_ago = 7  # Get coupons from the last 7 days
        start_date = timezone.now() - datetime.timedelta(days=days_ago)
        
        if options['featured_only']:
            coupons = Coupon.objects.filter(
                is_active=True,
                is_featured=True,
                created_at__gte=start_date
            ).order_by('-created_at')[:10]
        else:
            coupons = Coupon.objects.filter(
                is_active=True,
                created_at__gte=start_date
            ).order_by('-created_at')[:10]
        
        if not coupons:
            self.stdout.write(self.style.WARNING('No new coupons to include in the newsletter'))
            return
        
        # Create newsletter subject
        default_subject = f"CouponHub Weekly: {len(coupons)} New Deals This Week"
        subject = options.get('subject', default_subject)
        
        # Get subscribers
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        
        if not subscribers.exists():
            self.stdout.write(self.style.WARNING('No active subscribers found'))
            return
        
        self.stdout.write(f"Creating newsletter with subject: '{subject}'")
        self.stdout.write(f"Including {len(coupons)} coupons")
        self.stdout.write(f"Ready to send to {len(subscribers)} subscribers")
        
        if options['preview']:
            # Just show a preview without sending
            self.stdout.write("\n=== NEWSLETTER PREVIEW ===")
            
            # Render a sample email
            sample_email = subscribers.first()
            html_content = render_to_string('newsletter_email.html', {
                'subject': subject,
                'coupons': coupons,
                'email': sample_email.email
            })
            
            # Save preview to a file
            with open('newsletter_preview.html', 'w') as f:
                f.write(html_content)
            
            self.stdout.write(self.style.SUCCESS('Newsletter preview saved to newsletter_preview.html'))
            return
        
        # Ask for confirmation before sending
        confirm = input(f"\nSend newsletter to {len(subscribers)} subscribers? (y/n): ")
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('Newsletter sending cancelled'))
            return
        
        # Send emails
        from_email = settings.DEFAULT_FROM_EMAIL
        success_count = 0
        error_count = 0
        
        for subscriber in subscribers:
            try:
                # Render HTML email
                html_content = render_to_string('newsletter_email.html', {
                    'subject': subject,
                    'coupons': coupons,
                    'email': subscriber.email
                })
                
                # Create email message
                email = EmailMultiAlternatives(
                    subject,
                    f"Check out the latest deals and coupons on CouponHub!\n\nThis week we have {len(coupons)} new deals for you.",
                    from_email,
                    [subscriber.email]
                )
                
                # Attach HTML version
                email.attach_alternative(html_content, "text/html")
                
                # Send email
                email.send()
                success_count += 1
                
                # Show progress
                if success_count % 10 == 0:
                    self.stdout.write(f"Sent to {success_count} subscribers...")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send to {subscriber.email}: {str(e)}'))
                error_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully sent newsletter to {success_count} subscribers'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to send to {error_count} subscribers'))