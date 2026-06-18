#core/views.py
from .models import *
from django.contrib.auth import authenticate, login, logout
from .forms import (
    StudentForm,
    AcademicYearForm
)
from .forms import FeeCategoryForm
# core/views.py
from .models import District
from django.contrib.auth.models import User
from .forms import EmployeeForm
from .models import Employee
from django.contrib.auth.decorators import login_required, user_passes_test

def is_employee_or_admin(user):
    return user.is_superuser or user.groups.filter(name='Employee').exists()
# ---------- LOGIN ----------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'core/login.html')


# ---------- LOGOUT ----------
def logout_view(request):
    logout(request)
    return redirect('login')

# ---------- PROTECTED VIEWS ----------
@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'core/dashboard.html')


@login_required
def students_list(request):

    years = AcademicYear.objects.all().order_by('-start_date')
    classes = SchoolClass.objects.all().order_by('class_name')

    enrollments = StudentEnrollment.objects.select_related(
        'student',
        'academic_year',
        'class_section__school_class',
        'class_section__section'
    )

    year_id = request.GET.get('year')
    class_id = request.GET.get('class_filter')
    section_id = request.GET.get('section_filter')

    if year_id:
        enrollments = enrollments.filter(academic_year_id=year_id)

    if class_id:
        enrollments = enrollments.filter(class_section__school_class_id=class_id)

    if section_id:
        enrollments = enrollments.filter(class_section__section_id=section_id)

    context = {
        'enrollments': enrollments,
        'years': years,
        'classes': classes,
        'year': year_id,
        'class_filter': class_id,
        'section_filter': section_id
    }

    return render(request, 'core/students_list.html', context)

@login_required(login_url='login')
def student_create(request):

    form = StudentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'core/student_form.html', {
        'form': form
    })

from django.contrib.auth.decorators import login_required

from django.db.models import OuterRef, Subquery
from .models import  Student
from .forms import StudentEnrollmentForm, ClassPromotionForm

@login_required(login_url='login')
def enroll_student(request):
    mode = request.GET.get('mode', 'INDIVIDUAL').strip().upper()
    action = request.POST.get('action') or request.GET.get('action', 'view')

    # =========================
    # INDIVIDUAL MODE
    # =========================
    if mode == 'INDIVIDUAL':
        # Get already enrolled students
        active_year = AcademicYear.objects.filter(status='ACTIVE').first()

        enrolled_ids = StudentEnrollment.objects.filter(
            academic_year=active_year
        ).values_list('student_id', flat=True)
        students = Student.objects.filter(status='ACTIVE').exclude(student_id__in=enrolled_ids)

        if request.method == "POST":
            student_ids = request.POST.getlist('student')
            academic_year = request.POST.get('academic_year')
            school_class = request.POST.get('school_class')
            section = request.POST.get('section')

            if not student_ids:
                messages.error(request, "Please select at least one student")
                return redirect('/enroll/?mode=INDIVIDUAL')

            if not academic_year or not school_class or not section:
                messages.error(request, "Select academic year, class, and section")
                return redirect('/enroll/?mode=INDIVIDUAL')

            try:
                class_section = ClassSection.objects.get(
                    school_class_id=school_class,
                    section_id=section
                )
                for sid in student_ids:

                    if StudentEnrollment.objects.filter(
                            student_id=sid,
                            academic_year_id=academic_year
                    ).exists():
                        messages.warning(
                            request,
                            f"Student {sid} is already enrolled in this academic year."
                        )
                        continue

                    StudentEnrollment.objects.create(
                        student_id=int(sid),
                        academic_year_id=int(academic_year),
                        class_section=class_section
                    )
                messages.success(request, "Students enrolled successfully")
            except ClassSection.DoesNotExist:
                messages.error(request, "Selected class and section combination does not exist")

            return redirect('/enroll/?mode=INDIVIDUAL')

        # GET request: render form
        form = StudentEnrollmentForm(mode='INDIVIDUAL')
        return render(request, 'core/enrollment_form.html', {
            'form': form,
            'mode': mode,
            'students': students,
            'action': action,
        })

    # =========================
    # CLASS MODE
    # =========================
    elif mode == 'CLASS':

        latest_enrollment = StudentEnrollment.objects.filter(
            student=OuterRef('student')
        ).order_by('-academic_year_id')

        enrollments = StudentEnrollment.objects.filter(
            id=Subquery(latest_enrollment.values('id')[:1])
        ).select_related(
            'student',
            'academic_year',
            'class_section__school_class',
            'class_section__section'
        )

        # FILTERS
        from_year = request.GET.get('year')
        from_class = request.GET.get('class')
        from_section = request.GET.get('section')

        if from_year:
            enrollments = enrollments.filter(academic_year_id=from_year)
        if from_class:
            enrollments = enrollments.filter(class_section__school_class_id=from_class)
        if from_section:
            enrollments = enrollments.filter(class_section__section_id=from_section)

        if request.method == "POST":
            selected_ids = request.POST.getlist("enrollment_ids")
            to_year = request.POST.get("to_year")
            to_class = request.POST.get("school_class")
            to_section = request.POST.get("section")

            if selected_ids and to_year and to_class and to_section:
                try:
                    new_class_section = ClassSection.objects.get(
                        school_class_id=to_class,
                        section_id=to_section
                    )
                    for eid in selected_ids:

                        old_enroll = StudentEnrollment.objects.get(id=eid)

                        if StudentEnrollment.objects.filter(
                                student=old_enroll.student,
                                academic_year_id=to_year
                        ).exists():
                            messages.warning(
                                request,
                                f"{old_enroll.student.student_name} already enrolled in this year."
                            )
                            continue

                        StudentEnrollment.objects.create(
                            student=old_enroll.student,
                            academic_year_id=to_year,
                            class_section=new_class_section
                        )
                    messages.success(request, "Students promoted and new enrollment created successfully")
                except ClassSection.DoesNotExist:
                    messages.error(request, "Selected class and section combination does not exist")

            return redirect('/enroll/?mode=CLASS')

        filter_form = ClassPromotionForm(request.GET or None)
        promote_form = ClassPromotionForm()
        return render(request, 'core/enrollment_form.html', {
            'mode': 'CLASS',
            'filter_form': filter_form,
            'form': promote_form,
            'enrollments': enrollments,

            # IMPORTANT
            'academic_years': AcademicYear.objects.all(),
            'classes': SchoolClass.objects.all(),
            'sections': Section.objects.all(),
        })

    # =========================
    # FALLBACK
    # =========================
    else:
        messages.warning(request, "Invalid mode selected, switched to Individual mode")
        return redirect('/enroll/?mode=INDIVIDUAL')
