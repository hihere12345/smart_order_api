from django.db import models
from django.contrib.auth.models import User

class Table(models.Model):
    table_number = models.CharField(max_length=10, unique=True, help_text="唯一的餐桌号")
    is_available = models.BooleanField(default=True, help_text="餐桌当前是否可用?")

    def __str__(self):
        return f"Table {self.table_number}"

class MenuItem(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="菜品名称")
    description = models.TextField(blank=True, help_text="菜品的详细描述")
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="菜品价格")
    is_available = models.BooleanField(default=True, help_text="菜品当前是否可售?")

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('preparing', '准备中'),
        ('served', '已上菜'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders', help_text="订单所属的餐桌")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="订单状态")
    is_paid = models.BooleanField(default=False, help_text="订单是否已支付")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} for {self.table}"

    @property
    def total_price(self):
        """计算并返回订单中所有菜品项的总价"""
        # self.items 是通过 OrderItem 模型中的 related_name='items' 反向关联过来的
        # a.price 是下单时锁定的单价， a.quantity 是数量
        return sum(item.price * item.quantity for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', help_text="所属的订单")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, help_text="具体的菜品")
    quantity = models.PositiveIntegerField(default=1, help_text="菜品份数")
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="下单时的菜品单价")

    def save(self, *args, **kwargs):
        if not self.id:
            self.price = self.menu_item.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} for Order {self.order.id}"