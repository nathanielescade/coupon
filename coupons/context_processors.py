from django.conf import settings

def app_settings(request):
    """
    Makes app settings available in templates
    """
    return {
        'APP_NAME': getattr(settings, 'APP_NAME', 'CoupZilla'),
        'APP_TAGLINE': getattr(settings, 'APP_TAGLINE', 'Save Money with Exclusive Coupons'),
        'APP_ICON': getattr(settings, 'APP_ICON', 'fas fa-ticket-alt'),
        'APP_FAVICON': getattr(settings, 'APP_FAVICON', 'img/coupzilla.ico'),
        'APP_LOGO': getattr(settings, 'APP_LOGO', 'img/coupzilla.jpg'),
        'SOCIAL_LINKS': getattr(settings, 'SOCIAL_LINKS', {}),
        'CONTACT_EMAIL': getattr(settings, 'CONTACT_EMAIL', 'coupzilla.deals@gmail.com'),
        'CONTACT_PHONE': getattr(settings, 'CONTACT_PHONE', '+1 (555) 123-4567'),
    }