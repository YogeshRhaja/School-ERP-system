from django.urls import path
from . import views
from .views import scholarship_posting_view


urlpatterns = [

    # Authentication
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # Students
    path('students/', views.students_list, name='students_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('enroll/', views.enroll_student, name='enroll_student'),

    # Academic Year
    path('academic-year/', views.academic_year_manage,
         name='academic_year_manage'),

    # AJAX
    path('ajax/load-districts/',
         views.load_districts,
         name='ajax_load_districts'),
path('scholarships/create/', views.scholarship_manage_view, name='scholarship_manage'),

path('scholarships/posting/', views.scholarship_posting_view, name='scholarship_posting'),
path('reports/scholarship/', views.scholarship_report, name='scholarship_report'),
path('reports/new-admissions/', views.new_admission_report, name='new_admission_report'),
path('enrollment/edit/<int:id>/', views.edit_enrollment, name='edit_enrollment'),
# =========================
# Fee Management
# =========================

# =========================
# Fee Management
# =========================

path('fee-payment/', views.fee_payment, name='fee_payment'),
path('process-fee-payment/', views.process_fee_payment, name='process_fee_payment'),
path("core/receipt/", views.fee_receipt, name="fee_receipt"),

    path('reports/', views.reports_dashboard, name='reports_dashboard'),

    path('reports/fees-pending/', views.fees_pending_report, name='fees_pending_report'),

    path('reports/fees-payment/', views.fees_payment_report, name='fees_payment_report'),

    path('reports/fees-payment-day/', views.fees_payment_on_day, name='fees_payment_on_day'),

    path('reports/fees-payment-range/', views.fees_payment_between_dates, name='fees_payment_between_dates'),



path('ajax/load-students/', views.load_students, name='load_students'),
path('ajax/load-fees/', views.load_fees, name='load_fees'),
path('ajax/load-terms/', views.load_terms, name='load_terms'),
# =========================
# AJAX
# =========================

path(
    'ajax/load-students/',
    views.load_students,
    name='load_students'
),

path(
    'ajax/load-fees/',
    views.load_fees,
    name='load_fees'
),
path('ajax/load-terms/', views.load_terms, name='load_terms'),
    # School Classes
    path('school-classes/', views.school_class_list,
         name='school_class_list'),
    path('school-classes/add/', views.school_class_add,
         name='school_class_add'),
    path('school-classes/edit/<int:pk>/',
         views.school_class_edit,
         name='school_class_edit'),

    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/update/<int:id>/', views.employee_update, name='employee_update'),
    path('employees/delete/<int:id>/', views.employee_delete, name='employee_delete'),

    # =========================
    # Fee Category (CRUD)
    # =========================
    path('fee-category/',
         views.fee_category_list,
         name='fee_category_list'),

    path('fee-category/add/',
         views.fee_category_create,
         name='fee_category_create'),

    path('fee-category/edit/<int:pk>/',
         views.fee_category_update,
         name='fee_category_update'),

    path('fee-category/delete/<int:pk>/',
         views.fee_category_delete,
         name='fee_category_delete'),

    # =========================
    # Fee Structure (CRUD)
    # =========================
    path('fee-structure/',
         views.fee_structure_list,
         name='fee_structure_list'),

    path('fee-structure/add/',
         views.add_fee_structure,
         name='add_fee_structure'),

    path('fee-structure/edit/<int:id>/',
         views.edit_fee_structure,
         name='edit_fee_structure'),

    path('fee-structure/delete/<int:pk>/', views.delete_fee_structure, name='delete_fee_structure'),
    # Payments

path('load-districts/', views.load_districts, name='load_districts'),
path('ajax/load_sections/', views.load_sections, name='load_sections'),
path('sections/', views.section_list, name='section_list'),
path('sections/add/', views.section_add, name='section_add'),
path('sections/edit/<int:pk>/', views.section_edit, name='section_edit'),
path('class-section/', views.manage_class_section, name='manage_class_section'),


]