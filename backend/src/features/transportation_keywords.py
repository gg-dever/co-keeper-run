"""
Transportation Business Recognition for CoKeeper
================================================

Comprehensive keyword patterns and vendor lists for identifying American
transportation-related businesses in transaction descriptions.

This module provides structured lookups for 8 transportation categories:
- Airlines
- Rideshare/Taxi
- Gas Stations
- Parking
- Public Transit
- Tolls
- Car Rental
- Auto Services

Usage:
    from src.features.transportation_keywords import detect_transportation_type

    result = detect_transportation_type("UNITED AIRLINES PURCHASE")
    # Returns: 'airline'
"""

# ============================================================================
# AIRLINES - Major US carriers
# ============================================================================
AIRLINES = {
    'united', 'united airlines', 'ual',
    'delta', 'delta airlines', 'delta air',
    'american airlines', 'american air', 'aa.com',
    'southwest', 'southwest airlines', 'swa',
    'jetblue', 'jet blue',
    'alaska airlines', 'alaska air',
    'spirit airlines', 'spirit air',
    'frontier', 'frontier airlines',
    'allegiant', 'allegiant air',
    'hawaiian airlines',
    'sun country',
    'breeze airways',
    'avelo airlines',
}

# ============================================================================
# RIDESHARE & TAXI
# ============================================================================
RIDESHARE = {
    'uber', 'uber trip', 'uber eats', 'ubereats',
    'lyft',
    'taxi', 'cab', 'yellow cab', 'checker cab',
    'via', 'via rideshare',
    'curb', 'gett',
}

# ============================================================================
# GAS STATIONS - Major national chains
# ============================================================================
GAS_STATIONS = {
    # Major brands
    'shell', 'shell oil',
    'chevron',
    'exxon', 'exxonmobil',
    'mobil',
    'bp', 'british petroleum',
    'marathon', 'marathon petroleum',
    'speedway',
    'arco',
    '76', 'union 76',
    'conoco', 'conocophillips',
    'phillips 66',
    'valero',
    'citgo',
    'sunoco',
    'gulf', 'gulf oil',
    'getty',
    'texaco',

    # Regional/Other
    'wawa', 'sheetz', 'casey\'s', 'caseys',
    'circle k', 'kwik trip',
    'maverik', 'pilot', 'flying j',
    'love\'s', 'loves',
    'racetrac', 'racetrack',
    'quiktrip', 'qt',
    'bucees', 'buc-ees',
    'flash foods', 'flash food',
    'costco gas', 'sam\'s club gas',
    'sams club gas',
}

# Gas station keywords (for stations with numbers like "SHELL #1234")
GAS_KEYWORDS = {'gas station', 'fuel', 'gasoline', 'diesel', 'pump'}

# ============================================================================
# PARKING
# ============================================================================
PARKING = {
    # National operators
    'sp+', 'spplus', 'sp plus', 'standard parking',
    'parkwhiz', 'park whiz',
    'spothero', 'spot hero',
    'propark', 'pro park',
    'ace parking',
    'impark',
    'laz parking', 'laz',
    'ampco', 'ampco parking',
    'central parking',
    'premium parking',
    'Icon parking',

    # Airport parking
    'airport parking',
    'park n fly', 'park and fly',
    'the parking spot',
    'way.com',

    # Valet
    'valet', 'valet parking',
}

# Parking keywords
PARKING_KEYWORDS = {
    'parking', 'park', 'garage', 'lot',
    'meter', 'parkade', 'park & fly',
}

# ============================================================================
# PUBLIC TRANSIT - City systems
# ============================================================================
PUBLIC_TRANSIT = {
    # Major systems
    'mta', 'metropolitan transportation', 'metro',
    'bart', 'bay area rapid transit',
    'cta', 'chicago transit',
    'mbta',
    'septa',
    'wmata', 'washington metro',
    'muni', 'sf muni',
    'trimet',
    'metro transit',
    'nj transit', 'new jersey transit',
    'metrolink',
    'amtrak',
    'caltrain',
    'marc', 'marc train',
    'metra',
    'rtd', 'rtd denver',
    'king county metro',
    'marta', 'atlanta transit',
    'lynx',
    'metro rail',
    'light rail',
    'commuter rail',

    # Cards/Passes
    'clipper', 'clipper card',
    'ventra', 'ventra card',
    'orca', 'orca card',
    'charlie card', 'charliecard',
    'smartrip', 'smart trip',
    'tap', 'tap card',
}

# Transit keywords
TRANSIT_KEYWORDS = {
    'subway', 'train', 'transit', 'rail',
    'bus', 'trolley', 'streetcar', 'light rail',
}

