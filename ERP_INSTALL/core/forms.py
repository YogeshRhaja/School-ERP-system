#core/forms.py
from django import forms
from .models import (
    FeePayment,
)
from django import forms
from .models import StudentEnrollment, AcademicYear, ClassSection, SchoolClass, Section, Student
from .models import  District


class StudentForm(forms.ModelForm):

    class Meta:
        model = Student
        exclude = [
            'student_id',
            'created_at',
            'updated_at',
            'status',
            'leaving_date',
            'leaving_reason',
        ]

        widgets = {
            'admission_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'dob': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply Bootstrap to all fields
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

        # District filtering logic
        self.fields['district'].queryset = District.objects.all()

        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['district'].queryset = District.objects.filter(
                    state_id=state_id
                ).order_by('district_name')

            except (ValueError, TypeError):
                pass

        elif self.instance.pk and self.instance.state:
            self.fields['district'].queryset = District.objects.filter(
                state=self.instance.state
            ).order_by('district_name')

    # -----------------------------
    # VALIDATIONS
    # -----------------------------

    def clean_student_no(self):
        student_no = self.cleaned_data.get('student_no')

        if student_no is not None:
            qs = Student.objects.filter(student_no=student_no)

            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError("Student number already exists.")

        return student_no

    def clean_admission_no(self):
        admission_no = self.cleaned_data.get('admission_no')

        qs = Student.objects.filter(admission_no=admission_no)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Admission number already exists.")

        return admission_no

    def clean_emis_no(self):
        emis_no = self.cleaned_data.get('emis_no')

        if emis_no:
            qs = Student.objects.filter(emis_no=emis_no)

            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError("EMIS number already exists.")

        return emis_no

    def clean(self):
        cleaned_data = super().clean()

        student_no = cleaned_data.get("student_no")
        admission_no = cleaned_data.get("admission_no")

        if student_no:
            if Student.objects.filter(student_no=student_no).exclude(pk=self.instance.pk).exists():
                self.add_error("student_no", "Student number already exists.")

        if admission_no:
            if Student.objects.filter(admission_no=admission_no).exclude(pk=self.instance.pk).exists():
                self.add_error("admission_no", "Admission number already exists.")

        return cleaned_data
# core/forms.py
class StudentEnrollmentForm(forms.ModelForm):
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),  # initially empty
        label="Section",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StudentEnrollment
        fields = ['student', 'academic_year', 'school_class', 'section']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        # Pop 'mode' so it doesn’t cause TypeError
        mode = kwargs.pop('mode', None)
        super().__init__(*args, **kwargs)


        # Customize fields based on mode (optional)
        if mode == 'INDIVIDUAL':
            # Example: show only active students
            self.fields['student'].queryset = Student.objects.filter(status='ACTIVE')
        elif mode == 'CLASS':
            # Example: hide student field in class promotion mode
            self.fields['student'].widget = forms.HiddenInput()

            # Set section queryset based on selected school_class
            if 'school_class' in self.data:
                try:
                    class_id = int(self.data.get('school_class'))
                    self.fields['section'].queryset = Section.objects.filter(
                        id__in=ClassSection.objects.filter(school_class_id=class_id).values_list('section_id',
                                                                                                 flat=True)
                    )
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk:
                school_class = self.instance.class_section.school_class

                self.fields['school_class'].initial = school_class

                self.fields['section'].queryset = Section.objects.filter(
                    id__in=ClassSection.objects.filter(
                        school_class=school_class).values_list('section_id', flat=True)).distinct()
                self.fields['section'].initial = self.instance.class_section.section
            self.fields['section'].initial = self.instance.class_section.section

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        academic_year = cleaned_data.get("academic_year")

        if student and academic_year:
            if StudentEnrollment.objects.filter(
                    student=student,
                    academic_year=academic_year
            ).exists():
                raise forms.ValidationError(
                    "This student is already enrolled in this academic year."
                )

        return cleaned_data

