from django.contrib import admin
from .models import Table, MenuItem, Order, OrderItem
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class MenuItemResource(resources.ModelResource):
    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'description', 'price', 'is_available', 'created_at')
        export_order = fields
        import_id_fields = ['id']
        skip_admin_log = True

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'table')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)

@admin.register(MenuItem)
class MenuItemAdmin(ImportExportModelAdmin):
    resource_class = MenuItemResource
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)
    from_encoding = "utf-8"
    to_encoding = "utf-8"

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'is_available')
    list_filter = ('is_available',)