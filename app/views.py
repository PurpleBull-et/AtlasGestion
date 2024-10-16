from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa
from django.db.models import Q
from itertools import chain
from django.middleware import csrf
from django.db.models.functions import TruncDay
from django.db.models import Sum, Avg
from .forms import *
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Group, User

def es_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

@login_required
def home(request):
    palabra_clave = request.GET.get('buscar', None)
    categoria = request.GET.get('categoria', None)

    # Obtener el negocio relacionado al usuario
    if request.user.is_superuser:
        productos = Producto.objects.all()
    else:
        staff_profile = StaffProfile.objects.get(user=request.user)
        productos = Producto.objects.filter(almacen__negocio=staff_profile.negocio)

    # Filtrar por palabra clave (opcional)
    if palabra_clave:
        productos = productos.filter(
            Q(nombre__icontains=palabra_clave) |
            Q(descripcion__icontains=palabra_clave)
        )

    # Filtrar por categoría (opcional)
    if categoria:
        productos = productos.filter(categoria=categoria)

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    # Si la solicitud es AJAX, devolver solo el HTML de los productos
    if es_ajax(request):
        csrf_token = csrf.get_token(request)  # Obtener el token CSRF
        
        # Si no hay productos, devolvemos un mensaje
        if not productos.exists():
            html = '<p>No se encontraron productos</p>'
            return JsonResponse({'html': html}, status=200)

        html = render_to_string('app/productos_buscar.html', {
            'productos': productos,
            'csrf_token': csrf_token,  # Pasar el token CSRF al contexto
        })
        return JsonResponse({'html': html})

    return render(request, 'app/home.html', {
        'productos': productos,
        'carrito_items': carrito.carritoproducto_set.all(),
        'carrito_total': carrito.total
    })


@login_required
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    carrito_items = carrito.carritoproducto_set.all()

    # Verificar si el carrito está vacío
    if not carrito_items.exists():
        return render(request, 'app/carrito.html', {
            'carrito_items': [],
            'carrito_total': 0,
            'carrito_total_cantidad': 0,
            'mensaje_carrito_vacio': 'Tu carrito está vacío.'
        })

    return render(request, 'app/carrito.html', {
        'carrito_items': carrito_items,
        'carrito_total': carrito.total,
        'carrito_total_cantidad': carrito_items.count(),
    })

# Vista para agregar un producto al carrito
def registrar_cliente(request):
    if request.method == 'POST':
        form = PerfilClientesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')  # Después de guardar, redirige a home o muestra un mensaje de éxito
    else:
        form = PerfilClientesForm()

    return render(request, 'app/registrar_cliente_modal.html', {'form': form})



def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    if isinstance(producto, ProductoBar):
        if producto.cc_por_unidad < 200:  # ejemplo, verificamos que hay suficiente en stock
            return HttpResponse("No hay suficiente alcohol disponible", status=400)

        # Reducir el stock en cc
        producto.cc_por_unidad -= 200
        producto.save()

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    carrito_producto, created = CarritoProducto.objects.get_or_create(carrito=carrito, producto=producto)
    if not created:
        carrito_producto.cantidad += 1
        carrito_producto.save()

    actualizar_total_carrito(carrito)
    return redirect('home')