# ============================================================================
# TOLLS
# ============================================================================
TOLLS = {
    # Electronic toll systems
    'ezpass', 'ez pass', 'e-zpass',
    'fastrak', 'fast trak',
    'sunpass', 'sun pass',
    'i-pass', 'ipass',
    'k-tag', 'ktag',
    'txtag', 'tx tag',
    'pikepass', 'pike pass',
    'palmetto pass',
    'epass', 'e-pass',
    'nc quick pass',
    'peach pass',
    'go toll',

    # Specific roads/bridges
    'turnpike', 'toll road', 'tollway',
    'golden gate bridge',
    'bay bridge',
    'george washington bridge', 'gw bridge',
    'lincoln tunnel',
    'holland tunnel',
    'pennsylvania turnpike', 'pa turnpike',
    'florida turnpike',
    'ohio turnpike',
    'indiana toll road',
    'illinois tollway',
    'new jersey turnpike', 'nj turnpike',
    'mass pike', 'massachusetts turnpike',
}

# Toll keywords
TOLL_KEYWORDS = {'toll', 'bridge', 'tunnel', 'express lane'}

# ============================================================================
# CAR RENTAL
# ============================================================================
CAR_RENTAL = {
    'hertz',
    'enterprise', 'enterprise rent',
    'avis',
    'budget', 'budget rent',
    'national', 'national car',
    'alamo',
    'dollar', 'dollar rent',
    'thrifty',
    'sixt',
    'zipcar', 'zip car',
    'turo',
    'getaround', 'get around',
    'car2go',
}

# ============================================================================
# AUTO SERVICES
# ============================================================================
AUTO_SERVICES = {
    # Repairs & Maintenance
    'jiffy lube',
    'valvoline',
    'pep boys',
    'midas',
    'meineke',
    'maaco',
    'aamco',
    'firestone',
    'goodyear',
    'discount tire',
    'tire plus', 'tireplus',
    'big o tires',

    # Car wash
    'car wash', 'carwash',
    'auto spa',
    'wash depot',

    # Auto parts
    'autozone', 'auto zone',
    'napa', 'napa auto',
    'o\'reilly', 'oreilly',
    'advance auto',
    'car quest', 'carquest',
}

# Auto service keywords
AUTO_KEYWORDS = {
    'auto repair', 'mechanic', 'oil change',
    'tire', 'tires', 'brake', 'brakes',
    'smog check', 'inspection',
    'car wash', 'detail',
}


def detect_transportation_type(description: str, vendor_name: str = None) -> str:
    """
    Detect if a transaction is transportation-related and return the category.

    Args:
        description: Transaction description/memo
        vendor_name: Optional cleaned vendor name

    Returns:
        One of: 'airline', 'rideshare', 'gas_station', 'parking',
                'public_transit', 'toll', 'car_rental', 'auto_service'
        or None if not transportation-related
    """
    if not description:
        return None

    # Combine description and vendor for searching
    search_text = description.lower()
    if vendor_name:
        search_text += ' ' + vendor_name.lower()

    # Check exact matches first (most specific)
    if any(airline in search_text for airline in AIRLINES):
        return 'airline'

    if any(ride in search_text for ride in RIDESHARE):
        return 'rideshare'

    if any(gas in search_text for gas in GAS_STATIONS):
        return 'gas_station'

    if any(rental in search_text for rental in CAR_RENTAL):
        return 'car_rental'

    if any(transit in search_text for transit in PUBLIC_TRANSIT):
        return 'public_transit'

    if any(toll in search_text for toll in TOLLS):
        return 'toll'

    if any(park in search_text for park in PARKING):
        return 'parking'

    if any(auto in search_text for auto in AUTO_SERVICES):
        return 'auto_service'

    # Check keywords (less specific, requires longer matches to avoid false positives)
    if len(search_text) >= 10:  # Only check keywords on substantial text
        if any(keyword in search_text for keyword in GAS_KEYWORDS):
            return 'gas_station'

        if any(keyword in search_text for keyword in PARKING_KEYWORDS):
            return 'parking'

        if any(keyword in search_text for keyword in TRANSIT_KEYWORDS):
            return 'public_transit'

        if any(keyword in search_text for keyword in TOLL_KEYWORDS):
            return 'toll'

        if any(keyword in search_text for keyword in AUTO_KEYWORDS):
            return 'auto_service'

    return None


def get_all_transportation_vendors():
    """Return all transportation vendor names as a flat list."""
    all_vendors = []
    all_vendors.extend(AIRLINES)
    all_vendors.extend(RIDESHARE)
    all_vendors.extend(GAS_STATIONS)
    all_vendors.extend(PARKING)
    all_vendors.extend(PUBLIC_TRANSIT)
    all_vendors.extend(TOLLS)
    all_vendors.extend(CAR_RENTAL)
    all_vendors.extend(AUTO_SERVICES)
    return all_vendors


def get_transportation_vendors_by_type(transport_type: str):
    """
    Get all vendors for a specific transportation type.

    Args:
        transport_type: One of 'airline', 'rideshare', 'gas_station', 'parking',
                       'public_transit', 'toll', 'car_rental', 'auto_service'
    """
    mapping = {
        'airline': AIRLINES,
        'rideshare': RIDESHARE,
        'gas_station': GAS_STATIONS,
        'parking': PARKING,
        'public_transit': PUBLIC_TRANSIT,
        'toll': TOLLS,
        'car_rental': CAR_RENTAL,
        'auto_service': AUTO_SERVICES,
    }
    return mapping.get(transport_type, set())
