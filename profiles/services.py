import requests
import pycountry
import re


COUNTRY_NAMES = {c.alpha_2: c.name for c in pycountry.countries}
COUNTRY_NAME_TO_CODE = {c.name.lower(): c.alpha_2 for c in pycountry.countries}


def classify_age_group(age):
    """
    Converts numeric age to string category.
    Standalone so both the view and seeder can use it.
    """
    if age <= 12:
        return 'child'
    elif age <= 19:
        return 'teenager'
    elif age <= 59:
        return 'adult'
    return 'senior'


def fetch_profile_data(name):
    """
    Calls Genderize, Agify, Nationalize sequentially.
    Returns (data_dict, None) on success.
    Returns (None, 'ApiName') if any API fails or returns bad data.
    """
    results = {}

    try:
        r = requests.get(
            'https://api.genderize.io',
            params={'name': name},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()

        if not data.get('gender') or data.get('count', 0) == 0:
            return None, 'Genderize'

        results['gender'] = data['gender']
        results['gender_probability'] = data['probability']
        results['sample_size'] = data['count']

    except requests.exceptions.RequestException:
        return None, 'Genderize'

    try:
        r = requests.get(
            'https://api.agify.io',
            params={'name': name},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()

        if data.get('age') is None:
            return None, 'Agify'

        results['age'] = data['age']
        results['age_group'] = classify_age_group(data['age'])

    except requests.exceptions.RequestException:
        return None, 'Agify'

    try:
        r = requests.get(
            'https://api.nationalize.io',
            params={'name': name},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()

        countries = data.get('country', [])
        if not countries:
            return None, 'Nationalize'

        top = max(countries, key=lambda x: x['probability'])
        code = top['country_id']
        results['country_id'] = code
        results['country_probability'] = top['probability']
        results['country_name'] = COUNTRY_NAMES.get(code, code)

    except requests.exceptions.RequestException:
        return None, 'Nationalize'

    return results, None


def parse_natural_language_query(q):
    """
    Converts plain English to a filters dict.
    Returns (filters, None) on success.
    Returns (None, 'Unable to interpret query') if nothing matched.

    No AI — pure regex pattern matching.
    """
    q = q.lower().strip()
    filters = {}

    if re.search(r'\b(male|males|man|men)\b', q):
        filters['gender'] = 'male'
    elif re.search(r'\b(female|females|woman|women)\b', q):
        filters['gender'] = 'female'

    if re.search(r'\byoung\b', q):
        filters['min_age'] = 16
        filters['max_age'] = 24
    elif re.search(r'\b(child|children)\b', q):
        filters['age_group'] = 'child'
    elif re.search(r'\b(teenager|teenagers|teen|teens)\b', q):
        filters['age_group'] = 'teenager'
    elif re.search(r'\b(adult|adults)\b', q):
        filters['age_group'] = 'adult'
    elif re.search(r'\b(senior|seniors|elderly)\b', q):
        filters['age_group'] = 'senior'

    above = re.search(r'\b(above|over|older than|greater than)\s+(\d+)\b', q)
    if above:
        filters['min_age'] = int(above.group(2))

    below = re.search(r'\b(below|under|younger than|less than)\s+(\d+)\b', q)
    if below:
        filters['max_age'] = int(below.group(2))

    between = re.search(r'\bbetween\s+(\d+)\s+and\s+(\d+)\b', q)
    if between:
        filters['min_age'] = int(between.group(1))
        filters['max_age'] = int(between.group(2))

    country_match = re.search(
        r'\b(from|in|of)\s+([a-z\s]+?)(?=\s*(above|below|over|under|who|and|with|$))',
        q
    )
    if country_match:
        country_str = country_match.group(2).strip()
        if country_str in COUNTRY_NAME_TO_CODE:
            filters['country_id'] = COUNTRY_NAME_TO_CODE[country_str]
        else:
            for name, code in COUNTRY_NAME_TO_CODE.items():
                if name in country_str or country_str in name:
                    filters['country_id'] = code
                    break

    if not filters:
        return None, 'Unable to interpret query'

    return filters, None