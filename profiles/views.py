from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Profile
from .serializers import ProfileCreateSerializer, ProfileSerializer
from .filters import ProfileFilter
from .pagination import ProfilePagination
from .ordering import SeparateParamOrderingFilter
from .services import fetch_profile_data, parse_natural_language_query


@method_decorator(csrf_exempt, name='dispatch')
class ProfileListView(APIView):
    """
    POST /api/profiles  → create profile
    GET  /api/profiles  → list with filtering, sorting, pagination
    """

    filter_backends = [DjangoFilterBackend, SeparateParamOrderingFilter]
    filterset_class = ProfileFilter
    ordering_fields = ['age', 'created_at', 'gender_probability']

    def post(self, request):
        serializer = ProfileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data['name']

        existing = Profile.objects.filter(name=name).first()
        if existing:
            return Response({
                'status': 'success',
                'message': 'Profile already exists',
                'data': ProfileSerializer(existing).data
            }, status=status.HTTP_200_OK)

        data, failed_api = fetch_profile_data(name)
        if data is None:
            return Response({
                'status': '502',
                'message': f'{failed_api} returned an invalid response'
            }, status=status.HTTP_502_BAD_GATEWAY)

        profile = Profile.objects.create(
            name=name,
            gender=data['gender'],
            gender_probability=data['gender_probability'],
            sample_size=data['sample_size'],
            age=data['age'],
            age_group=data['age_group'],
            country_id=data['country_id'],
            country_name=data['country_name'],
            country_probability=data['country_probability'],
        )

        return Response({
            'status': 'success',
            'data': ProfileSerializer(profile).data
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        queryset = Profile.objects.all()

        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)

        paginator = ProfilePagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProfileSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })


@method_decorator(csrf_exempt, name='dispatch')
class ProfileDetailView(APIView):
    """
    GET    /api/profiles/{id} → retrieve single profile
    DELETE /api/profiles/{id} → delete profile
    """

    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'status': 'success',
            'data': ProfileSerializer(profile).data
        })

    def delete(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileSearchView(APIView):
    """
    GET /api/profiles/search?q=young males from nigeria

    Parses natural language → filters dict → same queryset pipeline.
    Supports page and limit params for pagination.
    """

    def get(self, request):
        q = request.GET.get('q', '').strip()

        if not q:
            return Response(
                {'status': 'error', 'message': 'q parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        filters, error = parse_natural_language_query(q)
        if error:
            return Response(
                {'status': 'error', 'message': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = Profile.objects.all()
        filterset = ProfileFilter(filters, queryset=queryset)
        if not filterset.is_valid():
            return Response(
                {'status': 'error', 'message': 'Invalid query parameters'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        queryset = filterset.qs

        paginator = ProfilePagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProfileSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'page': 1,
            'limit': 10,
            'total': queryset.count(),
            'data': serializer.data
        })