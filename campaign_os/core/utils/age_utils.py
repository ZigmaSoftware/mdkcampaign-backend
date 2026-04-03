"""
Age group utilities — single source of truth for age-based segmentation.

Groups:
  Below 18  →  age < 18
  18-25     →  18 ≤ age ≤ 25
  26-35     →  26 ≤ age ≤ 35
  36-45     →  36 ≤ age ≤ 45
  46-60     →  46 ≤ age ≤ 60
  60+       →  age > 60
"""

from django.db.models import Q

AGE_GROUPS = ['Below 18', '18-25', '26-35', '36-45', '46-60', '60+']

_AGE_GROUP_FILTERS = {
    'Below 18': Q(age__lt=18),
    '18-25':    Q(age__gte=18, age__lte=25),
    '26-35':    Q(age__gte=26, age__lte=35),
    '36-45':    Q(age__gte=36, age__lte=45),
    '46-60':    Q(age__gte=46, age__lte=60),
    '60+':      Q(age__gt=60),
}


def age_group_q(group: str) -> Q:
    """Return a Django Q filter for the given age group label.

    All groups exclude null ages automatically because Django ORM
    comparisons on nullable fields never match NULL.
    Returns an empty Q (no-op) for unknown labels.
    """
    return _AGE_GROUP_FILTERS.get(group, Q())


def build_age_filter(age_group_param: str) -> Q:
    """Parse a comma-separated age_group query string and return a combined Q.

    Example: "18-25,26-35" → Q(age__gte=18, age__lte=25) | Q(age__gte=26, age__lte=35)
    Returns an empty Q (no filter) when param is empty or has no valid groups.
    """
    if not age_group_param:
        return Q()
    groups = [g.strip() for g in age_group_param.split(',') if g.strip() in _AGE_GROUP_FILTERS]
    if not groups:
        return Q()
    combined = Q()
    for g in groups:
        combined |= _AGE_GROUP_FILTERS[g]
    return combined
