// analytics.js

// Track events on the page
document.addEventListener('DOMContentLoaded', function() {
    // Track coupon saves
    const saveButtons = document.querySelectorAll('a[href*="/save/"]');
    saveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const couponId = href.split('/').pop();
            
            trackEvent('save_coupon', window.location.pathname, 'save_button', {
                coupon_id: couponId
            });
        });
    });
    
    // Track coupon code copies
    const copyButtons = document.querySelectorAll('button[onclick*="copyCode"]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Get coupon ID from the onclick attribute
            const onclickAttr = this.getAttribute('onclick');
            const match = onclickAttr.match(/copyCode\('([^']+)'/);
            const couponId = match ? match[1] : null;
            
            if (couponId) {
                trackEvent('copy_code', window.location.pathname, 'copy_button', {
                    coupon_id: couponId
                });
            }
        });
    });
    
    // Track coupon uses
    const useButtons = document.querySelectorAll('a[href*="/use/"]');
    useButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const couponId = href.split('/').pop();
            
            trackEvent('use_coupon', window.location.pathname, 'use_button', {
                coupon_id: couponId
            });
        });
    });
    
    // Track filter clicks
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sortType = this.getAttribute('data-sort');
            const section = this.closest('.filter-controls').getAttribute('data-section');
            
            trackEvent('filter', window.location.pathname, 'filter_button', {
                section: section,
                sort_type: sortType
            });
        });
    });
    
    // Track search submissions
    const searchForms = document.querySelectorAll('form[action*="/search/"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function() {
            const searchInput = this.querySelector('input[name="q"]');
            const query = searchInput ? searchInput.value : '';
            
            trackEvent('search', window.location.pathname, 'search_form', {
                query: query
            });
        });
    });
    
    // Track scroll events (throttled)
    let scrollTracked = false;
    window.addEventListener('scroll', function() {
        if (!scrollTracked) {
            scrollTracked = true;
            
            setTimeout(function() {
                const scrollPercentage = Math.round(
                    (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
                );
                
                trackEvent('scroll', window.location.pathname, 'page_scroll', {
                    scroll_percentage: scrollPercentage
                });
                
                scrollTracked = false;
            }, 5000); // Only track scroll every 5 seconds
        }
    });
});

// Function to track events
function trackEvent(eventType, page, element, data = {}) {
    fetch('/analytics/track-event/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            event_type: eventType,
            page: page,
            element: element,
            data: data
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') {
            console.error('Failed to track event:', data);
        }
    })
    .catch(error => {
        console.error('Error tracking event:', error);
    });
}

// Function to get CSRF token
function getCsrfToken() {
    // Try to get from meta tag first
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    // Fallback to cookies
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return '';
}