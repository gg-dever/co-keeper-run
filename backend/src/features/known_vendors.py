"""
Universal Known Vendors Database for CoKeeper
==============================================

A static lookup of well-known vendors and their general category hints.
This is different from the ClientOverlay (which learns per-client).
This is universal vendor knowledge that benefits EVERY client.

This database sits between fuzzy matching and type inference:
  Level 1: Exact client-specific match
  Level 2: Fuzzy client-specific match
  Level 2.5: Known universal vendor database ← THIS FILE
  Level 3: Type inference from patterns
  Level 4: ML baseline

Usage:
    from src.features.known_vendors import lookup_known_vendor

    category_hint = lookup_known_vendor("zapier")
    # Returns: "software"
"""

# Map vendor names (lowercase) to category hints
KNOWN_VENDORS = {
    # ============================================================================
    # SOFTWARE & SAAS (the category that's failing worst)
    # ============================================================================
    'zapier': 'software',
    'notion': 'software',
    'slack': 'software',
    'figma': 'software',
    'canva': 'software',
    'miro': 'software',
    'airtable': 'software',
    'monday': 'software',
    'asana': 'software',
    'trello': 'software',
    'jira': 'software',
    'github': 'software',
    'gitlab': 'software',
    'bitbucket': 'software',
    'aws': 'software',
    'amazon web services': 'software',
    'azure': 'software',
    'google cloud': 'software',
    'heroku': 'software',
    'vercel': 'software',
    'netlify': 'software',
    'cloudflare': 'software',
    'digitalocean': 'software',
    'linode': 'software',

    # Payment processing
    'stripe': 'software',
    'square': 'software',
    'paypal': 'software',
    'braintree': 'software',

    # Communication
    'twilio': 'software',
    'sendgrid': 'software',
    'mailchimp': 'software',
    'mailgun': 'software',
    'postmark': 'software',
    'postmarkapp': 'software',

    # CRM & Sales
    'hubspot': 'software',
    'salesforce': 'software',
    'pipedrive': 'software',
    'zoho': 'software',

    # Video & Communication
    'zoom': 'software',
    'loom': 'software',
    'calendly': 'software',
    'microsoft teams': 'software',
    'google meet': 'software',

    # Storage
    'dropbox': 'software',
    'box': 'software',
    'google drive': 'software',
    'onedrive': 'software',

    # Website builders
    'squarespace': 'software',
    'wix': 'software',
    'shopify': 'software',
    'webflow': 'software',
    'wordpress': 'software',

    # Accounting
    'quickbooks': 'software',
    'quickbooks online': 'software',
    'xero': 'software',
    'freshbooks': 'software',
    'wave': 'software',

    # Customer support
    'intercom': 'software',
    'zendesk': 'software',
    'freshdesk': 'software',
    'helpscout': 'software',

    # Project management
    'basecamp': 'software',
    'clickup': 'software',
    'smartsheet': 'software',

    # Design & Creative
    'adobe': 'software',
    'adobe creative cloud': 'software',
    'sketch': 'software',
    'invision': 'software',

    # Media & Content
    'spotify': 'software',
    'apple music': 'software',
    'youtube premium': 'software',
    'vimeo': 'software',

    # Domain & Hosting
    'google domains': 'software',
    'namecheap': 'software',
    'godaddy': 'software',
    'hover': 'software',
    'bluehost': 'software',
    'hostgator': 'software',

    # Analytics
    'google analytics': 'software',
    'mixpanel': 'software',
    'amplitude': 'software',
    'segment': 'software',

    # Developer tools
    'sentry': 'software',
    'datadog': 'software',
    'new relic': 'software',
    'bugsnag': 'software',

    # Productivity
    'evernote': 'software',
    'onenote': 'software',
    'google workspace': 'software',
    'microsoft 365': 'software',
    'office 365': 'software',

    # Collaboration
    'mural': 'software',
    'lucidchart': 'software',
    'draw.io': 'software',

    # Miscellaneous software
    'docusign': 'software',
    'hellosign': 'software',
    'pandadoc': 'software',
    'typeform': 'software',
    'surveymonkey': 'software',
    'missive': 'software',
    'syncwith': 'software',
    'adformatic': 'software',
    'veem': 'software',
    'booking agent info': 'software',

    # ============================================================================
    # PAYROLL SERVICES
    # ============================================================================
    'gusto': 'payroll',
    'adp': 'payroll',
    'paychex': 'payroll',
    'justworks': 'payroll',
    'rippling': 'payroll',
    'bamboohr': 'payroll',
    'zenefits': 'payroll',
    'namely': 'payroll',

    # ============================================================================
    # FREELANCE & CONTRACT PLATFORMS
    # ============================================================================
    'upwork': 'contractors',
    'fiverr': 'contractors',
    'toptal': 'contractors',
    '99designs': 'contractors',
    'freelancer': 'contractors',
    'guru': 'contractors',

    # ============================================================================
    # SHIPPING & DELIVERY
    # ============================================================================
    'fedex': 'shipping',
    'ups': 'shipping',
    'usps': 'shipping',
    'dhl': 'shipping',
    'stamps.com': 'shipping',
    'shipstation': 'shipping',
    'easypost': 'shipping',

    # ============================================================================
    # TRAVEL & TRANSPORTATION
    # ============================================================================
    # Airlines
    'united airlines': 'travel',
    'united': 'travel',
    'delta': 'travel',
    'delta airlines': 'travel',
    'american airlines': 'travel',
    'southwest': 'travel',
    'southwest airlines': 'travel',
    'jetblue': 'travel',
    'alaska airlines': 'travel',
    'spirit airlines': 'travel',
    'frontier': 'travel',

    # Rideshare & Ground
    'uber': 'travel',
    'lyft': 'travel',
    'taxi': 'travel',

    # Hotels
    'airbnb': 'travel',
    'vrbo': 'travel',
    'marriott': 'travel',
    'hilton': 'travel',
    'hyatt': 'travel',
    'ihg': 'travel',
    'holiday inn': 'travel',
    'best western': 'travel',

    # Travel booking
    'expedia': 'travel',
    'booking.com': 'travel',
    'hotels.com': 'travel',
    'priceline': 'travel',
    'kayak': 'travel',

    # Car rental
    'hertz': 'travel',
    'enterprise': 'travel',
    'avis': 'travel',
    'budget': 'travel',
    'national': 'travel',
    'alamo': 'travel',
    'dollar': 'travel',
    'thrifty': 'travel',
    'sixt': 'travel',
    'zipcar': 'travel',
    'turo': 'travel',

    # ============================================================================
    # GAS STATIONS & FUEL
    # ============================================================================
    'shell': 'transportation',
    'chevron': 'transportation',
    'exxon': 'transportation',
    'exxonmobil': 'transportation',
    'mobil': 'transportation',
    'bp': 'transportation',
    'marathon': 'transportation',
    'speedway': 'transportation',
    'arco': 'transportation',
    '76': 'transportation',
    'conoco': 'transportation',
    'phillips 66': 'transportation',
    'valero': 'transportation',
    'citgo': 'transportation',
    'sunoco': 'transportation',
    'gulf': 'transportation',
    'texaco': 'transportation',
    'wawa': 'transportation',
    'sheetz': 'transportation',
    'caseys': 'transportation',
    'circle k': 'transportation',
    'kwik trip': 'transportation',
    'pilot': 'transportation',
    'flying j': 'transportation',
    'loves': 'transportation',
    'racetrac': 'transportation',
    'quiktrip': 'transportation',
    'bucees': 'transportation',

    # ============================================================================
    # PARKING
    # ============================================================================
    'spplus': 'transportation',
    'sp plus': 'transportation',
    'parkwhiz': 'transportation',
    'spothero': 'transportation',
    'propark': 'transportation',
    'ace parking': 'transportation',
    'laz parking': 'transportation',
    'ampco parking': 'transportation',

    # ============================================================================
    # PUBLIC TRANSIT
    # ============================================================================
    'mta': 'transportation',
    'bart': 'transportation',
    'cta': 'transportation',
    'mbta': 'transportation',
    'septa': 'transportation',
    'wmata': 'transportation',
    'muni': 'transportation',
    'trimet': 'transportation',
    'nj transit': 'transportation',
    'metrolink': 'transportation',
    'amtrak': 'transportation',
    'caltrain': 'transportation',
    'metra': 'transportation',
    'marta': 'transportation',

    # ============================================================================
    # TOLLS
    # ============================================================================
    'ezpass': 'transportation',
    'fastrak': 'transportation',
    'sunpass': 'transportation',
    'txtag': 'transportation',
    'peach pass': 'transportation',

    # ============================================================================
    # AUTO SERVICES
    # ============================================================================
    'jiffy lube': 'transportation',
    'valvoline': 'transportation',
    'pep boys': 'transportation',
    'midas': 'transportation',
    'meineke': 'transportation',
    'firestone': 'transportation',
    'goodyear': 'transportation',
    'discount tire': 'transportation',
    'autozone': 'transportation',
    'napa': 'transportation',
    'oreilly': 'transportation',
    'advance auto': 'transportation',

    # ============================================================================
    # OFFICE SUPPLIES & RETAIL
    # ============================================================================
    'amazon': 'office',
    'amazon.com': 'office',
    'staples': 'office',
    'office depot': 'office',
    'officemax': 'office',
    'target': 'office',
    'walmart': 'office',
    'costco': 'office',

    # ============================================================================
    # ADVERTISING & MARKETING
    # ============================================================================
    'facebook ads': 'advertising',
    'meta ads': 'advertising',
    'google ads': 'advertising',
    'google adwords': 'advertising',
    'linkedin ads': 'advertising',
    'twitter ads': 'advertising',
    'x ads': 'advertising',
    'instagram ads': 'advertising',
    'tiktok ads': 'advertising',
    'pinterest ads': 'advertising',
    'reddit ads': 'advertising',
    'bing ads': 'advertising',

    # ============================================================================
    # INSURANCE
    # ============================================================================
    'geico': 'insurance',
    'allstate': 'insurance',
    'state farm': 'insurance',
    'progressive': 'insurance',
    'liberty mutual': 'insurance',
    'farmers insurance': 'insurance',
    'nationwide': 'insurance',
    'usaa': 'insurance',

    # ============================================================================
    # FOOD DELIVERY
    # ============================================================================
    'doordash': 'meals',
    'uber eats': 'meals',
    'ubereats': 'meals',
    'grubhub': 'meals',
    'postmates': 'meals',
    'seamless': 'meals',
    'instacart': 'meals',

    # ============================================================================
    # BANKING & FINANCIAL
    # ============================================================================
    'mercury': 'bank_fee',
    'brex': 'bank_fee',
    'ramp': 'bank_fee',
    'divvy': 'bank_fee',
}