@login_required(login_url='login')
def fee_structure_view(request):
    fees = FeeStructure.objects.all()
    return render(request, 'core/fee_structure.html', {'fees': fees})

@login_required(login_url='login')
@user_passes_test(is_employee_or_admin)
def fee_payment(request):

    years = AcademicYear.objects.all()
    classes = SchoolClass.objects.all()

    return render(request,'core/fee_payment.html',{
        'years': years,
        'classes': classes
    })
from django.shortcuts import render, get_object_or_404, redirect
from .models import StudentEnrollment, ClassSection, Section
from .forms import SectionUpdateForm

def edit_enrollment(request, id):
    enrollment = get_object_or_404(StudentEnrollment, id=id)

    # Get current class
    current_class = enrollment.class_section.school_class

    # Filter only sections available in this class
    sections = Section.objects.filter(
        classsection__school_class=current_class
    ).distinct()

    form = SectionUpdateForm(request.POST or None)
    form.fields['section'].queryset = sections

    if request.method == 'POST' and form.is_valid():
        selected_section = form.cleaned_data['section']

        # Convert Section → ClassSection
        class_section = ClassSection.objects.get(
            school_class=current_class,
            section=selected_section
        )

        enrollment.class_section = class_section
        enrollment.save()

        return redirect('students_list')

    return render(request, 'core/edit_enrollment.html', {
        'form': form,
        'enrollment': enrollment
    })
def load_students(request):
    year_id = request.GET.get("year")
    class_id = request.GET.get("class_id")

    enrollments = StudentEnrollment.objects.select_related(
        "student",
        "academic_year",
        "class_section__school_class"
    )

    if year_id:
        enrollments = enrollments.filter(academic_year_id=year_id)
    if class_id:
        enrollments = enrollments.filter(class_section__school_class_id=class_id)

    enrollments = enrollments.order_by("roll_no")

    data = [
        {
            "id": e.id,
            "name": f"{e.student.student_no} - {e.student.student_name}",
            "academic_year_id": e.academic_year.year_id,
            "academic_year_name": e.academic_year.year_name
        }
        for e in enrollments
    ]

    return JsonResponse(data, safe=False)

def load_terms(request):

    enrollment_id = request.GET.get("enrollment_id")

    enrollment = get_object_or_404(StudentEnrollment, id=enrollment_id)

    terms = FeeStructure.objects.filter(
        academic_year=enrollment.academic_year,
        school_class=enrollment.class_section.school_class
    ).values(
        "term__id",
        "term__term_name"
    ).distinct()

    data = [
        {
            "id": t["term__id"],
            "name": t["term__term_name"]
        }
        for t in terms
    ]

    return JsonResponse(data, safe=False)
from decimal import Decimal
from django.template.loader import render_to_string


