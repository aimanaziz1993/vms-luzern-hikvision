from django.urls import path, include

from . import views


urlpatterns = [

    # CHECK IN
    path('check-in/', views.check_in, name='check-in'),
    path('check-in/details/', views.details_checkin, name="details-checkin"),

    # Validate NRIC
    path('validate-nric/', views.validate_nric, name='validate-nric'),

    # Visitor Registration Path
    path('visitor/', include(([
        path('', views.visitor_reg, name='visitors_reg'),
        path('<str:refs_tenant>/', views.visitor_reg, name='visitors_reg'),
        # path('store/', views.visitor_reg_store, name='visitor-store')
        
    ], 'self_registration'), namespace='visitors')),

    path('staff/', include(([
        path('', views.staff_reg, name='staffs_reg'),
        path('<str:refs_tenant>/', views.staff_reg, name='staffs_reg'),
        
    ], 'self_registration'), namespace='staffs')),
]