def lookup_known_vendor(vendor_name: str) -> str:
    """
    Look up a vendor name in the universal known vendors database.

    Args:
        vendor_name: The vendor/merchant name to look up

    Returns:
        Category hint (e.g., 'software', 'payroll', 'travel')
        or None if vendor is not in the database
    """
    if not vendor_name:
        return None

    # Normalize the vendor name
    clean_name = str(vendor_name).lower().strip()

    # Direct lookup
    if clean_name in KNOWN_VENDORS:
        return KNOWN_VENDORS[clean_name]

    # Try with common suffixes removed
    for suffix in [' inc', ' llc', ' corp', ' ltd', '.com', '.io', '.app']:
        if clean_name.endswith(suffix):
            base_name = clean_name[:-len(suffix)].strip()
            if base_name in KNOWN_VENDORS:
                return KNOWN_VENDORS[base_name]

    # Try substring match (only for longer vendor names to avoid false matches)
    if len(clean_name) >= 8:
        for known_vendor, category in KNOWN_VENDORS.items():
            if known_vendor in clean_name or clean_name in known_vendor:
                return category

    return None


def get_all_known_vendors():
    """Return the complete known vendors dictionary."""
    return KNOWN_VENDORS.copy()


def get_known_vendors_by_category(category_hint: str) -> list:
    """
    Get all known vendors for a specific category hint.

    Args:
        category_hint: The category hint (e.g., 'software', 'travel')

    Returns:
        List of vendor names in that category
    """
    return [vendor for vendor, cat in KNOWN_VENDORS.items() if cat == category_hint]
