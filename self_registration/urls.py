from django.urls import path, include

from . import views

urlpatterns = [

    # Deliveries or Guest
    path('', views.option_page, name='option-page'),

    # Search Registration
    path('search-mobile/', views.search_registration, name='search-mobile'),
    path('result/<str:mobile>/', views.search_result, name='search-result'),

    # CHECK IN
    path('check-in/', views.check_in, name='check-in'),
    path('check-in/details/', views.details_checkin, name="details-checkin"),

    # CHECK OUT
    path('check-out/', views.checkout, name='check-out'),

    # Validate NRIC
    path('validate-nric/', views.validate_nric, name='validate-nric'),

    # Face Verification
    path('validate-photo/', views.validate_photo, name='validate-photo'),

    path('fra-photo-validation/', views.fra_validation, name='fra_photo_validation'),

    # Visitor Registration Path
    path('visitor/', include(([
        path('mobile/', views.visitor_reg_mobile, name='visitors_reg_mobile'),
        path('', views.visitor_reg, name='visitors_reg'),
        path('<str:refs_tenant>/', views.visitor_reg, name='visitors_reg'),
        
        # path('store/', views.visitor_reg_store, name='visitor-store')
        
    ], 'self_registration'), namespace='visitors')),

    path('staff/', include(([
        path('', views.staff_reg, name='staffs_reg'),
        path('<str:refs_tenant>/', views.staff_reg, name='staffs_reg'),
        
    ], 'self_registration'), namespace='staffs')),
]