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
        """
        查看当前餐桌的订单。
        如果餐桌或未支付的订单不存在，则返回404。
        """
        try:
            table_number = self.kwargs.get('table_number')
            # 步骤1: 严格使用 get() 查找餐桌，找不到就抛出异常
            table = Table.objects.get(table_number=table_number)
            # 步骤2: 同样严格使用 get() 查找未支付的订单
            order = Order.objects.get(table=table, is_paid=False)

            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            # 捕获 Table.DoesNotExist 和 Order.DoesNotExist 异常
            return Response({"info": "指定的餐桌没有未支付的订单。"}, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        """
        向订单中添加菜品（下单或加单）。
        餐桌必须预先存在，但订单可以是新创建的。
        """
        try:
            table_number = self.kwargs.get('table_number')
            # 步骤1: 确保餐桌是真实存在的
            table = Table.objects.get(table_number=table_number)
        except Table.DoesNotExist:
            return Response({"error": f"餐桌 '{table_number}' 不存在，无法下单。"}, status=status.HTTP_404_NOT_FOUND)

        # 步骤2: 餐桌存在的前提下，获取或创建（get_or_create）一个未支付的订单
        # 查找该餐桌上任何状态不是 'completed' 的订单
        try:
            order = Order.objects.exclude(status='completed').get(table=table)
            created = False # 订单是找到的，不是新创建的
        except Order.DoesNotExist:
            # 如果不存在任何未完成的订单，则创建一个新的
            order = Order.objects.create(table=table, status='pending')
            created = True # 订单是新创建的

            # 如果订单是新创建的，则立即将餐桌设为不可用
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
        """
        处理顾客的结账请求。
        餐桌和未支付的订单必须都存在。
        """
        try:
            table_number = self.kwargs.get('table_number')
            table = Table.objects.get(table_number=table_number)
            order = Order.objects.get(table=table, is_paid=False)

            # 执行结账逻辑
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

    # def _has_active_orders(self, table_instance):
    #     """
    #     检查餐桌是否有未支付或未取消的订单。
    #     将 `order_set` 修改为 `orders`。
    #     """
    #     return table_instance.orders.filter(is_paid=False).exclude(status__in=['cancelled', 'completed']).exists()
        
    # def perform_destroy(self, instance):
    #     if self._has_active_orders(instance):
    #         return Response(
    #             {"detail": "此餐桌有未支付或未取消的订单，不能被删除。"},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #     instance.delete()

    # def update(self, request, *args, **kwargs):
    #     """
    #     如果餐桌有未支付或未取消的订单，则不能修改其状态为 '可用'。
    #     """
    #     instance = self.get_object()
    #     new_status = request.data.get('status')
        
    #     if new_status == 'available' and self._has_active_orders(instance):
    #         return Response(
    #             {"detail": "此餐桌有未支付或未取消的订单，不能被修改为 '可用'。"},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
        
    #     return super().update(request, *args, **kwargs)

class PaymentView(generics.GenericAPIView):
    """
    处理特定订单支付的API视图。
    """
    permission_classes = [AllowAny] # 允许任何人访问支付接口

    def post(self, request, pk, format=None):
        """
        处理支付请求。'pk' 是订单的ID。
        """
        try:
            # 步骤1: 根据URL传入的pk（订单ID）获取订单
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "订单不存在。"}, status=status.HTTP_404_NOT_FOUND)

        # 步骤2: 验证订单状态，防止重复支付
        if order.is_paid:
            return Response({"error": "该订单已经支付，请勿重复操作。"}, status=status.HTTP_400_BAD_REQUEST)

        #
        # --- 模拟支付网关集成 ---
        # 在真实的应用中，这里会调用第三方支付SDK，
        # 处理支付逻辑，并等待支付成功的回调。
        #
        # payment_gateway.charge(order.total_price, token=request.data.get('payment_token'))
        #
        # 我们在这里直接模拟支付成功。
        #

        # 步骤3: 更新订单状态
        order.is_paid = True
        order.status = 'completed'
        order.save()

        # 支付完成后，获取订单关联的餐桌
        table = order.table
        # 将餐桌状态更新为可用
        table.is_available = True
        table.save()

        # 步骤4: 返回成功响应和更新后的订单数据
        serializer = OrderSerializer(order)
        return Response({
            "message": "支付成功！",
            "order": serializer.data
        }, status=status.HTTP_200_OK)

class StaffOrderItemManagementView(generics.RetrieveUpdateDestroyAPIView):
    """
    允许授权员工查看、更新（修改数量）和删除单个订单项。
    - PATCH: 用于修改数量
    - DELETE: 用于删除订单项
    """
    queryset = OrderItem.objects.all()
    serializer_class = StaffOrderItemUpdateSerializer
    permission_classes = [DjangoModelPermissions] # 使用Django模型权限进行精细化控制
