from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, AllowAny
from .models import Table, MenuItem, Order, OrderItem
from .serializers import (
    CustomerMenuItemSerializer, AdminMenuItemSerializer, TableSerializer,
    OrderSerializer, StaffOrderItemUpdateSerializer
)

class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def userPermissions(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "permissions": list(user.get_all_permissions()),
            "groups": [g.name for g in user.groups.all()]
        })

class MenuView(generics.ListAPIView):
    serializer_class = CustomerMenuItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MenuItem.objects.filter(is_available=True)

class OrderView(generics.GenericAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            table_number = self.kwargs.get('table_number')
            table = Table.objects.get(table_number=table_number)
            order = Order.objects.get(table=table, is_paid=False)

            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({"info": "指定的餐桌没有未支付的订单。"}, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        try:
            table_number = self.kwargs.get('table_number')
            table = Table.objects.get(table_number=table_number)
        except Table.DoesNotExist:
            return Response({"error": f"餐桌 '{table_number}' 不存在，无法下单。"}, status=status.HTTP_404_NOT_FOUND)

        try:
            order = Order.objects.exclude(status='completed').get(table=table)
            created = False
        except Order.DoesNotExist:
            order = Order.objects.create(table=table, status='pending')
            created = True

            if created:
                table.is_available = False
                table.save()

        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"error": "未提供菜品信息"}, status=status.HTTP_400_BAD_REQUEST)

        for item_data in items_data:
            menu_item_id = item_data.get('menu_item_id')
            quantity = item_data.get('quantity', 1)

            try:
                menu_item = MenuItem.objects.get(id=menu_item_id, is_available=True)
                order_item, item_created = OrderItem.objects.get_or_create(
                    order=order,
                    menu_item=menu_item,
                    defaults={'quantity': quantity}
                )
                if not item_created:
                    order_item.quantity += quantity
                    order_item.save()

            except MenuItem.DoesNotExist:
                return Response(
                    {"error": f"ID为 {menu_item_id} 的菜品不存在或不可售。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        try:
            table_number = self.kwargs.get('table_number')
            table = Table.objects.get(table_number=table_number)
            order = Order.objects.get(table=table, is_paid=False)

            order.is_paid = True
            order.status = 'completed'
            order.save()

            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({"error": "指定的餐桌或需要结账的订单不存在。"}, status=status.HTTP_404_NOT_FOUND)

class StaffOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):

        order = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': '未提供状态信息'}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()
        return Response(self.get_serializer(order).data)

class AdminMenuViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = AdminMenuItemSerializer
    permission_classes = [DjangoModelPermissions]

class AdminTableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [DjangoModelPermissions]

    lookup_field = 'table_number'

class PaymentView(generics.GenericAPIView):

    permission_classes = [AllowAny]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def post(self, request, pk, format=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "订单不存在。"}, status=status.HTTP_404_NOT_FOUND)

        if order.is_paid:
            return Response({"error": "该订单已经支付，请勿重复操作。"}, status=status.HTTP_400_BAD_REQUEST)

        order.is_paid = True
        order.status = 'completed'
        order.save()

        table = order.table
        table.is_available = True
        table.save()

        serializer = OrderSerializer(order)
        return Response({
            "message": "支付成功！",
            "order": serializer.data
        }, status=status.HTTP_200_OK)

class StaffOrderItemManagementView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = StaffOrderItemUpdateSerializer
    permission_classes = [DjangoModelPermissions]