def load_fees(request):
    enrollment_id = request.GET.get("enrollment_id")
    term_id = request.GET.get("term_id")
    academic_year_id = request.GET.get("academic_year_id")

    if not enrollment_id:
        return JsonResponse({"error": "Enrollment ID missing"})

    enrollment = get_object_or_404(
        StudentEnrollment.objects.select_related(
            "student",
            "academic_year",
            "class_section__school_class"
        ),
        id=enrollment_id
    )

    # Determine academic year
    academic_year = enrollment.academic_year
    if academic_year_id:
        try:
            academic_year = AcademicYear.objects.get(year_id=academic_year_id)
        except AcademicYear.DoesNotExist:
            pass

    # Load terms
    terms = FeeStructure.objects.filter(
        academic_year=academic_year,
        school_class=enrollment.class_section.school_class
    ).values("term__id", "term__term_name").distinct()

    fees = []
    total = paid_total = balance_total = total_scholarship = Decimal("0")

    if term_id:
        try:
            term_id = int(term_id)
        except ValueError:
            term_id = None

        fee_structures = FeeStructure.objects.filter(
            academic_year=academic_year,
            school_class=enrollment.class_section.school_class,
            term_id=term_id
        ).select_related("category")

        # Get total scholarship for this student and academic year
        scholarship_total = ScholarshipPosting.objects.filter(
            student=enrollment.student,
            academic_year=academic_year
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        remaining_scholarship = scholarship_total

        for fee in fee_structures:
            paid = FeePayment.objects.filter(
                enrollment=enrollment,
                fee_structure=fee
            ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or Decimal("0")

            # ✅ Get scholarship actually applied for THIS fee
            applied_scholarship = FeePayment.objects.filter(
                enrollment=enrollment,
                fee_structure=fee,
                payment_mode="Scholarship"
            ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or Decimal("0")

            # ✅ Correct balance (no fake scholarship deduction)
            balance = max(fee.amount - paid, Decimal("0"))

            fees.append({
                "category": fee.category.category_name,
                "total": fee.amount,
                "paid": paid,
                "balance": balance,
                "scholarship_applied": applied_scholarship,
                "fee_id": fee.id
            })

            total += fee.amount
            paid_total += paid
            balance_total += balance
            total_scholarship += applied_scholarship

    html = render_to_string(
        "core/partials/fee_table.html",
        {
            "enrollment": enrollment,
            "terms": terms,
            "fees": fees,
            "total": total,
            "paid_total": paid_total,
            "balance_total": balance_total,
            "total_scholarship": scholarship_total,
            "term_id": term_id,
            "academic_year": academic_year
        },
        request=request
    )

    return JsonResponse({
        "html": html,
        "academic_year_id": academic_year.year_id
    })
@login_required(login_url='login')
def academic_year_manage(request):
    form = AcademicYearForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('academic_year_manage')

    return render(request, 'core/academic_year.html', {
        'form': form
    })
def enrollment_view(request):
    mode = request.POST.get('mode', 'INDIVIDUAL')  # default individual

    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, mode=mode)
        if form.is_valid():
            form.save()
            return redirect('enrollment_success')
    else:
        form = StudentEnrollmentForm(mode=mode)
    return render(request, 'core/enrollment_form.html', {'form': form, 'mode': mode})
def load_districts(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).values(
        'district_id', 'district_name'
    )
    return JsonResponse(list(districts), safe=False)

# List all classes
@login_required(login_url='login')
def school_class_list(request):
    classes = SchoolClass.objects.all()
    return render(request, 'core/school_class_list.html', {'classes': classes})

# Add new class
@login_required(login_url='login')
def school_class_add(request):
    form = SchoolClassForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('school_class_list')
    return render(request, 'core/school_class_form.html', {'form': form})

# Edit existing class
@login_required(login_url='login')
def school_class_edit(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=school_class)
    if form.is_valid():
        form.save()
        return redirect('school_class_list')
    return render(request, 'core/school_class_form.html', {'form': form, 'school_class': school_class})

@login_required
def employee_create(request):

    if request.method == 'POST':

        form = EmployeeForm(request.POST, request.FILES)

        if form.is_valid():

            employee = form.save(commit=False)

            password = form.cleaned_data.get("password")

            # check duplicate employee id
            if User.objects.filter(username=employee.employee_id).exists():
                messages.error(request, "Employee ID already exists")
                return redirect("employee_create")

            # create login user
            user = User.objects.create_user(
                username=employee.employee_id,
                password=password
            )

            # link employee to user
            employee.user = user

            # save employee details
            employee.save()

            messages.success(request, "Employee Created Successfully")

            return redirect("employee_list")

    else:
        form = EmployeeForm()

    return render(request, "core/employee_create.html", {"form": form})
@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})

