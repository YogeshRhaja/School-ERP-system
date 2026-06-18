#core/models.py
from django.db import models
from django.contrib.auth.models import User

class SchoolClass(models.Model):

    class_name = models.CharField(max_length=10)

    def __str__(self):
        return self.class_name


class Section(models.Model):

    section_name = models.CharField(max_length=5)

    def __str__(self):
        return self.section_name


class ClassSection(models.Model):

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('school_class', 'section')

    def __str__(self):
        return f"{self.school_class}-{self.section}"

class AcademicYear(models.Model):
    year_id = models.AutoField(primary_key=True)
    year_name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, default='INACTIVE')

    def __str__(self):
        return self.year_name
class State(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=50)

    def __str__(self):
        return self.state_name

class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="districts"
    )
    district_name = models.CharField(max_length=100)

    def __str__(self):
        return self.district_name


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    student_no = models.PositiveIntegerField(
        unique=True,
        editable=True,
        null=True,
        blank=True
    )
    admission_no = models.CharField(max_length=30, unique=True)
    admission_date = models.DateField()

    ADMISSION_TYPE_CHOICES = [
        ('NEW', 'New'),
        ('TRANSFER', 'Transfer'),
        ('REJOIN', 'Rejoin'),
    ]

    admission_type = models.CharField(
        max_length=30,
        choices=ADMISSION_TYPE_CHOICES,
        default='NEW'
    )
    previous_school = models.CharField(max_length=150, blank=True, null=True)

    student_name = models.CharField(max_length=150)
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )
    dob = models.DateField()
    blood_group = models.CharField(max_length=10)
    nationality = models.CharField(max_length=50)
    religion = models.CharField(max_length=50)
    caste = models.CharField(max_length=50)
    community = models.CharField(max_length=50)

    aadhaar_no = models.CharField(max_length=20)
    emis_no = models.CharField(max_length=30)
    student_photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True
    )

    father_name = models.CharField(max_length=150)
    father_occupation = models.CharField(max_length=100)
    father_contact = models.CharField(max_length=15)
    father_email = models.CharField(max_length=100)

    mother_name = models.CharField(max_length=150)
    mother_occupation = models.CharField(max_length=100)
    mother_contact = models.CharField(max_length=15)
    mother_email = models.CharField(max_length=100)

    guardian_name = models.CharField(max_length=150)
    guardian_relation = models.CharField(max_length=50)
    guardian_contact = models.CharField(max_length=15)

    house_no = models.CharField(max_length=50)
    street = models.CharField(max_length=150)
    town = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)
    pincode = models.CharField(max_length=10)
    medical_conditions = models.TextField()
    emergency_contact_name = models.CharField(max_length=150)
    emergency_contact_no = models.CharField(max_length=15)

    status = models.CharField(max_length=20, default='ACTIVE')
    leaving_date = models.DateField(blank=True, null=True)
    leaving_reason = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.student_no:
            last = Student.objects.order_by('-student_no').first()
            self.student_no = (last.student_no if last else 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_no} - {self.student_name}"
class StudentEnrollment(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE
    )

    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.CASCADE
    )

    roll_no = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):

        if not self.roll_no:

            last_roll = StudentEnrollment.objects.filter(
                academic_year=self.academic_year,
                class_section=self.class_section
            ).order_by('-roll_no').first()

            if last_roll:
                self.roll_no = last_roll.roll_no + 1
            else:
                self.roll_no = 1

        super().save(*args, **kwargs)

    class Meta:
        unique_together = [
            ('student', 'academic_year'),
            ('academic_year', 'class_section', 'roll_no')
        ]

    def __str__(self):
        return f"{self.student} - {self.class_section} - Roll {self.roll_no}"

class FeeCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.category_name

class Term(models.Model):
    term_name = models.CharField(max_length=50)

    def __str__(self):
        return self.term_name
class FeeStructure(models.Model):

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        unique_together = (
            'academic_year',
            'school_class',
            'term',
            'category'
        )

    def __str__(self):
        return f"{self.academic_year} - {self.school_class} - {self.term}"
class StudentFee(models.Model):
    student_fee_id = models.AutoField(primary_key=True)
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE)
    fee = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('enrollment', 'fee')

class FeePayment(models.Model):

    receipt_no = models.AutoField(primary_key=True)

    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Online', 'Online'),
        ('UPI', 'UPI'),
    ]

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES
    )

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Receipt {self.receipt_no} - {self.enrollment.student.student_name} - ₹{self.amount_paid}"
class Employee(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    ACCESS_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)

    employee_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    mobile_no = models.CharField(max_length=15)
    alternate_mobile_no = models.CharField(max_length=15, blank=True, null=True)

    designation = models.CharField(max_length=100)
    employee_photo = models.ImageField(upload_to='employees/', blank=True, null=True)

    date_of_joining = models.DateField()

    door_no = models.CharField(max_length=50)
    street_name = models.CharField(max_length=100)
    town = models.CharField(max_length=100)

    country = models.CharField(max_length=50, default='India')
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pincode = models.CharField(max_length=10)

    access_rights = models.CharField(max_length=20, choices=ACCESS_CHOICES)

    def __str__(self):
        return f"{self.employee_id} - {self.employee_name}"

