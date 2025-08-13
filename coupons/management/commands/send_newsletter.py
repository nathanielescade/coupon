from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from coupons.models import NewsletterSubscriber

class Command(BaseCommand):
    help = 'Send newsletter to all active subscribers'
    
    def add_arguments(self, parser):
        parser.add_argument('--subject', type=str, help='Subject of the newsletter')
        parser.add_argument('--message', type=str, help='Message content of the newsletter')
    
    def handle(self, *args, **options):
        subject = options.get('subject', 'Latest Deals and Coupons from CouponHub')
        message = options.get('message', 'Check out our latest deals and coupons on our website!')
        
        if not subject or not message:
            self.stdout.write(self.style.ERROR('Both subject and message are required'))
            return
        
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        
        if not subscribers.exists():
            self.stdout.write(self.style.WARNING('No active subscribers found'))
            return
        
        from_email = settings.DEFAULT_FROM_EMAIL
        success_count = 0
        error_count = 0
        
        for subscriber in subscribers:
            try:
                # Render HTML email
                html_content = render_to_string('newsletter_email.html', {
                    'subject': subject,
                    'message': message,
                    'email': subscriber.email
                })
                
                # Create email message
                email = EmailMultiAlternatives(
                    subject,
                    message,  # Plain text version
                    from_email,
                    [subscriber.email]
                )
                
                # Attach HTML version
                email.attach_alternative(html_content, "text/html")
                
                # Send email
                email.send()
                success_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send to {subscriber.email}: {str(e)}'))
                error_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully sent newsletter to {success_count} subscribers'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to send to {error_count} subscribers'))