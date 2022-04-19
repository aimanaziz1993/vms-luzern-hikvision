from django.urls import include, path

from .views import administrator, dashboard, tenant

urlpatterns = [

    path('', dashboard.home, name='home'),

    path('superuser/', include(([
        path('', dashboard.home, name='home_view'),
        path('user-list/', dashboard.UserList.as_view(), name='user-list'),

    ], 'accounts'), namespace='superusers')),

    path('administrator/', include(([
        path('', administrator.home, name='home_view'),

        # BUILDING
        # path('building-list', administrator.BuildingList.as_view(), name='building-list'),
        path('building/create/', administrator.BuildingCreate.as_view(), name='building-create'),
        # path('building/<int:pk>/edit'),
        # path('building/<int:pk>/delete', ),

        # FLOOR
        path('floor/create/', administrator.FloorCreate.as_view(), name='floor-create'),


        # TENANT
        path('tenant-list/', administrator.TenantList.as_view(), name='tenant-list'),
        path('tenant/create/', administrator.TenantCreate.as_view(), name='tenant-create'),
        path('tenant/<int:pk>/detail', administrator.TenantDetail.as_view(), name='tenant-detail'),
        path('delete/<int:pk>/', administrator.TenantDelete.as_view(), name='tenant-delete'),

        # DEVICE
        path('device-list/', administrator.DeviceList.as_view(), name='device-list'),
        path('device/<int:pk>/detail', administrator.DeviceDetail.as_view(), name='device-detail'),
        path('device/create/', administrator.DeviceCreate.as_view(), name='device-create'),
        path('device/<int:pk>/update', administrator.DeviceUpdate.as_view(), name='device-update'),
        path('device/<int:pk>/delete', administrator.DeviceDelete.as_view(), name='device-delete'),

        path('change-security/', administrator.change_security, name='change-security'),

    ], 'accounts'), namespace='administrators')),


    path('tenant/', include(([
        # HOME
        path('', tenant.home, name='home_view'),
        path('generate-code/', tenant.generate_code, name='tenant-generate_code'),

        path('profile/<int:pk>/update', tenant.TenantProfileUpdate.as_view(), name='tenant-update'),

        # VISITOR
        path('visitor-list/', tenant.TenantVisitorList.as_view(), name='tenant-visitor-list'),
        path('visitor-list/<str:status>/', tenant.TenantVisitorListFilter.as_view(), name='visitor-update-list'),
        path('visitor/<int:pk>/detail', tenant.TenantVisitorDetail.as_view(), name='tenant-visitor-detail'),
        path('visitor/<int:pk>/delete', tenant.TenantVisitorDelete.as_view(), name='tenant-visitor-delete'),
        path('visitor/<int:pk>/approval/', tenant.visitor_approval, name='tenant-visitor-approval'),


        # STAFF
        path('staff-list/', tenant.TenantStaffList.as_view(), name='tenant-staff-list'),
        path('staff-list/<str:status>/', tenant.TenantStaffListFilter.as_view(), name='staff-update-list'),
        path('staff/<int:pk>/detail', tenant.TenantStaffDetail.as_view(), name='tenant-staff-detail'),
        path('staff/<int:pk>/delete', tenant.TenantStaffDelete.as_view(), name='tenant-staff-delete'),
        path('staff/<int:pk>/approval/', tenant.staff_approval, name='tenant-staff-approval'),

    ], 'accounts'), namespace='tenants'))
]