# Vista para restar la cantidad de un producto en el carrito
@require_POST
@login_required
def restar_producto(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    carrito = get_object_or_404(Carrito, usuario=request.user)
    carrito_producto = get_object_or_404(CarritoProducto, carrito=carrito, producto=producto)

    if carrito_producto.cantidad > 1:
        carrito_producto.cantidad -= 1
        carrito_producto.save()
    else:
        carrito_producto.delete()

    actualizar_total_carrito(carrito)

    if es_ajax(request):
        html_carrito = render_to_string('app/carrito.html', {
            'carrito_items': carrito.carritoproducto_set.all(),
            'carrito_total': carrito.total,
            'carrito_total_cantidad': carrito.carritoproducto_set.count()
        })
        return JsonResponse({'carrito_html': html_carrito})

    return redirect('home')

# Vista para eliminar un producto del carrito
@require_POST
@login_required
def eliminar_del_carrito(request, item_id):
    carrito_producto = get_object_or_404(CarritoProducto, id=item_id, carrito__usuario=request.user)
    carrito_producto.delete()

    carrito = carrito_producto.carrito
    actualizar_total_carrito(carrito)

    if es_ajax(request):
        html_carrito = render_to_string('app/carrito.html', {
            'carrito_items': carrito.carritoproducto_set.all(),
            'carrito_total': carrito.total,
            'carrito_total_cantidad': carrito.carritoproducto_set.count()
        })
        return JsonResponse({'carrito_html': html_carrito})

    return redirect('home')

# Función auxiliar para actualizar el total del carrito
def actualizar_total_carrito(carrito):
    total = sum(item.total_precio() for item in carrito.carritoproducto_set.all())
    carrito.total = total
    carrito.save()

    carrito.save()


from django.contrib.auth.decorators import login_required
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#PAGO
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from .models import Carrito, CarritoProducto, Compra, DetalleCompra


@login_required
def confirmar_compra(request):
    carrito = get_object_or_404(Carrito, usuario=request.user)
    carrito_items = carrito.carritoproducto_set.all()

    if carrito_items:
        # Crear una nueva compra
        compra = Compra.objects.create(usuario=request.user, total=carrito.total)

        # Crear los detalles de la compra
        for item in carrito_items:
            DetalleCompra.objects.create(
                compra=compra,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )

        # Limpiar el carrito una vez realizada la compra
        carrito.carritoproducto_set.all().delete()
        carrito.total = 0
        carrito.save()

        # Redirigir a la página de éxito de compra
        return redirect('compra_exitosa', compra_id=compra.id)

    return redirect('home')


@login_required
def compra_exitosa(request, compra_id):
    # Buscar la compra por ID, independientemente de si tiene un usuario o no
    compra = get_object_or_404(Compra, id=compra_id)

    # Obtener los detalles de la compra
    detalles = compra.detalles.all()

    # Si el parámetro 'pdf' está presente en la URL, generar PDF
    if 'pdf' in request.GET:
        # Cargar la plantilla HTML para el PDF
        template_path = 'payment/compra_exitosa_pdf.html'
        context = {
            'compra': compra,
            'detalles': detalles
        }

        # Generar el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="comprobante.pdf"'

        # Renderizar el HTML a PDF
        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)

        # Verificar errores de generación
        if pisa_status.err:
            return HttpResponse('Hubo un error al generar el PDF <pre>%s</pre>' % html)

        return response

    # Renderizar la página HTML normal si no se solicita PDF
    return render(request, 'payment/compra_exitosa.html', {
        'compra': compra,
        'detalles': detalles
    })

def confirmar_compra_invitado(request):
    email = request.POST.get('email_invitado')
    carrito = get_object_or_404(Carrito, usuario=request.user)
    carrito_items = carrito.carritoproducto_set.all()

    if carrito_items:
        # Crear una nueva compra sin usuario registrado, solo con el correo si se proporciona
        compra = Compra.objects.create(usuario=None, total=carrito.total, correo=email)

        # Crear los detalles de la compra
        for item in carrito_items:
            DetalleCompra.objects.create(
                compra=compra,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )

        # Limpiar el carrito una vez realizada la compra
        carrito.carritoproducto_set.all().delete()
        carrito.total = 0
        carrito.save()

        # Redirigir a la página de éxito de compra
        return redirect('compra_exitosa', compra_id=compra.id)  # Asegúrate de que compra.id se está obteniendo correctamente

    return redirect('home')


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# REGISTRO, LOGIN Y LOGOUT
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')  
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})



@require_POST
def logoutView(request):
    logout(request) 
    return redirect('login') 
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# CRUD PRODUCTO
@login_required
@permission_required('app.add_producto', raise_exception=True)
def add_prod(request):
    staff_profile = StaffProfile.objects.get(user=request.user)  # Obtener el negocio del usuario

    if request.method == 'POST':
        producto_form = ProductoForm(request.POST)
        
        if producto_form.is_valid():
            producto = producto_form.save(commit=False)
            producto.almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()  # Enlazar con el almacén del negocio
            producto.save()

            return redirect('list_prod')
    else:
        producto_form = ProductoForm()

    # Filtrar las categorías por el negocio del usuario
    producto_form.fields['categoria'].queryset = Categoria.objects.filter(negocio=staff_profile.negocio)

    return render(request, 'producto/add_prod.html', {
        'producto_form': producto_form
    })

