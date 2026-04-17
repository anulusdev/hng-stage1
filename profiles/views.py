from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests
import json
from .models import Profile


def fetch_profile_data(name):
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

        age = data['age']
        results['age'] = age

        if age <= 12:
            results['age_group'] = 'child'
        elif age <= 19:
            results['age_group'] = 'teenager'
        elif age <= 59:
            results['age_group'] = 'adult'
        else:
            results['age_group'] = 'senior'

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

        top_country = max(countries, key=lambda x: x['probability'])
        results['country_id'] = top_country['country_id']
        results['country_probability'] = top_country['probability']

    except requests.exceptions.RequestException:
        return None, 'Nationalize'

    return results, None


def format_profile(profile, full=True):
    if full:
        return {
            'id': str(profile.id),
            'name': profile.name,
            'gender': profile.gender,
            'gender_probability': profile.gender_probability,
            'sample_size': profile.sample_size,
            'age': profile.age,
            'age_group': profile.age_group,
            'country_id': profile.country_id,
            'country_probability': profile.country_probability,
            'created_at': profile.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    else:
        return {
            'id': str(profile.id),
            'name': profile.name,
            'gender': profile.gender,
            'age': profile.age,
            'age_group': profile.age_group,
            'country_id': profile.country_id,
        }


@method_decorator(csrf_exempt, name='dispatch')
class ProfileListView(View):

    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid JSON body'},
                status=400
            )

        name = body.get('name', '')

        if not name or not str(name).strip():
            return JsonResponse(
                {'status': 'error', 'message': 'name is required'},
                status=400
            )

        if not isinstance(name, str):
            return JsonResponse(
                {'status': 'error', 'message': 'name must be a string'},
                status=422
            )

        name = name.strip().lower()

        existing = Profile.objects.filter(name=name).first()
        if existing:
            return JsonResponse({
                'status': 'success',
                'message': 'Profile already exists',
                'data': format_profile(existing)
            }, status=200)

        data, failed_api = fetch_profile_data(name)

        if data is None:
            return JsonResponse({
                'status': '502',
                'message': f'{failed_api} returned an invalid response'
            }, status=502)

        profile = Profile.objects.create(
            name=name,
            gender=data['gender'],
            gender_probability=data['gender_probability'],
            sample_size=data['sample_size'],
            age=data['age'],
            age_group=data['age_group'],
            country_id=data['country_id'],
            country_probability=data['country_probability']
        )

        return JsonResponse({
            'status': 'success',
            'data': format_profile(profile)
        }, status=201)

    def get(self, request):
        queryset = Profile.objects.all()

        gender = request.GET.get('gender')
        country_id = request.GET.get('country_id')
        age_group = request.GET.get('age_group')

        if gender:
            queryset = queryset.filter(gender__iexact=gender)
        if country_id:
            queryset = queryset.filter(country_id__iexact=country_id)
        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)

        profiles = [format_profile(p, full=False) for p in queryset]

        return JsonResponse({
            'status': 'success',
            'count': len(profiles),
            'data': profiles
        }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileDetailView(View):

    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'Profile not found'},
                status=404
            )

        return JsonResponse({
            'status': 'success',
            'data': format_profile(profile)
        }, status=200)

    def delete(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'Profile not found'},
                status=404
            )

        profile.delete()
        return JsonResponse({}, status=204)