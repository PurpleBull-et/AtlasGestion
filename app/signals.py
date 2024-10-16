from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from atlasManagement.middleware import get_current_authenticated_user

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    staff_jefe, _ = Group.objects.get_or_create(name='staff_jefe')
    staff_bodega, _ = Group.objects.get_or_create(name='staff_bodega')
    staff_vendedor, _ = Group.objects.get_or_create(name='staff_vendedor')

    permisos_jefe = [
        'view_almacen', 'add_almacen', 'change_almacen', 'delete_almacen',
        'view_negocio', 'add_negocio', 'change_negocio', 'delete_negocio',
        'view_producto', 'add_producto', 'change_producto', 'delete_producto',
        'view_compra', 'add_compra', 'change_compra', 'delete_compra',
        'view_entradabodega', 'add_entradabodega', 'change_entradabodega', 'delete_entradabodega',
        'view_detallecompra', 'add_detallecompra', 'change_detallecompra', 'delete_detallecompra',
        'view_carritoproducto', 'add_carritoproducto', 'change_carritoproducto', 'delete_carritoproducto',
        'view_imagen', 'add_imagen', 'change_imagen', 'delete_imagen',
        'view_devolucionproveedor', 'add_devolucionproveedor', 'change_devolucionproveedor', 'delete_devolucionproveedor',
        'view_categoria', 'add_categoria', 'change_categoria', 'delete_categoria',
        'view_proveedor', 'add_proveedor', 'change_proveedor', 'delete_proveedor',
        'view_productosdevueltos', 'add_productosdevueltos', 'change_productosdevueltos', 'delete_productosdevueltos'
    ]

    permisos_bodega = [
        'view_almacen', 'add_almacen', 'change_almacen',
        'view_producto', 'add_producto', 'change_producto',
        'view_compra', 'add_compra', 'change_compra',
        'view_entradabodega', 'add_entradabodega', 'change_entradabodega',
        'view_detallecompra', 'add_detallecompra', 'change_detallecompra',
        'view_devolucionproveedor', 'add_devolucionproveedor',
        'view_categoria', 'add_categoria', 'change_categoria', 'delete_categoria',
        'view_proveedor', 'add_proveedor', 'change_proveedor'
    ]

    permisos_vendedor = [
        'view_producto',
        'view_compra', 'add_compra',
        'view_detallecompra',
        'view_categoria', 'add_categoria', 'change_categoria', 'delete_categoria'
    ]

    for perm_codename in permisos_jefe:
        try:
            permission = Permission.objects.get(codename=perm_codename)
            staff_jefe.permissions.add(permission)
        except Permission.DoesNotExist:
            print(f"Permiso {perm_codename} no encontrado")

    for perm_codename in permisos_bodega:
        try:
            permission = Permission.objects.get(codename=perm_codename)
            staff_bodega.permissions.add(permission)
        except Permission.DoesNotExist:
            print(f"Permiso {perm_codename} no encontrado")

    for perm_codename in permisos_vendedor:
        try:
            permission = Permission.objects.get(codename=perm_codename)
            staff_vendedor.permissions.add(permission)
        except Permission.DoesNotExist:
            print(f"Permiso {perm_codename} no encontrado")




@receiver(post_save, sender=Producto)
def registrar_cambios_producto(sender, instance, created, **kwargs):
    if not created:
        if 'update_fields' not in kwargs or kwargs.get('update_fields') is None:
            usuario = get_current_authenticated_user()  
            cambio = f'Producto {instance.nombre} ha sido modificado.'
            HistorialProducto.objects.create(producto=instance, usuario=usuario, cambio=cambio)