@login_required
def list_prod(request):
    estado_filtro = request.GET.get('estado', None)
    negocio_filtro = request.GET.get('negocio', None)
    
    # Si el usuario es administrador
    if request.user.is_superuser:
        negocios = Negocio.objects.all()
        productos = Producto.objects.all()

        # Aplicar filtro de negocio
        negocio_nombre = None
        if negocio_filtro:
            try:
                negocio_filtro = int(negocio_filtro)
                productos = productos.filter(almacen__negocio_id=negocio_filtro)
                negocio_nombre = Negocio.objects.get(id=negocio_filtro).nombre  
            except (ValueError, Negocio.DoesNotExist):
                negocio_filtro = None
        
        if estado_filtro:
            productos = productos.filter(estado=estado_filtro)

    else:
        staff_profile = StaffProfile.objects.get(user=request.user)
        productos = Producto.objects.filter(almacen__negocio=staff_profile.negocio)
        negocio_nombre = staff_profile.negocio.nombre 

        if estado_filtro:
            productos = productos.filter(estado=estado_filtro)

        negocios = None

    return render(request, 'producto/list_prod.html', {
        'productos': productos,
        'estado_filtro': estado_filtro,
        'negocios': negocios,
        'negocio_filtro': negocio_filtro,
        'negocio_nombre': negocio_nombre 
    })




