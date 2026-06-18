from django.core.management.base import BaseCommand
from core.models import AcademicYear
from datetime import date

class Command(BaseCommand):
    help = "Generate Academic Years from 2001 to 2050"

    def handle(self, *args, **kwargs):
        AcademicYear.objects.all().update(status='INACTIVE')

        current_year = date.today().year

        for year in range(2001, 2050):
            start_year = year
            end_year = year + 1

            year_name = f"{start_year}-{end_year}"
            start_date = date(start_year, 5, 1)
            end_date = date(end_year, 5, 1)

            status = 'ACTIVE' if start_year == current_year else 'INACTIVE'

            AcademicYear.objects.get_or_create(
                year_name=year_name,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'status': status
                }
            )

        self.stdout.write(self.style.SUCCESS("Academic years generated successfully"))