from .forms import FeeStructureForm

@login_required
def employee_update(request, id):

    employee = Employee.objects.get(id=id)

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)

        if form.is_valid():
            employee = form.save(commit=False)

            password = form.cleaned_data.get("password")

            # update password if entered
            if password:
                employee.user.set_password(password)
                employee.user.save()

            employee.save()

            messages.success(request, "Employee updated successfully")
            return redirect('employee_list')

    else:
        form = EmployeeForm(instance=employee)

    return render(request, "core/employee_create.html", {"form": form})

@login_required
def employee_delete(request, id):

    employee = get_object_or_404(Employee, id=id)

    # delete linked user also
    if employee.user:
        employee.user.delete()

    employee.delete()

    messages.success(request, "Employee deleted successfully")

    return redirect('employee_list')
def fee_structure_list(request):
    fees = FeeStructure.objects.select_related(
        'academic_year',
        'school_class'
    ).all()

    return render(request, 'core/fee_structure.html', {
        'fees': fees
    })


def fee_structure_create(request):

    form = FeeStructureForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('fee_structure_list')

    return render(request, 'core/fee_structure_form.html', {
        'form': form
    })
def add_fee_structure(request):
    form = FeeStructureForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('fee_structure_list')

    return render(request,
                  'core/add_fee_structure.html',
                  {'form': form})
def edit_fee_structure(request, id):
    fee = get_object_or_404(FeeStructure, pk=id)
    form = FeeStructureForm(request.POST or None, instance=fee)

    if form.is_valid():
        form.save()
        return redirect('fee_structure_list')

    return render(request,
                  'core/add_fee_structure.html',
                  {'form': form})

from django.shortcuts import get_object_or_404, redirect

def delete_fee_structure(request, pk):
    fee = get_object_or_404(FeeStructure, pk=pk)

    if request.method == "POST":
        fee.delete()
        return redirect('fee_structure_list')
def fee_category_list(request):
    categories = FeeCategory.objects.all()

    return render(request,
        'core/fee_category.html',
        {'categories': categories}
    )
def fee_category_create(request):

    if request.method == "POST":
        form = FeeCategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('fee_category_list')
    else:
        form = FeeCategoryForm()

    return render(request,
        'core/fee_category_form.html',
        {'form': form}
    )
def fee_category_create(request):

    if request.method == "POST":
        form = FeeCategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('fee_category_list')
    else:
        form = FeeCategoryForm()

    return render(request,
        'core/fee_category_form.html',
        {'form': form}
    )
def fee_category_update(request, pk):

    category = FeeCategory.objects.get(pk=pk)

    if request.method == "POST":
        form = FeeCategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            return redirect('fee_category_list')
    else:
        form = FeeCategoryForm(instance=category)

    return render(request,
        'core/fee_category_form.html',
        {'form': form}
    )
def fee_category_delete(request, pk):

    category = FeeCategory.objects.get(pk=pk)
    category.delete()

    return redirect('fee_category_list')
from django.views.decorators.csrf import csrf_exempt

@user_passes_test(is_employee_or_admin)
def pay_fee(request):

    if request.method == "POST":

        enrollment_id = request.POST.get("enrollment")
        fee_id = request.POST.get("fee")
        amount = request.POST.get("amount")

        FeePayment.objects.create(
            enrollment_id=enrollment_id,
            fee_structure_id=fee_id,
            amount_paid=amount,
            payment_mode="Cash"
        )

        return JsonResponse({"status": "success"})

def save_fee_payment(request):

    if request.method == "POST":

        enrollment_id = request.POST.get('enrollment_id')
        payment_mode = request.POST.get('payment_mode')
        fee_ids = request.POST.getlist('fee_ids')

        enrollment = StudentEnrollment.objects.get(id=enrollment_id)

        for fee_id in fee_ids:

            amount = request.POST.get(f'amount_{fee_id}')

            if amount and float(amount) > 0:

                fee = FeeStructure.objects.get(id=fee_id)

                total_paid = FeePayment.objects.filter(
                    enrollment=enrollment,
                    fee_structure=fee
                ).aggregate(
                    Sum('amount_paid')
                )['amount_paid__sum'] or 0

                balance = fee.amount - total_paid

                if float(amount) <= balance:

                    FeePayment.objects.create(
                        enrollment=enrollment,
                        fee_structure=fee,
                        amount_paid=amount,
                        payment_mode=payment_mode
                    )

        return redirect('fee_payment')

def load_sections(request):
    class_id = request.GET.get('class_id')
    sections = ClassSection.objects.filter(school_class_id=class_id).select_related('section')
    data = [{'id': cs.section.id, 'section_name': cs.section.section_name} for cs in sections]
    return JsonResponse({'sections': data})
