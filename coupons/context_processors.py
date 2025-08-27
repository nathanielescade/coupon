from django.conf import settings

def app_settings(request):
    """
    Makes app settings available in templates
    """
    return {
        'APP_NAME': getattr(settings, 'APP_NAME', 'CouPradise'),
        'APP_TAGLINE': getattr(settings, 'APP_TAGLINE', 'Discover Amazing Deals, Save Big Every Day'),
        'APP_ICON': getattr(settings, 'APP_ICON', 'fas fa-tags'),
        'APP_FAVICON': getattr(settings, 'APP_FAVICON', 'img/favicon.ico'),
        'APP_LOGO': getattr(settings, 'APP_LOGO', 'img/logo.jpg'),
        'SOCIAL_LINKS': getattr(settings, 'SOCIAL_LINKS', {}),
        'CONTACT_EMAIL': getattr(settings, 'CONTACT_EMAIL', 'coupradise.deals@gmail.com'),
        'CONTACT_PHONE': getattr(settings, 'CONTACT_PHONE', '+1 (555) 123-4567'),
    }