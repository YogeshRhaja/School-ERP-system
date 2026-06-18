# core/admin.py
from django.contrib import admin
from .models import *

admin.site.register(AcademicYear)
admin.site.register(State)
admin.site.register(District)
admin.site.register(Student)
admin.site.register(StudentEnrollment)
admin.site.register(FeeCategory)
admin.site.register(FeeStructure)
admin.site.register(FeePayment)
admin.site.register(Term)


