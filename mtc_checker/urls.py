from django.urls import path
from . import views

app_name = 'mtc_checker'

urlpatterns = [
    path('login/', views.student_login_view, name='student_login'),

    # URL for displaying test results (requires student_id)
    path('results/<uuid:student_id>/', views.test_results_view, name='test_results'),

    # Remove or comment out this line to avoid conflicting URL
    # path('all_results/', views.test_results_view, name='all_test_results'),  # REMOVE or COMMENT OUT

    path('', views.student_login_or_select_view, name='student_select'),
    path('test/<uuid:student_id>/', views.test_interface_view, name='test_interface'),
    path('test/submit/<uuid:student_id>/', views.submit_test_view, name='submit_test'),
    path('test/complete/<uuid:student_id>/<uuid:attempt_id>/', views.test_complete_view, name='test_complete'),
    path('results/<uuid:student_id>/', views.student_results_view, name='student_results'),  # <--- THIS LINE IS CRUCIAL

    # Remove or comment out this line to avoid conflicting URL
    # path('results/', views.test_results_view, name='test_results'),  # REMOVE or COMMENT OUT

    # Custom Admin URLs for Student Management
    path('manage/students/', views.student_admin_dashboard_view, name='student_admin_dashboard'),
    path('manage/students/add/', views.student_add_view, name='student_add'),
    path('manage/students/edit/<uuid:student_id>/', views.student_edit_view, name='student_edit'),
    path('manage/students/delete/<uuid:student_id>/', views.student_delete_view, name='student_delete'),
    path('manage/students/upload-csv/', views.student_upload_csv_view, name='student_upload_csv'),
]