from django.contrib.auth.decorators import login_required

# Section List
@login_required(login_url='login')
def section_list(request):
    sections = Section.objects.all()
    return render(request, 'core/section_list.html', {'sections': sections})


# Add Section
@login_required(login_url='login')
def section_add(request):
    form = SectionForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('section_list')
    return render(request, 'core/section_form.html', {'form': form})


# Edit Section
@login_required(login_url='login')
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form = SectionForm(request.POST or None, instance=section)
    if form.is_valid():
        form.save()
        return redirect('section_list')
    return render(request, 'core/section_form.html', {'form': form, 'section': section})

from .models import  Section, ClassSection
from django.contrib.auth.decorators import login_required
from .forms import SchoolClassForm, SectionForm, ClassSectionForm

@login_required
def manage_class_section(request):
    # Determine which form to show
    form_type = request.GET.get('form', 'add_class')

    class_form = SchoolClassForm()
    section_form = SectionForm()
    class_section_form = ClassSectionForm()

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "add_class":
            class_form = SchoolClassForm(request.POST)
            if class_form.is_valid():
                class_form.save()
                return redirect('/class-section/?form=add_class')

        elif action == "add_section":
            section_form = SectionForm(request.POST)
            if section_form.is_valid():
                section_form.save()
                return redirect('/class-section/?form=add_section')

        elif action == "assign_section":
            class_section_form = ClassSectionForm(request.POST)
            if class_section_form.is_valid():
                class_section_form.save()
                return redirect('/class-section/?form=assign_section')

    context = {
        "form_type": form_type,
        "class_form": class_form,
        "section_form": section_form,
        "class_section_form": class_section_form,
    }

    return render(request, "core/class_section_manage.html", context)

from django.contrib import messages

@login_required
@user_passes_test(is_employee_or_admin)
def fee_payment(request):

    years = AcademicYear.objects.all().order_by('-start_date')
    classes = SchoolClass.objects.all().order_by('class_name')

    return render(
        request,
        "core/fee_payment.html",
        {
            "years": years,
            "classes": classes
        }
    )

