from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MenuView, OrderView, StaffOrderViewSet, AdminMenuViewSet, AdminTableViewSet, PaymentView, StaffOrderItemManagementView, SummaryReportView

router = DefaultRouter()
router.register(r'staff/orders', StaffOrderViewSet, basename='staff-order')
router.register(r'admin/menu', AdminMenuViewSet, basename='admin-menu')
router.register(r'admin/tables', AdminTableViewSet, basename='admin-table')

urlpatterns = [
    path('tables/<str:table_number>/menu/', MenuView.as_view(), name='menu-view'),
    path('tables/<str:table_number>/order/', OrderView.as_view(), name='order-view'),
    path('permissions/', UserViewSet.as_view({'get': 'userPermissions'}), name='permission-view'),
    path('orders/<int:pk>/pay/', PaymentView.as_view(), name='order-payment'),
    path('staff/order-items/<int:pk>/', StaffOrderItemManagementView.as_view(), name='staff-order-item-management'),
    path('reports/summary/', SummaryReportView.as_view(), name='summary-report'),
    path('', include(router.urls)),
]