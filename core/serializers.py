from rest_framework import serializers
from .models import Table, MenuItem, Order, OrderItem

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'is_available']

class CustomerMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price']

class AdminMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'is_available']

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = CustomerMenuItemSerializer(read_only=True)
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source='menu_item', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_id', 'quantity', 'price']
        read_only_fields = ['price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'table_number', 'status', 'is_paid', 'created_at', 'items', 'total_price']
        read_only_fields = ['status', 'is_paid', 'created_at']

class StaffOrderItemUpdateSerializer(serializers.ModelSerializer):
    # 将关联的字段设为只读，以提供上下文信息，但防止修改
    menu_item = CustomerMenuItemSerializer(read_only=True)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        # 字段列表中只包含 id, menu_item, price (只读) 和 quantity (可写)
        fields = ['id', 'menu_item', 'price', 'quantity']