@login_required
@permission_required('app.delete_producto', raise_exception=True)
def erase_prod(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    staff_profile = StaffProfile.objects.get(user=request.user)
    if producto.almacen.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para eliminar este producto.")

    if request.method == 'POST':
        # En lugar de eliminar el producto, cambiar su estado a 'sin_stock'
        producto.estado = 'sin_stock'
        producto.save()
        
        return redirect('list_prod')
    
    return redirect('list_prod')

@login_required
@permission_required('app.change_producto', raise_exception=True)
def descontinuar_prod(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)

    # Verificar que el producto pertenece al negocio del staff
    staff_profile = StaffProfile.objects.get(user=request.user)
    if producto.almacen.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para modificar este producto.")

    devoluciones = []
    if producto.stock > 0:
        for proveedor in producto.proveedores.all():
            # Registrar toda la cantidad en stock como devuelta al último proveedor
            devolucion = DevolucionProveedor.objects.create(
                producto=producto,
                cantidad=producto.stock,
                proveedor=proveedor.nombre,
                fecha_devolucion=timezone.now()
            )
            devoluciones.append(devolucion)

    # Marcar el producto como descontinuado y poner stock a 0
    producto.estado = 'descontinuado'
    producto.stock = 0
    producto.save()

    messages.success(request, f'Producto {producto.nombre} descontinuado exitosamente.')
    return redirect('list_prod')


@login_required
@permission_required('app.add_productosdevueltos', raise_exception=True)
def devolver_prod(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        lote = request.POST.get('lote')
        motivo_devolucion = request.POST.get('motivo_devolucion')
        
        # Verificar la existencia del lote en las entradas de bodega
        entrada = EntradaBodega.objects.filter(producto=producto, lote=lote).first()
        
        if not entrada:
            messages.error(request, f"No se encontró una entrada con el lote {lote} para este producto.")
            return redirect('list_prod')

        # Verificar si ya existe una devolución para este lote, producto y proveedor
        devolucion_existente = ProductosDevueltos.objects.filter(
            producto=producto, 
            lote=lote, 
            proveedor=entrada.proveedor
        ).exists()

        if devolucion_existente:
            messages.error(request, f"El lote {lote} ya ha sido devuelto para este producto y proveedor.")
            return redirect('list_prod')

        # Si no existe una devolución previa, registrar la devolución
        devolucion = ProductosDevueltos.objects.create(
            producto=producto,
            entrada_bodega=entrada,
            cantidad_devuelta=entrada.cantidad_recibida,
            proveedor=entrada.proveedor,
            lote=entrada.lote,
            motivo_devolucion=motivo_devolucion
        )

        # Actualizar el stock del producto
        producto.stock -= entrada.cantidad_recibida
        producto.actualizar_estado()
        producto.save()

        messages.success(request, f"Devolución del lote {lote} registrada correctamente.")
        return redirect('list_prod')

    return render(request, 'producto/devolver_prod.html', {'producto': producto})

@login_required
@permission_required('app.change_producto', raise_exception=True)
def mod_prod(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    # Verificar que el producto pertenece al negocio del staff
    staff_profile = StaffProfile.objects.get(user=request.user)
    if producto.almacen.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para modificar este producto.")

    if request.method == 'POST':
        producto_form = ProductoForm(request.POST, instance=producto)

        if producto_form.is_valid():
            producto = producto_form.save()

            # Si el stock es 0, marcar como "sin_stock"
            if producto.stock == 0:
                producto.estado = 'sin_stock'
            producto.save()

            return redirect('list_prod')
    else:
        producto_form = ProductoForm(instance=producto)

    return render(request, 'producto/mod_prod.html', {
        'producto_form': producto_form,
        'producto': producto,
    })


@login_required
@permission_required('app.change_producto', raise_exception=True)
def actualizar_precio_prod(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)

    # Verificar que el producto pertenece al negocio del staff
    staff_profile = StaffProfile.objects.get(user=request.user)
    if producto.almacen.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para modificar este producto.")

    if request.method == 'POST':
        form = ActualizarPrecioForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            return redirect('list_prod')  # Recargar la página después de guardar
        else:
            return render(request, 'producto/modal_actualizar_precio.html', {
                'form': form,
                'producto': producto
            })
    else:
        form = ActualizarPrecioForm(instance=producto)
    return render(request, 'producto/modal_actualizar_precio.html', {
        'form': form,
        'producto': producto
    })

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# Error de pago
def error_pago(request):
    return render(request, 'payment/pay_error.html')


def error_400(request, exception=None):
    return render(request, 'err/error_400.html', status=400)

def error_403(request, exception=None):
    return render(request, 'err/error_403.html', status=403)

def error_404(request, exception):
    return render(request, 'err/error_404.html', status=404)

def error_500(request):
    return render(request, 'err/error_500.html', status=500)

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#BODEGA
@login_required
@staff_member_required
@permission_required('app.view_entradabodega', raise_exception=True)
def historial_bodega(request):
    entradas = EntradaBodega.objects.all().order_by('-fecha_entrada')
    return render(request, 'bodega/historial_bodega.html', {'entradas': entradas})

@login_required
@staff_member_required
@permission_required('app.add_entradabodega', raise_exception=True)
def operaciones_bodega(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio  # Obtener el negocio desde el perfil del staff

    # Filtrar productos que están asociados al negocio del staff y tienen stock o están sin stock
    productos_validos = Producto.objects.filter(almacen__negocio=negocio, estado__in=['disponible', 'sin_stock'])
    
    # Filtrar proveedores que están asociados al negocio del staff
    proveedores_validos = Proveedor.objects.filter(negocio=negocio)

    # Manejo del formulario de entrada de bodega
    if request.method == 'POST':
        form = EntradaBodegaForm(request.POST)
        if form.is_valid():
            entrada = form.save(commit=False)
            
            # Asignar el negocio correctamente a la entrada de bodega
            entrada.negocio = negocio

            # Actualizar el stock del producto en base a la cantidad recibida
            entrada.producto.stock += entrada.cantidad_recibida
            entrada.producto.save()

            # Guardar la entrada de bodega
            entrada.save()
            return redirect('operaciones_bodega')
    else:
        form = EntradaBodegaForm()

        # Filtrar productos y proveedores válidos en el formulario
        form.fields['producto'].queryset = productos_validos
        form.fields['proveedor'].queryset = proveedores_validos

    # Mostrar las entradas de bodega filtradas por el negocio actual
    entradas = EntradaBodega.objects.filter(negocio=negocio).order_by('-fecha_entrada')

    # Obtener todas las devoluciones de productos
    devoluciones = ProductosDevueltos.objects.filter(entrada_bodega__negocio=negocio).order_by('-fecha_devolucion')

    return render(request, 'bodega/operaciones_bodega.html', {
        'form': form,
        'entradas': entradas,
        'devoluciones': devoluciones  # Pasamos las devoluciones al contexto
    })





#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
@login_required
@staff_member_required
def mi_negocio(request):
    # Obtener todas las ventas realizadas
    compras = Compra.objects.prefetch_related('detalles').all()

    # Datos del perfil del staff
    staff = request.user

    # Calcular KPI
    total_ventas = Compra.objects.aggregate(Sum('total'))['total__sum'] or 0
    promedio_ventas_diario = Compra.objects.annotate(dia=TruncDay('fecha')).values('dia').annotate(total_dia=Sum('total')).aggregate(Avg('total_dia'))['total_dia__avg'] or 0
    producto_mas_vendido = DetalleCompra.objects.values('producto__nombre').annotate(cantidad_total=Sum('cantidad')).order_by('-cantidad_total').first()

    return render(request, 'business/mi_negocio.html', {
        'compras': compras,
        'staff': staff,
        'total_ventas': total_ventas,
        'promedio_ventas_diario': promedio_ventas_diario,
        'producto_mas_vendido': producto_mas_vendido,
    })
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE STAFF
@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_staff(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = StaffProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_staff = True 
            user.is_superuser = False 
            user.is_active = True
            user.save()

            # Añadir al grupo STAFF
            staff_group, created = Group.objects.get_or_create(name='staff_default')
            user.groups.add(staff_group)

            # Guardar perfil de staff
            staff_profile = profile_form.save(commit=False)
            staff_profile.user = user
            staff_profile.save()

            return redirect('list_staff')
    else:
        user_form = UserForm()
        profile_form = StaffProfileForm()

    return render(request, 'administration/staff/register_staff.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_staff(request):
    # Obtener el filtro de negocio desde la URL (si existe)
    negocio_filtro = request.GET.get('negocio', None)

    # Obtener todos los negocios para el dropdown
    negocios = Negocio.objects.all()

    # Si se ha seleccionado un negocio, filtrar los usuarios por ese negocio
    if negocio_filtro:
        try:
            negocio_filtro = int(negocio_filtro)
            staff_list = User.objects.filter(staffprofile__negocio_id=negocio_filtro, is_staff=True, is_active=True, is_superuser=False)
            negocio_nombre = Negocio.objects.get(id=negocio_filtro).nombre
        except (ValueError, Negocio.DoesNotExist):
            staff_list = User.objects.filter(is_staff=True, is_active=True, is_superuser=False)
            negocio_nombre = None
    else:
        # Si no hay filtro, mostrar todos los usuarios staff
        staff_list = User.objects.filter(is_staff=True, is_active=True, is_superuser=False)
        negocio_nombre = None

    return render(request, 'administration/staff/list_staff.html', {
        'staff_list': staff_list,
        'negocios': negocios,
        'negocio_filtro': negocio_filtro,
        'negocio_nombre': negocio_nombre
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mod_staff_account(request, staff_id):
    user = get_object_or_404(User, pk=staff_id)

    if request.method == 'POST':
        # Modificamos el nombre de usuario y contraseña
        user_form = UserForm(request.POST, instance=user)
        password_form = PasswordChangeForm(user, request.POST)

        if user_form.is_valid() and password_form.is_valid():
            user_form.save()

            # Cambiar la contraseña si se proporciona
            user = password_form.save()
            update_session_auth_hash(request, user)  # Mantener la sesión activa después del cambio de contraseña

            return redirect('list_staff')
    else:
        user_form = UserForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'administration/staff/mod_staff_account.html', {
        'user_form': user_form,
        'password_form': password_form,
        'staff': user,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mod_staff_profile(request, staff_id):
    user = get_object_or_404(User, pk=staff_id)
    staff_profile = get_object_or_404(StaffProfile, user=user)

    grupos = Group.objects.all()

    if request.method == 'POST':
        profile_form = StaffProfileForm(request.POST, instance=staff_profile)

        if profile_form.is_valid():
            profile_form.save()

            # Asignar grupo al usuario
            grupo_seleccionado = request.POST.get('grupo')
            if grupo_seleccionado:
                grupo = Group.objects.get(id=grupo_seleccionado)
                user.groups.clear()
                user.groups.add(grupo)

            return redirect('list_staff')
    else:
        profile_form = StaffProfileForm(instance=staff_profile)

    return render(request, 'administration/staff/mod_staff_profile.html', {
        'profile_form': profile_form,
        'staff': user,
        'grupos': grupos,
        'grupo_actual': user.groups.first()
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def erase_staff(request, staff_id):
    user = get_object_or_404(User, pk=staff_id)

    if request.method == 'POST':
        # Eliminar el perfil asociado
        StaffProfile.objects.filter(user=user).delete()
        # Eliminar el usuario
        user.delete()
        return redirect('list_staff')

    return render(request, 'administration/staff/erase_staff.html', {'staff': user})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE ADMIN
# Listar administradores (solo superusuarios)
def list_admin(request):
    admin_list = User.objects.filter(is_superuser=True) 
    return render(request, 'administration/admin/list_admin.html', {'admin_list': admin_list})

# Registrar nuevo administrador
def register_admin(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = AdminProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_superuser = True
            user.is_staff = True
            user.save()

            # Verificar si ya existe un perfil para el usuario antes de crear uno nuevo
            if not AdminProfile.objects.filter(user=user).exists():
                admin_profile = profile_form.save(commit=False)
                admin_profile.user = user
                admin_profile.save()

            return redirect('list_admin')
    else:
        user_form = UserForm()
        profile_form = AdminProfileForm()

    return render(request, 'administration/admin/register_admin.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })



# Modificar perfil de administrador
def mod_admin_profile(request, admin_id):
    admin_profile = get_object_or_404(AdminProfile, user__id=admin_id, user__is_superuser=True)  # Filtrar por superusuario
    if request.method == 'POST':
        profile_form = AdminProfileForm(request.POST, instance=admin_profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('list_admin')
    else:
        profile_form = AdminProfileForm(instance=admin_profile)
    return render(request, 'administration/admin/mod_admin_profile.html', {'profile_form': profile_form})

# Modificar cuenta de administrador
def mod_admin_account(request, admin_id):
    user = get_object_or_404(User, id=admin_id, is_superuser=True)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        if user_form.is_valid():
            user_form.save()
            return redirect('list_admin')
    else:
        user_form = UserForm(instance=user)
    return render(request, 'administration/admin/mod_admin_account.html', {'user_form': user_form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def erase_admin(request, admin_id):
    user = get_object_or_404(User, pk=admin_id)

    if request.method == 'POST':
        AdminProfile.objects.filter(user=user).delete()
        user.delete()
        return redirect('list_admin')

    return render(request, 'administration/admin/erase_admin.html', {'admin': user})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#Cambio de clave

# Cambiar la contraseña de un usuario
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('password_success') 
        else:
            messages.error(request, 'Algo ocurrió, vuelve a intentarlo.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'administration/change_password.html', {'form': form})


@login_required
def password_success(request):
    return render(request, 'success/password_success.html')


@login_required
def licencia_vencida(request):
    return render(request, 'administration/licencia_vencida.html')
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE NEGOCIOS
@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_negocios(request):
    negocios = Negocio.objects.all()

    if request.method == 'POST':
        form = NegocioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('list_negocios')
    else:
        form = NegocioForm()

    return render(request, 'administration/negocio/list_negocios.html', {
        'form': form,
        'negocios': negocios
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mod_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, pk=negocio_id)
    almacen = Almacen.objects.filter(negocio=negocio).first()  # Obtener el almacén asociado

    if request.method == 'POST':
        form = NegocioForm(request.POST, request.FILES, instance=negocio)
        if form.is_valid():
            negocio = form.save(commit=False)
            negocio.save()
            
            if almacen:
                almacen.direccion = form.cleaned_data['almacen_direccion']
                almacen.save()
            return redirect('list_negocios')
    else:

        form = NegocioForm(instance=negocio, initial={
            'almacen_direccion': almacen.direccion if almacen else ''
        })

    return render(request, 'administration/negocio/mod_negocio.html', {
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def erase_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, pk=negocio_id)
    
    if request.method == 'POST':
        negocio.delete()
        return redirect('list_negocios')

    return render(request, 'administration/negocio/erase_negocio.html', {'negocio': negocio})

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE PROVEEDORES
@login_required
@permission_required('app.add_proveedor', raise_exception=True)
def add_proveedor(request):
    staff_profile = StaffProfile.objects.get(user=request.user)

    if request.method == 'POST':
        proveedor_form = ProveedorForm(request.POST)
        
        if proveedor_form.is_valid():
            proveedor = proveedor_form.save(commit=False)
            proveedor.negocio = staff_profile.negocio  # Enlazar el proveedor con el negocio del usuario actual
            proveedor.save()

            return redirect('list_proveedores')
    else:
        proveedor_form = ProveedorForm()

    return render(request, 'administration/proveedor/add_proveedor.html', {
        'proveedor_form': proveedor_form,
    })

@login_required
@permission_required('app.view_proveedor', raise_exception=True)
def list_proveedores(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    proveedores = Proveedor.objects.filter(negocio=staff_profile.negocio)  # Filtrar proveedores por negocio

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.negocio = staff_profile.negocio  # Asociar el proveedor al negocio
            proveedor.save()
            return redirect('list_proveedores')
    else:
        form = ProveedorForm()

    return render(request, 'administration/proveedor/list_proveedores.html', {
        'proveedores': proveedores,
        'form': form,  # Pasar el formulario al template
    })



@login_required
@permission_required('app.change_proveedor', raise_exception=True)
def mod_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    staff_profile = StaffProfile.objects.get(user=request.user)

    if proveedor.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para modificar este proveedor.")

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect('list_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'administration/proveedor/mod_proveedor.html', {'form': form})

@login_required
@permission_required('app.delete_proveedor', raise_exception=True)
def erase_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    staff_profile = StaffProfile.objects.get(user=request.user)

    if proveedor.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para eliminar este proveedor.")

    if request.method == 'POST':
        proveedor.delete()
        return redirect('list_proveedores')

    return render(request, 'administration/proveedor/erase_proveedor.html', {'proveedor': proveedor})

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE CATEGORIAS

@login_required
@permission_required('app.view_categoria', raise_exception=True)
def list_categorias(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    categorias = Categoria.objects.filter(negocio=staff_profile.negocio)  # Filtrar categorías por negocio

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.negocio = staff_profile.negocio  # Asociar la categoría al negocio del usuario
            categoria.save()
            return redirect('list_categorias')
    else:
        form = CategoriaForm()

    return render(request, 'categorias/list_categorias.html', {
        'categorias': categorias,
        'form': form,  # Pasar el formulario al template
    })

@login_required
@permission_required('app.add_categoria', raise_exception=True)
def add_categoria(request):
    staff_profile = StaffProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.negocio = staff_profile.negocio  # Asociar categoría con el negocio
            categoria.save()
            return redirect('list_categorias')
    else:
        form = CategoriaForm()

    return render(request, 'categorias/add_categoria.html', {'form': form})

@login_required
@permission_required('app.change_categoria', raise_exception=True)
def mod_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    staff_profile = StaffProfile.objects.get(user=request.user)

    if categoria.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para modificar esta categoría.")

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('list_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    return render(request, 'categorias/mod_categoria.html', {'form': form})

@login_required
@permission_required('app.delete_categoria', raise_exception=True)
def erase_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    staff_profile = StaffProfile.objects.get(user=request.user)

    if categoria.negocio != staff_profile.negocio:
        return HttpResponseForbidden("No tienes permiso para eliminar esta categoría.")

    if request.method == 'POST':
        categoria.delete()
        return redirect('list_categorias')

    return render(request, 'categorias/erase_categoria.html', {'categoria': categoria})
