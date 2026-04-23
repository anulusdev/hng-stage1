import json
import os
import pycountry
import uuid6
from django.core.management.base import BaseCommand
from django.utils import timezone
from profiles.models import Profile
from profiles.services import classify_age_group

class Command(BaseCommand):
    help = 'Seed the database with 2026 profiles from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='seed_profiles.json')

    def handle(self, *args, **options):
        filepath = options['file']
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'File not found: {filepath}'))
            return

        created_count = 0
        skipped_count = 0

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('Error: The file is not valid JSON.'))
                return
            
            if isinstance(raw_data, dict):
                if 'data' in raw_data:
                    profiles_data = raw_data['data']
                elif 'profiles' in raw_data:
                    profiles_data = raw_data['profiles']
                else:
                    for key, value in raw_data.items():
                        if isinstance(value, list):
                            profiles_data = value
                            break
            else:
                profiles_data = raw_data
                
            for row in profiles_data:
                name = row.get('name', '').strip().lower()
                if not name:
                    continue

                country_id = row.get('country_id', '')
                country_obj = pycountry.countries.get(alpha_2=country_id)
                country_name = country_obj.name if country_obj else country_id

                _, created = Profile.objects.get_or_create(
                    name=name,
                    defaults={
                        'id': uuid6.uuid7(),
                        'gender': row.get('gender', ''),
                        'gender_probability': float(row.get('gender_probability', 0)),
                        'sample_size': int(row.get('sample_size', 0)),
                        'age': int(row.get('age', 0)),
                        'age_group': classify_age_group(int(row.get('age', 0))),
                        'country_id': country_id,
                        'country_name': country_name,
                        'country_probability': float(row.get('country_probability', 0)),
                        'created_at': timezone.now(),
                    }
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'Seeding complete! Created: {created_count}, Skipped: {skipped_count}'))