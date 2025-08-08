# CouponHub

A comprehensive coupon and deals platform built with Django and Django REST Framework that helps users discover, save, and use coupons from their favorite stores.

## Features

### User Features
- **Browse Coupons**: Explore a wide variety of coupons from different stores and categories
- **Search Functionality**: Find specific coupons by searching through titles, descriptions, codes, store names, and categories
- **Save Coupons**: Save coupons for later use with a personal account
- **Copy Coupon Codes**: One-click copying of coupon codes with visual feedback
- **Filter & Sort**: Filter coupons by store, category, or sort by popularity, expiry date, or discount value
- **Store & Category Pages**: Browse all coupons from specific stores or categories
- **Responsive Design**: Fully responsive design that works on all devices

### Admin Features
- **Analytics Dashboard**: Comprehensive analytics for user behavior, coupon performance, and more
- **Coupon Management**: Create, edit, and delete coupons with full CRUD operations
- **User Management**: Monitor and manage user accounts and activities
- **Coupon Providers**: Integrate with external coupon APIs through the provider system

### Technical Features
- **REST API**: Full REST API for mobile app integration
- **Real-time Analytics**: Track user interactions and coupon usage in real-time
- **Event Tracking**: Comprehensive event tracking for user actions
- **Search Optimization**: Efficient search functionality across multiple fields
- **Security**: CSRF protection, secure authentication, and input validation

## Technology Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Database**: SQLite (development), can be configured for PostgreSQL/MySQL in production
- **Authentication**: Django's built-in authentication system
- **Analytics**: Custom analytics system with event tracking
- **Deployment**: Can be deployed with ngrok for development/testing

## Installation

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nathanielescade/coupon.git
   cd couponhub
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Update the necessary environment variables:
     ```
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

5. **Apply database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Frontend: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Project Structure

```
couponhub/
├── coupon_project/          # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── coupons/               # Coupons app
│   ├── models.py          # Coupon, Store, Category models
│   ├── views.py           # Main views and viewsets
│   ├── serializers.py     # API serializers
│   └── urls.py            # App URLs
├── analytics/             # Analytics app
│   ├── models.py          # Analytics models
│   ├── views.py           # Analytics views
│   └── middleware.py      # Analytics middleware
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── home.html          # Homepage
│   ├── coupon_detail.html # Coupon detail page
│   └── search.html        # Search results page
├── static/                # Static files
│   ├── css/               # CSS files
│   ├── js/                # JavaScript files
│   └── images/            # Image files
└── media/                 # User-uploaded media
```

## API Endpoints

### Authentication
- `POST /api/login/` - User login
- `POST /api/logout/` - User logout

### Coupons
- `GET /api/coupons/` - List all coupons
- `GET /api/coupons/{id}/` - Get coupon details
- `POST /api/coupons/` - Create a new coupon (admin only)
- `PUT /api/coupons/{id}/` - Update a coupon (admin only)
- `DELETE /api/coupons/{id}/` - Delete a coupon (admin only)
- `POST /api/coupons/{id}/save_coupon/` - Save a coupon to user account
- `POST /api/coupons/{id}/use_coupon/` - Mark a coupon as used

### Stores & Categories
- `GET /api/stores/` - List all stores
- `GET /api/categories/` - List all categories

### User Actions
- `GET /api/my_coupons/` - Get user's saved coupons
- `GET /api/coupons/featured/` - Get featured coupons
- `GET /api/coupons/expiring_soon/` - Get coupons expiring soon

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL | SQLite |
| `STATIC_ROOT` | Static files root | `/staticfiles/` |
| `MEDIA_ROOT` | Media files root | `/media/` |

### Ngrok Configuration

For development and testing with external services:

1. **Add ngrok URL to settings**:
   ```python
   ALLOWED_HOSTS = ["localhost", "127.0.0.1", "your-ngrok-url.ngrok-free.app"]
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:8000",
       "http://127.0.0.1:8000",
       "https://your-ngrok-url.ngrok-free.app",
   ]
   CSRF_TRUSTED_ORIGINS = [
       "https://your-ngrok-url.ngrok-free.app",
   ]
   ```

2. **Start ngrok**:
   ```bash
   ngrok http 8000
   ```

## Usage

### For Users

1. **Browse Coupons**: Visit the homepage to see featured and latest coupons
2. **Search**: Use the search bar to find specific coupons
3. **Filter**: Use the filter options to narrow down results
4. **Save Coupons**: Click the heart icon to save coupons for later
5. **Copy Codes**: Click the "Copy" button to copy coupon codes
6. **Use Coupons**: Click "Use Deal" to visit the store's website

### For Administrators

1. **Access Admin Panel**: Visit `/admin` and log in with your superuser account
2. **Manage Coupons**: Create, edit, or delete coupons as needed
3. **View Analytics**: Visit `/analytics/dashboard` to see usage statistics
4. **Manage Stores & Categories**: Add or update stores and categories

## Development

### Adding New Features

1. **Models**: Define new models in the appropriate app's `models.py`
2. **Migrations**: Create and apply migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. **Views**: Add views in `views.py` or create viewsets for API endpoints
4. **URLs**: Update `urls.py` to include new endpoints
5. **Templates**: Create or update HTML templates as needed
6. **Static Files**: Add CSS, JavaScript, or images to the static folder

### Testing

Run tests:
```bash
python manage.py test
```

## Deployment

### Production Settings

1. **Update settings**:
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   ```

2. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Set up a production database** (PostgreSQL recommended)

4. **Configure environment variables** in your hosting environment

### Deployment Options

- **Heroku**: Easy deployment with the Heroku platform
- **AWS**: Use EC2, RDS, and S3 for a scalable solution
- **DigitalOcean**: Use Django Droplet for straightforward deployment
- **Docker**: Containerize the application for consistent deployment

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.

## Roadmap

- [ ] Mobile app development
- [ ] Email notifications for expiring coupons
- [ ] Social sharing features
- [ ] User profiles and preferences
- [ ] Advanced filtering options
- [ ] Coupon rating and review system
- [ ] Browser extension for automatic coupon detection
