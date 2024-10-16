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
    path('', home, name='home'),

    path('compra/exitosa/<int:compra_id>/', compra_exitosa, name='compra_exitosa'),
    
    path('carrito/ver/', ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/restar/<int:producto_id>/', restar_producto, name='restar_producto'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('compra/confirmar/', confirmar_compra, name='confirmar_compra'),
    path('compra/confirmar/invitado/', confirmar_compra_invitado, name='confirmar_compra_invitado'),
    path('registrar-cliente/', registrar_cliente, name='registrar_cliente'),

    path('bodega/operaciones/', operaciones_bodega, name='operaciones_bodega'),

    path('mi_negocio/', mi_negocio, name='mi_negocio'),

    path('staffs/', list_staff, name='list_staff'),
    path('staffs/eliminar/<int:staff_id>/', erase_staff, name='erase_staff'),  # Correcta ruta para eliminar
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



    path('negocios/', list_negocios, name='list_negocios'),
    path('negocio/modificar/<int:negocio_id>/', mod_negocio, name='mod_negocio'),
    path('negocio/borrar/<int:negocio_id>/', erase_negocio, name='erase_negocio'),

    path('proveedores/agregar/', add_proveedor, name='add_proveedor'),
    path('proveedores/', list_proveedores, name='list_proveedores'),
    path('proveedor/modificar/<proveedor_id>/', mod_proveedor, name='mod_proveedor'),
    path('proveedor/borrar/<proveedor_id>/', erase_proveedor, name='erase_proveedor'),

    path('categorias/', list_categorias, name='list_categorias'),
    path('categorias/agregar/', add_categoria, name='add_categoria'),
    path('categorias/modificar/<int:categoria_id>/', mod_categoria, name='mod_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', erase_categoria, name='erase_categoria'),
    
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
    path('productos/descontinuar/<int:producto_id>/', descontinuar_prod, name='descontinuar_prod'),
    path('productos/devolver/<int:producto_id>/', devolver_prod, name='devolver_prod'),
    path('producto/<int:producto_id>/actualizar_precio/', actualizar_precio_prod, name='actualizar_precio_prod'),


    

    
    

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