class FeePaymentForm(forms.ModelForm):

    class Meta:
        model = FeePayment
        fields = [
            'enrollment',
            'fee_structure',   # ✅ IMPORTANT
            'amount_paid',
            'payment_mode'
        ]

        widgets = {
            'enrollment': forms.Select(attrs={'class': 'form-control'}),
            'fee_structure': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_amount_paid(self):
        amount = self.cleaned_data['amount_paid']

        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than 0")

        return amount

class ClassPromotionForm(forms.Form):
    to_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.filter(status='ACTIVE').order_by('-start_date'),  # Next year first
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all().order_by('class_name'),  # Populates dropdown
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'school_class_promote'})
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'section_promote'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Filter classes by grade level logic if needed

    def clean(self):
        cleaned_data = super().clean()
        school_class = cleaned_data.get('school_class')
        section = cleaned_data.get('section')
        if school_class and section:
            try:
                class_section = ClassSection.objects.filter(
                    school_class=school_class,
                    section=section
                ).first()

                if not class_section:
                    raise forms.ValidationError("Invalid Class-Section combination.")

                cleaned_data['to_class_section'] = class_section
            except ClassSection.DoesNotExist:
                raise forms.ValidationError("Invalid Class-Section combination.")
        elif not school_class or not section:
            raise forms.ValidationError("Please select both Class and Section.")
        return cleaned_data

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['year_name', 'start_date', 'end_date', 'status']

        widgets = {
            'year_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2025-2026'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'status': forms.Select(
                choices=[('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE')],
                attrs={'class': 'form-control'}
            )
        }

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and start >= end:
            raise forms.ValidationError(
                "End date must be after start date"
            )

        return cleaned_data
class IndividualEnrollmentForm(forms.ModelForm):

    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        label="Student No",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StudentEnrollment
        fields = ['student', 'academic_year', 'class_section', 'roll_no']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'class_section': forms.Select(attrs={'class': 'form-control'}),
            'roll_no': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_year = AcademicYear.objects.filter(status='ACTIVE').first()

        if active_year:
            enrolled_students = StudentEnrollment.objects.filter(
                academic_year=active_year
            ).values_list('student_id', flat=True)

            self.fields['student'].queryset = Student.objects.exclude(
                id__in=enrolled_students
            )
        else:
            self.fields['student'].queryset = Student.objects.all()

        self.fields['academic_year'].queryset = AcademicYear.objects.filter(status='ACTIVE')
        self.fields['class_section'].queryset = ClassSection.objects.all()

class ClassEnrollmentForm(forms.Form):

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False
    )

    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        required=False
    )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    to_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all()
    )

    to_class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all()
    )
class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['class_name']  # only class_name
class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['section_name']  # only section_name
class ClassSectionForm(forms.ModelForm):
    class Meta:
        model = ClassSection
        fields = ['school_class', 'section']
from django import forms
from django.contrib.auth.models import User
from .models import Employee

from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(),
        label="Login Password"
    )

    date_of_joining = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Employee
        exclude = ['user']
        widgets = {
            'state': forms.Select(attrs={'id': 'id_state'}),
            'district': forms.Select(attrs={'id': 'id_district'}),
        }
from .models import FeeStructure

class FeeStructureForm(forms.ModelForm):

    class Meta:
        model = FeeStructure
        fields = [
            'academic_year',
            'school_class',
            'term',
            'category',
            'amount'
        ]

        widgets = {
            'academic_year': forms.Select(attrs={'class':'form-control'}),
            'school_class': forms.Select(attrs={'class':'form-control'}),
            'term': forms.Select(attrs={'class':'form-control'}),
            'category': forms.Select(attrs={'class':'form-control'}),
            'amount': forms.NumberInput(attrs={'class':'form-control'}),
        }
from django import forms
from .models import FeeCategory

class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ['category_name']
