from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import *

from django.conf.urls import handler400, handler403, handler404, handler500
from django.urls import path


handler400 = 'app.views.error_400'
handler403 = 'app.views.error_403'
handler404 = 'app.views.error_404'
handler500 = 'app.views.error_500'


urlpatterns = [
    path('hora-actual/', obtener_hora_actual, name='obtener_hora_actual'),
    path('conectado/', conectado, name='conectado'),

    path('compras/detalle/<int:compra_id>/', detalle_compra, name='detalle_compra'),
    path('', home, name='home'),
    path('ajax/cargar-provincias/', cargar_provincias, name='cargar_provincias'),
    path('ajax/cargar-comunas/', cargar_comunas, name='cargar_comunas'),

    path('compra/confirmar/invitado/', confirmar_compra_invitado, name='confirmar_compra_invitado'),

    path('carrito/boleta/agregar', reg_prod_boleta, name='reg_prod_boleta'),
    path('carrito/factura/agregar/', reg_prod_factura, name='reg_prod_factura'),

    path('boleta/', boleta, name='boleta'),
    path('carrito/boleta/agregar/<int:producto_id>/', agregar_al_carrito_boleta, name='agregar_al_carrito_boleta'),
    path('carrito/boleta/eliminar/<int:item_id>/', eliminar_del_carrito_boleta, name='eliminar_del_carrito_boleta'),
    path('carrito/boleta/restar/<int:producto_id>/', restar_producto_boleta, name='restar_producto_boleta'),
    path('confirmar_compra/boleta/', confirmar_compra_boleta, name='confirmar_compra_boleta'),
    
    path('producto/boleta/actualizar_descuento/<int:producto_id>/', actualizar_descuento_boleta, name='actualizar_descuento_boleta'),
    path('carrito/boleta/vaciar/', vaciar_carrito_boleta, name='vaciar_carrito_boleta'),
    path('compra/boleta/<int:compra_id>/', compra_exitosa_boleta, name='compra_exitosa_boleta'),

    path('factura/', factura, name='factura'),
    path('carrito/factura/agregar/<int:producto_id>/', agregar_al_carrito_factura, name='agregar_al_carrito_factura'),
    path('carrito/factura/eliminar/<int:item_id>/', eliminar_del_carrito_factura, name='eliminar_del_carrito_factura'),
    path('carrito/factura/restar/<int:producto_id>/', restar_producto_factura, name='restar_producto_factura'),
    path('confirmar_compra/factura/', confirmar_compra_factura, name='confirmar_compra_factura'),
    path('reg-producto/factura', reg_prod_factura, name='reg_prod_factura'),
    path('producto/factura/actualizar_descuento/<int:producto_id>/', actualizar_descuento_factura, name='actualizar_descuento_factura'),
    path('carrito/factura/vaciar/', vaciar_carrito_factura, name='vaciar_carrito_factura'),
    path('compra/factura/<int:compra_id>/', compra_exitosa_factura, name='compra_exitosa_factura'),
    
    path('compras/operaciones/', operaciones_bodega, name='operaciones_bodega'),
    path('compras/entrada/', listar_entradas_bodega, name='listar_entradas_bodega'),
    path('compras/entrada/<int:entrada_id>/', detalle_entrada_bodega, name='detalle_entrada_bodega'),
    path('compras/entrada/<int:entrada_id>/producto/<int:producto_id>/', detalle_prod_entrada_bodega, name='detalle_prod_entrada_bodega'),
    path('compras/entrada/<int:entrada_id>/devolucion/', devolver_factura, name='devolver_factura'),
    path('compras/devoluciones/', historial_devoluciones, name='historial_devoluciones'),


    path('socios/cuentas/agregar/', add_cliente, name='add_cliente'),
    path('socios/cuentas/', list_clientes, name='list_clientes'),
    path('socios/cuentas/modificar/<int:cliente_id>/', mod_cliente, name='mod_cliente'),
    path('socios/cuentas/eliminar/', erase_cliente, name='erase_cliente'),

    path('socios/empresas/agregar/', add_empresa, name='add_empresa'),
    path('socios/empresas/', list_empresa, name='list_empresa'),
    path('socios/empresas/modificar/<int:cliente_id>/', mod_empresa, name='mod_empresa'),
    path('socios/empresas/eliminar/', erase_empresa, name='erase_empresa'),

    path('mi_negocio_dashboard/', mi_negocio, name='mi_negocio'),

    path('staffs/', list_staff, name='list_staff'),
    path('staffs/eliminar/<int:staff_id>/', erase_staff, name='erase_staff'),
    path('licencia-vencida/', licencia_vencida, name='licencia_vencida'),
    path('staffs/registrar/', register_staff, name='register_staff'),
    
    #Mod cuenta y perfil staff
    path('perfil/modificar/<int:staff_id>/', mod_staff_profile, name='mod_staff_profile'),
    path('cuenta/modificar/<int:staff_id>/', mod_staff_account, name='mod_staff_account'),

    path('administradores/', list_admin, name='list_admin'),
    path('administradores/registrar/', register_admin, name='register_admin'),
    path('administradores/modificar-perfil/<int:admin_id>/', mod_admin_profile, name='mod_admin_profile'),
    path('administradores/modificar-cuenta/<int:admin_id>/', mod_admin_account, name='mod_admin_account'),
    path('administradores/eliminar/<int:admin_id>/', erase_admin, name='erase_admin'),

    path('change_password/', change_password, name='change_password'),
    path('password_success/', password_success, name='password_success'),

    #Mod cuenta y perfil staff
    path('negocios/', list_negocios, name='list_negocios'), #Método 2 en 1
    path('negocio/modificar/<int:negocio_id>/', mod_negocio, name='mod_negocio'),
    path('negocio/borrar/<int:negocio_id>/', erase_negocio, name='erase_negocio'),
    path('negocio/desactivar/<int:negocio_id>/', cambiar_estado_negocio, name='cambiar_estado_negocio'),


    path('proveedores/agregar/', add_proveedor, name='add_proveedor'),
    path('proveedores/', list_proveedores, name='list_proveedores'),
    path('proveedor/modificar/<proveedor_id>/', mod_proveedor, name='mod_proveedor'),
    path('proveedor/borrar/<proveedor_id>/', erase_proveedor, name='erase_proveedor'),

    path('categorias/', list_categorias, name='list_categorias'),
    path('categorias/agregar/', add_categoria, name='add_categoria'),
    path('categorias/modificar/<int:categoria_id>/', mod_categoria, name='mod_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', erase_categoria, name='erase_categoria'),

    path('marcas/', list_marcas, name='list_marcas'),
    path('marcas/agregar/', add_marca, name='add_marca'),
    path('marcas/modificar/<int:marca_id>/', mod_marca, name='mod_marca'),
    path('marcas/eliminar/<int:marca_id>/', erase_marca, name='erase_marca'),
    
     # Ruta para error de pago
    path('error-pago/', error_pago, name='error_pago'),

    # Registro, Login y Logout
    path('accounts/login/', login, name='login'),
    path('accounts/logout/', logoutView, name='logout'),

    # Reseteo de contraseña
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Gestión de productos (CRUD)
    path('productos/', list_prod, name='list_prod'),
    path('productos/agregar/', add_prod, name='add_prod'),
    path('productos/modificar/<producto_id>/', mod_prod, name='mod_prod'),
    path('productos/eliminar/<producto_id>/', erase_prod, name='erase_prod'),
    path('productos/devolver/<int:producto_id>/', devolver_prod, name='devolver_prod'),
    path('producto/<int:producto_id>/actualizar_precio/', actualizar_precio_prod, name='actualizar_precio_prod'),
    path('add_prod_modal/', add_prod_modal, name='add_prod_modal'),
    path('producto/modificar_modal/<int:producto_id>/', mod_prod_modal, name='mod_prod_modal'),
    path('bodega/operaciones_modal/', operaciones_bodega_modal, name='operaciones_bodega_modal'),

    # Busqueda dinamica
    path('buscar_categoria/', buscar_categoria, name='buscar_categoria'),
    path('buscar_marca/', buscar_marca, name='buscar_marca'),
    path('buscar_correo/', buscar_correo, name='buscar_correo'),

    path('gestionar_empresas/', gestionar_empresas, name='gestionar_empresas'),


    path('administrar/registrar_empleado', register_staff_for_boss, name='register_staff_for_boss'),
    path('administrar/empleados/', list_staff_for_boss, name='list_staff_for_boss'),
    path('administrar/empleados/modificar/perfil/<int:staff_id>/', mod_staff_profile_for_boss, name='mod_staff_profile_for_boss'),
    path('administrar/empleados/modificar/cuenta/<int:staff_id>/', mod_staff_account_for_boss, name='mod_staff_account_for_boss'),
    path('administrar/empleados/eliminar/<int:staff_id>/', erase_staff_for_boss, name='erase_staff_for_boss'),
    
    # Gráficos
    path('api/compras-por-mes/', compras_por_mes, name='compras_por_mes'),
    path('api/compras-diarias/', compras_diarias, name='compras_diarias'),
    path('reporte/', mostrar_reporte, name='mostrar_reporte'),
    path('reporte/pdf/', generar_reporte_pdf, name='generar_reporte_pdf'),

    

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