from decimal import Decimal
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum
import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def process_fee_payment(request):
    if request.method != "POST":
        return redirect("fee_payment")

    enrollment_id = request.POST.get("enrollment_id")
    term_id = request.POST.get("term_id")
    academic_year_id = request.POST.get("academic_year_id")

    cash_amount = Decimal(request.POST.get("cash_amount") or 0)
    upi_amount = Decimal(request.POST.get("upi_amount") or 0)
    card_amount = Decimal(request.POST.get("card_amount") or 0)
    total_amount_paid = cash_amount + upi_amount + card_amount

    if total_amount_paid <= 0:
        return JsonResponse({"success": False, "message": "Enter at least one payment amount"})

    current_enrollment = get_object_or_404(StudentEnrollment, id=enrollment_id)
    term = get_object_or_404(Term, id=term_id)
    academic_year = get_object_or_404(AcademicYear, year_id=academic_year_id)

    old_enrollment = StudentEnrollment.objects.filter(
        student=current_enrollment.student,
        academic_year=academic_year
    ).first()

    if not old_enrollment:
        return JsonResponse({"success": False, "message": "No enrollment found for selected academic year"})

    # Prevent duplicate payment within 2 seconds
    last_payment = FeePayment.objects.filter(
        enrollment=old_enrollment
    ).order_by("-payment_date").first()

    if last_payment and (timezone.now() - last_payment.payment_date).seconds < 2:
        return JsonResponse({"success": False, "message": "Duplicate payment blocked"})

    # Keep QuerySet for aggregation
    fee_categories_qs = FeeStructure.objects.filter(
        academic_year=academic_year,
        school_class=old_enrollment.class_section.school_class,
        term=term
    ).order_by("id")

    if not fee_categories_qs.exists():
        return JsonResponse({"success": False, "message": "No fee categories found"})

    # Convert to list only for locking and looping
    fee_categories = list(fee_categories_qs.select_for_update())

    # Scholarship totals
    scholarship_total = ScholarshipPosting.objects.filter(
        student=old_enrollment.student,
        academic_year=academic_year
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Already used scholarship
    scholarship_used = FeePayment.objects.filter(
        enrollment=old_enrollment,
        payment_mode="Scholarship"
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

    remaining_scholarship = max(scholarship_total - (scholarship_used or 0), 0)

    # Term balance calculation
    term_balance = sum(
        max(fee.amount - (FeePayment.objects.filter(enrollment=old_enrollment, fee_structure=fee)
                          .aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0), 0)
        for fee in fee_categories
    )

    if scholarship_used > 0:
        # Already used once → don't apply again
        scholarship_to_apply = Decimal("0")
    else:
        # First time → apply full scholarship (or up to term balance)
        scholarship_to_apply = min(term_balance, remaining_scholarship)

    if term_balance <= 0:
        return JsonResponse({"success": False, "message": "All fees already paid"})

    if total_amount_paid > term_balance:
        return JsonResponse({"success": False, "message": f"Payment exceeds balance ₹{term_balance}"})

    receipt_no = "RCPT-" + uuid.uuid4().hex[:8].upper()
    payment_modes = [("Cash", cash_amount), ("UPI", upi_amount), ("Online", card_amount)]

    with transaction.atomic():

        fee_categories = list(fee_categories_qs.select_for_update())
        fee_balances = {}
        for fee in fee_categories:
            paid = FeePayment.objects.filter(
                enrollment=old_enrollment,
                fee_structure=fee
            ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or Decimal("0")
            fee_balances[fee.id] = max(fee.amount - paid, 0)
        remaining = scholarship_to_apply
        for fee in fee_categories:
            if remaining <= 0:
                break
            balance = fee_balances[fee.id]
            if balance <= 0:
                continue
            use_amount = min(balance, remaining)
            FeePayment.objects.create(
                enrollment=old_enrollment,
                fee_structure=fee,
                amount_paid=use_amount,
                payment_mode="Scholarship",
                receipt_no=receipt_no
            )
            fee_balances[fee.id] -= use_amount
            remaining -= use_amount
        for mode, amount in payment_modes:
            remaining = amount
            if remaining <= 0:
                continue
            for fee in fee_categories:
                if remaining <= 0:
                    break
                balance = fee_balances[fee.id]
                if balance <= 0:
                    continue
                pay_amount = min(balance, remaining)
                FeePayment.objects.create(
                    enrollment=old_enrollment,
                    fee_structure=fee,
                    amount_paid=pay_amount,
                    payment_mode=mode,
                    receipt_no=receipt_no
                )
                fee_balances[fee.id] -= pay_amount
                remaining -= pay_amount
    total = fee_categories_qs.aggregate(Sum("amount"))["amount__sum"] or Decimal("0")
    paid_total = FeePayment.objects.filter(enrollment=old_enrollment, fee_structure__in=fee_categories).aggregate(
        Sum("amount_paid")
    )["amount_paid__sum"] or Decimal("0")
    balance_total = total - paid_total

    return JsonResponse({
        "success": True,
        "message": "Payment successful",
        "receipt_no": receipt_no,
        "total": str(total),
        "paid_total": str(paid_total),
        "balance_total": str(balance_total),
        "scholarship_used": str(scholarship_to_apply),
        "remaining_scholarship": str(remaining_scholarship - scholarship_to_apply),
    })

def reports_dashboard(request):
    return render(request, 'core/reports_dashboard.html')

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from collections import defaultdict

def fee_receipt(request):
    receipt_no = request.GET.get("payment_id")

    if not receipt_no:
        return HttpResponse("Invalid receipt")

    # Get payments of this receipt
    payments = FeePayment.objects.filter(
        receipt_no=receipt_no
    ).select_related(
        "fee_structure__category",
        "enrollment",
        "fee_structure__term"
    ).order_by("fee_structure__id")

    if not payments.exists():
        return HttpResponse("Receipt not found")

    payment = payments.first()
    enrollment = payment.enrollment
    term = payment.fee_structure.term

    # --- All fee structures for this student in this term ---
    fee_structures = FeeStructure.objects.filter(
        academic_year=enrollment.academic_year,
        school_class=enrollment.class_section.school_class,
        term=term
    ).select_related('category')

    # Build category-wise totals
    category_totals_dict = defaultdict(lambda: {"total": 0, "paid": 0, "balance": 0})

    for fs in fee_structures:
        category_name = fs.category.category_name
        total_paid_for_fee = FeePayment.objects.filter(
            enrollment=enrollment,
            fee_structure=fs
        ).aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0

        category_totals_dict[category_name]["total"] += fs.amount
        category_totals_dict[category_name]["paid"] += total_paid_for_fee
        category_totals_dict[category_name]["balance"] = category_totals_dict[category_name]["total"] - category_totals_dict[category_name]["paid"]

    category_totals = [
        {
            "category_name": name,
            "total": vals["total"],
            "paid": vals["paid"],
            "balance": vals["balance"]
        }
        for name, vals in category_totals_dict.items()
    ]

    # Total fee for the term (all categories)
    total_fee = sum(c["total"] for c in category_totals)
    total_paid_term = sum(c["paid"] for c in category_totals)
    total_balance_term = total_fee - total_paid_term

    # Payment mode totals for this receipt only
    mode_totals = payments.values("payment_mode").annotate(total_amount=Sum("amount_paid"))

    context = {
        "enrollment": enrollment,
        "receipt_no": receipt_no,
        "payment_date": payment.payment_date,
        "category_totals": category_totals,
        "mode_totals": mode_totals,
        "total_fee": total_fee,
        "total_paid_receipt": sum(fs.amount_paid for fs in payments),
        "total_term_balance": total_balance_term,
        "term": term
    }

    return render(request, "core/receipt.html", context)

from .models import StudentEnrollment, FeeStructure, FeePayment, SchoolClass, Term, AcademicYear


def fees_pending_report(request):

    classes = SchoolClass.objects.all()
    terms = Term.objects.all()
    years = AcademicYear.objects.all()

    class_id = request.GET.get('class')
    term_id = request.GET.get('term')
    year_id = request.GET.get('academic_year')

    enrollments = StudentEnrollment.objects.select_related(
        'student',
        'class_section__school_class',
        'class_section__section',
        'academic_year'
    )

    if class_id:
        enrollments = enrollments.filter(class_section__school_class_id=class_id)

    if year_id:
        enrollments = enrollments.filter(academic_year_id=year_id)

    report_data = []
    total_pending = 0

    for e in enrollments:

        fee_structures = FeeStructure.objects.filter(
            school_class=e.class_section.school_class
        )

        if year_id:
            fee_structures = fee_structures.filter(academic_year_id=year_id)
        else:
            fee_structures = fee_structures.filter(academic_year=e.academic_year)

        if term_id:
            fee_structures = fee_structures.filter(term_id=term_id)

        for fee in fee_structures:

            paid = FeePayment.objects.filter(
                enrollment=e,
                fee_structure=fee
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

            balance = fee.amount - paid

            if balance > 0:

                total_pending += balance

                report_data.append({
                    'student': e.student.student_name,
                    'class': e.class_section.school_class.class_name,
                    'section': e.class_section.section.section_name,
                    'academic_year': e.academic_year.year_name,
                    'term': fee.term.term_name,
                    'category': fee.category.category_name,
                    'total_fee': fee.amount,
                    'paid': paid,
                    'pending': balance
                })

    context = {
        'report_data': report_data,
        'classes': classes,
        'terms': terms,
        'years': years,
        'selected_class': class_id,
        'selected_term': term_id,
        'selected_year': year_id,
        'total_pending': total_pending
    }

    return render(request, 'core/fees_pending_report.html', context)

def fees_payment_report(request):
    classes = SchoolClass.objects.all()
    terms = Term.objects.all()
    years = AcademicYear.objects.all()

    # Add payment modes dynamically if needed
    PAYMODES = FeePayment.objects.values_list('payment_mode', flat=True).distinct().order_by('payment_mode')

    class_id = request.GET.get('class')
    term_id = request.GET.get('term')
    year_id = request.GET.get('academic_year')
    paymode = request.GET.get('paymode')  # new

    payments = FeePayment.objects.select_related(
        'enrollment__student',
        'enrollment__class_section__school_class',
        'enrollment__class_section__section',
        'enrollment__academic_year',
        'fee_structure__term',
        'fee_structure__category'
    )

    if class_id:
        payments = payments.filter(enrollment__class_section__school_class_id=class_id)
    if term_id:
        payments = payments.filter(fee_structure__term_id=term_id)
    if year_id:
        payments = payments.filter(enrollment__academic_year_id=year_id)
    if paymode:
        payments = payments.filter(payment_mode=paymode)

    total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0

    context = {
        'payments': payments,
        'classes': classes,
        'terms': terms,
        'years': years,
        'paymodes': PAYMODES,         # pass paymodes to template
        'selected_class': class_id,
        'selected_term': term_id,
        'selected_year': year_id,
        'selected_paymode': paymode,   # current selection
        'total_paid': total_paid,
    }
    return render(request, 'core/fees_payment_report.html', context)



from django.db.models import Sum
from datetime import datetime

@login_required
def fees_payment_on_day(request):
    date_str = request.GET.get('payment_date')
    payment_mode = request.GET.get('payment_mode')  # new filter
    payments = FeePayment.objects.none()  # start empty

    if date_str:
        try:
            payment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            payments = FeePayment.objects.filter(payment_date__date=payment_date).select_related(
                'enrollment__student',
                'enrollment__class_section__school_class',
                'enrollment__class_section__section',
                'enrollment__academic_year',
                'fee_structure__category',
                'fee_structure__term'
            )

            if payment_mode and payment_mode != "all":
                payments = payments.filter(payment_mode=payment_mode)

        except ValueError:
            pass  # invalid date, keep payments empty

    total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0

    # Get unique payment modes for dropdown
    payment_modes = FeePayment.objects.values_list('payment_mode', flat=True) \
        .distinct() \
        .order_by('payment_mode')

    context = {
        'payments': payments,
        'payment_date': date_str,
        'total_paid': total_paid,
        'payment_modes': payment_modes,
        'selected_mode': payment_mode,
    }
    return render(request, 'core/fees_payment_on_day.html', context)
from datetime import datetime
from django.db.models import Sum
from datetime import datetime


def fees_payment_between_dates(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_mode = request.GET.get('payment_mode')  # new filter

    payments = FeePayment.objects.none()  # start empty

    # Get all unique payment modes in DB (for dropdown)
    all_modes = FeePayment.objects.values_list('payment_mode', flat=True)
    payment_modes = sorted(set([m.strip() for m in all_modes if m]))

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            payments = FeePayment.objects.filter(payment_date__date__range=[start_date, end_date])

            # Apply payment mode filter if selected
            if selected_mode:
                payments = payments.filter(payment_mode=selected_mode)

            payments = payments.select_related(
                'enrollment__student',
                'enrollment__class_section__school_class',
                'enrollment__class_section__section',
                'enrollment__academic_year',
                'fee_structure__category',
                'fee_structure__term'
            ).order_by('payment_date')

        except ValueError:
            payments = FeePayment.objects.none()

    # Calculate total
    total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0

    context = {
        'payments': payments,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_paid': total_paid,
        'payment_modes': payment_modes,
        'selected_mode': selected_mode,
    }
    return render(request, 'core/fees_payment_between_dates.html', context)
from .forms import ScholarshipForm
from .models import Scholarship
from django.contrib.auth.decorators import login_required

@login_required
def scholarship_manage_view(request):
    # Handle form submission
    form = ScholarshipForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('scholarship_manage')  # reload same page

    # List of scholarships
    scholarships = Scholarship.objects.all()

    context = {
        'form': form,
        'scholarships': scholarships,
        'page_title': 'Manage Scholarships'
    }
    return render(request, 'core/scholarship_manage.html', context)
# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ScholarshipPostingForm

@login_required
def scholarship_posting_view(request):
    if request.method == 'POST':
        form = ScholarshipPostingForm(request.POST)
        if form.is_valid():
            posting = form.save(commit=False)
            # assign actual student object from form.cleaned_data
            posting.student = form.cleaned_data['student_no']
            posting.save()
            messages.success(request, "Scholarship posted successfully!")
            return redirect('scholarship_posting')
    else:
        form = ScholarshipPostingForm()

    # List all posted scholarships
    scholarships = ScholarshipPosting.objects.select_related(
        'student', 'scholarship', 'academic_year'
    ).order_by('-id')

    context = {
        'form': form,
        'scholarships': scholarships
    }
    return render(request, 'core/scholarship_posting.html', context)
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import ScholarshipPosting, AcademicYear, ClassSection

@login_required
def scholarship_report(request):

    academic_year_id = request.GET.get("academic_year")
    class_id = request.GET.get("class")

    scholarships = ScholarshipPosting.objects.select_related(
        'student', 'scholarship', 'academic_year'
    )


    if academic_year_id:
        scholarships = scholarships.filter(academic_year__year_id=academic_year_id)

    if class_id:
        scholarships = scholarships.filter(student__studentenrollment__class_section__school_class__id=class_id)

    # Totals
    total_scholarship = scholarships.aggregate(Sum("amount"))["amount__sum"] or 0

    # Dropdown data
    academic_years = AcademicYear.objects.all()
    classes = ClassSection.objects.select_related("school_class") \
        .values("school_class__id", "school_class__class_name") \
        .distinct()

    context = {
        "scholarships": scholarships,
        "total_scholarship": total_scholarship,
        "academic_years": academic_years,
        "classes": classes
    }

    return render(request, "core/scholarship_report.html", context)
from django.shortcuts import render
from .models import StudentEnrollment, SchoolClass, AcademicYear

def new_admission_report(request):
    classes = SchoolClass.objects.all()
    years = AcademicYear.objects.all()

    class_id = request.GET.get('class')
    year_id = request.GET.get('academic_year')

    # Filter enrollments for NEW admissions only
    enrollments = StudentEnrollment.objects.select_related(
        'student',
        'class_section__school_class',
        'class_section__section',
        'academic_year'
    ).filter(student__admission_type='NEW')  # <-- filter new admissions

    if class_id:
        enrollments = enrollments.filter(class_section__school_class_id=class_id)
    if year_id:
        enrollments = enrollments.filter(academic_year_id=year_id)

    context = {
        'enrollments': enrollments,
        'classes': classes,
        'years': years,
        'selected_class': class_id,
        'selected_year': year_id,
        'total_new': enrollments.count()  # total count of new admissions
    }

    return render(request, 'core/new_admission_report.html', context)