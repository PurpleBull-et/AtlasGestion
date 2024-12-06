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
from django.forms import modelformset_factory
from django.db import transaction
from django.http import JsonResponse
from django.db.models import F, Sum, ExpressionWrapper, IntegerField
from django.db.models import F, Sum, ExpressionWrapper, IntegerField, Value, CharField, Case, When, Q
from django.http import JsonResponse
import requests
from datetime import datetime

@login_required
def conectado(request):
    request.session['last_activity'] = datetime.timestamp(datetime.now())
    return JsonResponse({'status': 'active'})

def jefe_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.groups.filter(name='staff_jefe').exists())
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped_view

def bodeguero_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.groups.filter(name='staff_bodega').exists())
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped_view

def cajero_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.groups.filter(name='staff_vendedor').exists())
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped_view

def negocio_mayorista_required(view_func):
    @login_required
    def wrapped_view(request, *args, **kwargs):
        
        staff_profile = get_object_or_404(StaffProfile, user=request.user)
        
        if not staff_profile.negocio.is_mayorista:
            return HttpResponseForbidden("Acceso denegado: Este recurso es solo para negocios mayoristas.")
        return view_func(request, *args, **kwargs)
    return wrapped_view

def validar_correo_unico(correo, modelo, negocio=None):
    filtro = {'correo': correo}
    if negocio:
        filtro['negocio'] = negocio

    if modelo.objects.filter(**filtro).exists():
        raise ValidationError(f"El correo '{correo}' ya está registrado en este módulo.")


from datetime import datetime
from django.utils.timezone import make_aware

def obtener_hora_actual():
    url = "https://www.timeapi.io/api/Time/current/zone?timeZone=America/Santiago"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Convertir la fecha y hora de la API en un objeto datetime
        fecha_hora_actual = datetime(
            year=data['year'],
            month=data['month'],
            day=data['day'],
            hour=data['hour'],
            minute=data['minute'],
            second=data['seconds']
        )
        
        # Asegurar que el objeto datetime sea timezone-aware
        fecha_hora_actual = make_aware(fecha_hora_actual)
        return fecha_hora_actual
    except requests.exceptions.RequestException as e:
        # En caso de error, devuelve la hora del servidor
        return make_aware(datetime.now())

def cargar_provincias(request):
    region_id = request.GET.get('region_id')
    provincias = Provincia.objects.filter(region_id=region_id).order_by('nombre')
    return JsonResponse(list(provincias.values('id', 'nombre')), safe=False)

def cargar_comunas(request):
    provincia_id = request.GET.get('provincia_id')
    comunas = Comuna.objects.filter(provincia_id=provincia_id).order_by('nombre')
    return JsonResponse(list(comunas.values('id', 'nombre')), safe=False)

def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'is_superuser': request.user.is_superuser,
        'es_jefe': request.user.groups.filter(name='staff_jefe').exists(),
        'es_cajero': request.user.groups.filter(name='staff_vendedor').exists(),
        'es_bodeguero': request.user.groups.filter(name='staff_bodega').exists(),
    }

@login_required
@staff_member_required
def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    detalles = compra.detalles.all()

    # Seleccionar template basado en `tipo_documento`
    if compra.tipo_documento == "boleta":
        template_name = 'comprobante/compra_exitosa_boleta.html'
    elif compra.tipo_documento == "factura":
        template_name = 'comprobante/compra_exitosa_factura.html'
    else:
        return HttpResponse("Tipo de documento desconocido", status=400)

    return render(request, template_name, {
        'compra': compra,
        'detalles': detalles,
    })

@login_required
@staff_member_required
def home(request):
    user = request.user
    es_jefe = user.groups.filter(name="staff_jefe").exists()
    es_cajero = user.groups.filter(name="staff_vendedor").exists()
    es_bodeguero = user.groups.filter(name="staff_bodega").exists()

    if request.user.is_superuser:
        return redirect('list_admin') 

    staff_profile = StaffProfile.objects.get(user=request.user)

    # Ordenar las compras desde la más reciente
    compras = Compra.objects.filter(
        usuario__staffprofile__negocio=staff_profile.negocio
    ).prefetch_related('detalles').order_by('-fecha')

    # Aplicar paginación (10 compras por página)
    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')  # Obtener el número de página
    compras_page = paginator.get_page(page_number)  # Página actual

    # Cálculo de KPI si es jefe
    if es_jefe:
        total_ventas = compras.aggregate(Sum('total'))['total__sum'] or 0
        promedio_ventas_diario = compras.annotate(
            dia=TruncDay('fecha')
        ).values('dia').annotate(
            total_dia=Sum('total')
        ).aggregate(
            Avg('total_dia')
        )['total_dia__avg'] or 0
        producto_mas_vendido = DetalleCompra.objects.filter(
            compra__usuario__staffprofile__negocio=staff_profile.negocio
        ).values('producto__nombre').annotate(
            cantidad_total=Sum('cantidad')
        ).order_by('-cantidad_total').first()
    else:
        total_ventas = promedio_ventas_diario = producto_mas_vendido = None

    return render(request, 'app/home.html', {
        'staff': user,
        'es_jefe': es_jefe,
        'es_cajero': es_cajero,
        'es_bodeguero': es_bodeguero,
        'compras': compras_page,  # Pasar la página actual al contexto
        'total_ventas': total_ventas,
        'promedio_ventas_diario': promedio_ventas_diario,
        'producto_mas_vendido': producto_mas_vendido,
    })




def es_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# BOLETA
@login_required
def boleta(request):
    palabra_clave = request.GET.get('buscar', '')
    categoria_filtro = request.GET.get('categoria', None)
    negocio_filtro = request.GET.get('negocio', None)

    if request.user.is_superuser:
        productos = Producto.objects.exclude(precio=0)
        categorias = Categoria.objects.all()
        marcas = Marca.objects.all()
        proveedores = Proveedor.objects.all()
        negocios = Negocio.objects.all()
    else:
        staff_profile = StaffProfile.objects.get(user=request.user)
        productos = Producto.objects.filter(almacen__negocio=staff_profile.negocio).exclude(precio=0)
        categorias = Categoria.objects.filter(negocio=staff_profile.negocio)
        marcas = Marca.objects.filter(negocio=staff_profile.negocio)
        proveedores = Proveedor.objects.filter(negocio=staff_profile.negocio)
        negocios = None

    if palabra_clave:
        productos = productos.filter(Q(nombre__icontains=palabra_clave))

    if categoria_filtro and categoria_filtro.isdigit():
        productos = productos.filter(categoria_id=int(categoria_filtro))

    if request.user.is_superuser and negocio_filtro and negocio_filtro.isdigit():
        productos = productos.filter(almacen__negocio_id=int(negocio_filtro))

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="boleta")
    carrito.actualizar_total()

    
    return render(request, 'caja/boleta.html', {
        'productos': productos,
        'carrito_items': carrito.carritoproducto_set.all(),
        'carrito_subtotal': carrito.subtotal,
        'carrito_descuento_total': carrito.descuento_total,
        'carrito_iva': carrito.iva_total,
        'carrito_total': carrito.total,
        'categorias': categorias,
        'marcas': marcas,
        'proveedores': proveedores,
        'negocios': negocios,
        'categoria_filtro': categoria_filtro,
        'negocio_filtro': negocio_filtro,
        'palabra_clave': palabra_clave,
    })


@login_required
def agregar_al_carrito_boleta(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="boleta")

    carrito_producto, created = CarritoProducto.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': 1, 'precio_unitario': producto.precio}
    )

    if not created:
        carrito_producto.cantidad += 1
    carrito_producto.save()
    carrito.actualizar_total()
    return redirect('boleta')

@require_POST
@login_required
def eliminar_del_carrito_boleta(request, item_id):
    carrito_producto = get_object_or_404(CarritoProducto, id=item_id, carrito__usuario=request.user, carrito__tipo="boleta")
    carrito_producto.delete()
    carrito_producto.carrito.actualizar_total()
    return redirect('boleta')


@login_required
def confirmar_compra_boleta(request):
    if request.method == 'POST':
        # Identificar si la solicitud es para cancelar la venta
        if 'cancelar' in request.POST:
            carrito = Carrito.objects.filter(usuario=request.user, tipo="boleta").first()
            if carrito:
                carrito.carritoproducto_set.all().delete()  # Elimina todos los productos del carrito
                carrito.actualizar_total()  # Actualiza el total a 0
            messages.success(request, "El carrito ha sido vaciado.")
            return redirect('boleta')  # Redirige al sitio actual (boleta)

        correo = request.POST.get('correo', '').strip()
        medio_pago = request.POST.get('medio_pago', '')

        carrito = get_object_or_404(Carrito, usuario=request.user, tipo="boleta")
        carrito_items = carrito.carritoproducto_set.all()

        if carrito_items:
            perfil_cliente = None
            if correo:
                perfil_cliente, _ = PerfilClientes.objects.get_or_create(correo=correo)

            # Calcular subtotal (sin IVA), descuentos, IVA y total
            subtotal = sum((item.producto.precio / 1.19) * item.cantidad for item in carrito_items)
            descuento_total = sum(
                (item.producto.precio / 1.19) * item.cantidad * item.producto.descuento / 100 for item in carrito_items
            )
            iva_total = (subtotal - descuento_total) * 0.19
            total = subtotal - descuento_total + iva_total

            # Obtener la fecha y hora actual
            fecha_hora_actual = obtener_hora_actual()

            # Crear compra
            compra = Compra.objects.create(
                usuario=request.user,
                subtotal=subtotal,
                descuento_total=descuento_total,
                iva_total=iva_total,
                total=total,
                nombre_staff=request.user.get_full_name(),
                correo=perfil_cliente.correo if perfil_cliente else None,
                medio_pago=medio_pago,
                tipo_documento='boleta',
                fecha=fecha_hora_actual  
            )

            # Procesar cada item en el carrito
            for item in carrito_items:
                producto = item.producto
                if producto.stock >= item.cantidad:
                    producto.stock -= item.cantidad
                    producto.save()

                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=item.cantidad,
                        precio_unitario=producto.precio
                    )
                else:
                    messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
                    return redirect('boleta')

            # Limpiar el carrito
            carrito.carritoproducto_set.all().delete()
            carrito.actualizar_total()

            # Generar y enviar boleta en PDF
            if correo:
                template_path = 'comprobante/boleta_pdf.html'
                context = {'compra': compra, 'detalles': compra.detalles.all()}
                pdf = generar_pdf(template_path, context)
                if pdf:
                    enviar_correo(
                        correo, 
                        '¡Su compra ha sido exitosa!', 
                        'Hola, A continuación te adjuntamos la Boleta electrónica asociada a tu compra, para que esté disponible dónde y cuándo quieras. Guarda esta boleta e imprímela sólo de ser necesario. ¡Cuidemos juntos nuestro planeta!.', 
                        pdf, 
                        'boleta.pdf'
                    )

            messages.success(request, 'La compra ha sido confirmada.')
            return redirect('compra_exitosa_boleta', compra_id=compra.id)
        else:
            messages.warning(request, 'El carrito está vacío.')
            return redirect('boleta')


def generar_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if not pisa_status.err:
        return result.getvalue()
    return None

def enviar_correo(destinatario, asunto, mensaje, archivo, nombre_archivo):
    email = EmailMessage(asunto, mensaje, 'contacto@atlasgestion.cl', [destinatario])
    email.attach(nombre_archivo, archivo, 'application/pdf')
    email.send()

@require_POST
@login_required
def restar_producto_boleta(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    carrito = get_object_or_404(Carrito, usuario=request.user, tipo="boleta")
    carrito_producto = get_object_or_404(CarritoProducto, carrito=carrito, producto=producto)

    if carrito_producto.cantidad > 1:
        carrito_producto.cantidad -= 1
        carrito_producto.save()
    else:
        carrito_producto.delete()

    carrito.actualizar_total()
    return redirect('boleta')

@login_required
@permission_required('app.add_producto', raise_exception=True)
def reg_prod_boleta(request):
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if request.method == "GET":
        return render(request, 'caja/reg_prod_boleta.html', {})

    elif request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        precio = int(request.POST.get("precio", 0))
        stock = int(request.POST.get("stock", 0))

        # Manejo de Marca
        marca_id = request.POST.get("marca_id", None)
        if marca_id:
            marca = get_object_or_404(Marca, id=marca_id)
        else:
            marca_nombre = request.POST.get("marca_nombre", "").strip()
            marca, _ = Marca.objects.get_or_create(nombre=marca_nombre, negocio=staff_profile.negocio)

        # Manejo de Categoría
        categoria_id = request.POST.get("categoria_id", None)
        if categoria_id:
            categoria = get_object_or_404(Categoria, id=categoria_id)
        else:
            categoria_nombre = request.POST.get("categoria_nombre", "").strip()
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre, negocio=staff_profile.negocio)

        almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()
        if not almacen:
            return JsonResponse({"success": False, "message": "No se encontró un almacén asociado al negocio."}, status=400)

        # Crear el producto
        producto = Producto.objects.create(
            nombre=nombre,
            precio=precio or 0,
            stock=stock,
            marca=marca,
            categoria=categoria,
            estado="ingresado_manual",
            descuento=0,
            precio_mayorista=0,
            descuento_mayorista=0,
            almacen=almacen,  
        )

        # Agregar automáticamente al carrito
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="boleta")
        carrito_producto, created = CarritoProducto.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 1, 'precio_unitario': producto.precio},
        )
        if not created:
            carrito_producto.cantidad += 1
            carrito_producto.save()

        # Actualizar el total del carrito
        carrito.actualizar_total()

        messages.success(request, f'El producto "{producto.nombre}" ha sido registrado y agregado al carrito de boleta.')
        return JsonResponse({"success": True})

    # Si llega por otro método (como PUT o DELETE), devolver un error
    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)



@login_required
@permission_required('app.change_producto', raise_exception=True)
def actualizar_descuento_boleta(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    if request.method == 'POST':
        nuevo_descuento = request.POST.get('descuento', 0)  
        
        if nuevo_descuento:
            producto.descuento = int(nuevo_descuento)
        
        producto.save()
        messages.success(request, f"El descuento de '{producto.nombre}' han sido actualizados.")


    return redirect('boleta')

@login_required
def vaciar_carrito_boleta(request):
    carrito = Carrito.objects.filter(usuario=request.user, tipo="boleta").first()
    if carrito:
        carrito.carritoproducto_set.all().delete()  # Elimina todos los productos del carrito
        carrito.actualizar_total()  # Resetea el total del carrito
    messages.success(request, "El carrito ha sido vaciado.")
    return redirect('boleta')  # Redirige a la página de boleta


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# FACTURA
@login_required
@negocio_mayorista_required
def factura(request):
    palabra_clave = request.GET.get('buscar', '')
    categoria_filtro = request.GET.get('categoria', None)
    negocio_filtro = request.GET.get('negocio', None)
    clientes = PerfilClientes.objects.all()  # Agregar clientes al contexto
    cliente_form = PerfilClientesForm()
    
    if request.user.is_superuser:
        productos = Producto.objects.exclude(precio_mayorista=0)
        categorias = Categoria.objects.all()
        marcas = Marca.objects.all()
        proveedores = Proveedor.objects.all()
        negocios = Negocio.objects.all()
    else:
        staff_profile = StaffProfile.objects.get(user=request.user)
        productos = Producto.objects.filter(almacen__negocio=staff_profile.negocio).exclude(precio_mayorista=0)
        categorias = Categoria.objects.filter(negocio=staff_profile.negocio)
        marcas = Marca.objects.filter(negocio=staff_profile.negocio)
        proveedores = Proveedor.objects.filter(negocio=staff_profile.negocio)
        negocios = None

    if palabra_clave:
        productos = productos.filter(Q(nombre__icontains=palabra_clave))

    if categoria_filtro and categoria_filtro.isdigit():
        productos = productos.filter(categoria_id=int(categoria_filtro))

    if request.user.is_superuser and negocio_filtro and negocio_filtro.isdigit():
        productos = productos.filter(almacen__negocio_id=int(negocio_filtro))

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="factura")
    carrito.actualizar_total_mayorista()  
    
    return render(request, 'caja/factura.html', {
        'productos': productos,
        'carrito_items': carrito.carritoproducto_set.all(),
        'carrito_subtotal': carrito.subtotal,
        'carrito_descuento_total': carrito.descuento_total,
        'carrito_iva': carrito.iva_total,
        'carrito_total': carrito.total,
        'categorias': categorias,
        'marcas': marcas,
        'proveedores': proveedores,
        'negocios': negocios,
        'categoria_filtro': categoria_filtro,
        'negocio_filtro': negocio_filtro,
        'palabra_clave': palabra_clave,
        'clientes': clientes,
        'cliente_form': cliente_form,
    })



@login_required
def agregar_al_carrito_factura(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="factura")

    carrito_producto, created = CarritoProducto.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': 1, 'precio_unitario': producto.precio_mayorista}
    )

    if not created:
        carrito_producto.cantidad += 1
    carrito_producto.save()
    carrito.actualizar_total_mayorista()
    return redirect('factura')


@require_POST
@login_required
def eliminar_del_carrito_factura(request, item_id):
    carrito_producto = get_object_or_404(CarritoProducto, id=item_id, carrito__usuario=request.user, carrito__tipo="factura")
    carrito_producto.delete()
    carrito_producto.carrito.actualizar_total_mayorista()
    return redirect('factura')

from django.core.mail import EmailMessage
from xhtml2pdf import pisa
from io import BytesIO

def generar_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if not pisa_status.err:
        return result.getvalue()
    return None

def enviar_correo(destinatario, asunto, mensaje, archivo, nombre_archivo):
    email = EmailMessage(asunto, mensaje, 'contacto@atlasgestion.cl', [destinatario])
    email.attach(nombre_archivo, archivo, 'application/pdf')
    email.send()

def enviar_correo_datos(destinatario, asunto, mensaje, archivo=None, nombre_archivo=''):
    email = EmailMessage(asunto, mensaje, 'contacto@atlasgestion.cl', [destinatario])
    if archivo and nombre_archivo: 
        email.attach(nombre_archivo, archivo, 'application/pdf')
    email.send()


@login_required
def buscar_correo(request):
    term = request.GET.get('term', '').strip()
    correos = PerfilClientes.objects.filter(correo__icontains=term).values('id', 'correo')[:10]

    # Crear correo automáticamente si no existe y es válido
    if not correos.exists() and '@' in term:  # Valida un formato básico de correo
        nuevo_perfil, created = PerfilClientes.objects.get_or_create(correo=term)
        correos = [{'id': nuevo_perfil.id, 'correo': nuevo_perfil.correo}]

    results = [{'id': correo['id'], 'label': correo['correo'], 'value': correo['correo']} for correo in correos]
    return JsonResponse(results, safe=False)


@login_required
def confirmar_compra_factura(request):
    if request.method == 'POST':
        medio_pago = request.POST.get('medio_pago', '')
        glosa = request.POST.get('glosa', '').strip()
        correo = request.POST.get('correo', '').strip()
                
        carrito = get_object_or_404(Carrito, usuario=request.user, tipo="factura")
        carrito_items = carrito.carritoproducto_set.all()

        if carrito_items:
            perfil_cliente = None
            if correo:
                try:
                    perfil_cliente = PerfilClientes.objects.get(correo=correo)
                except PerfilClientes.DoesNotExist:
                    perfil_cliente = PerfilClientes(correo=correo)
                    perfil_cliente.full_clean()  # Validación antes de guardar
                    perfil_cliente.save()

            # Usar la función para obtener la fecha y hora actuales
            fecha_hora_actual = obtener_hora_actual()

            # Calcular subtotal, descuentos y IVA
            subtotal = sum((item.producto.precio_mayorista / 1.19) * item.cantidad for item in carrito_items)
            descuento_total = sum(
                item.producto.precio_mayorista * item.cantidad * item.producto.descuento_mayorista / 100 for item in carrito_items
            )
            iva_total = (subtotal - descuento_total) * 0.19
            total = subtotal - descuento_total + iva_total

            # Crear la instancia de compra con los valores calculados
            compra = Compra.objects.create(
                usuario=request.user,
                subtotal=subtotal,
                descuento_total=descuento_total,
                iva_total=iva_total,
                total=total,
                nombre_staff=request.user.get_full_name(),
                correo=perfil_cliente.correo if perfil_cliente else None,
                medio_pago=medio_pago,
                glosa=glosa,
                tipo_documento='factura',
                fecha=fecha_hora_actual  # Usar la fecha y hora obtenidas 
            )
            
            # Procesar cada item en el carrito
            for item in carrito_items:
                producto = item.producto
                if producto.stock >= item.cantidad:
                    producto.stock -= item.cantidad
                    producto.save()

                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=item.cantidad,
                        precio_unitario=producto.precio_mayorista
                    )
                else:
                    messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
                    return redirect('factura')

            # Limpiar el carrito después de la compra
            carrito.carritoproducto_set.all().delete()
            carrito.actualizar_total_mayorista()

            # Enviar correo con factura en PDF
            if correo:
                template_path = 'comprobante/factura_pdf.html'
                context = {'compra': compra, 'detalles': compra.detalles.all()}
                pdf = generar_pdf(template_path, context)
                if pdf:
                    enviar_correo(correo, '¡Su compra ha sido exitosa!', 
                                  'Hola, A continuación te adjuntamos la Factura electrónica asociada a tu compra, para que esté disponible dónde y cuándo quieras. Guarda esta factura e imprímela sólo de ser necesario. ¡Cuidemos juntos nuestro planeta!.', 
                                  pdf, 'factura.pdf')

            messages.success(request, 'La compra ha sido confirmada.')
            return redirect('compra_exitosa_factura', compra_id=compra.id)
        else:
            messages.warning(request, 'El carrito está vacío.')
            return redirect('factura')


@require_POST
@login_required
def restar_producto_factura(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    carrito = get_object_or_404(Carrito, usuario=request.user, tipo="factura")
    carrito_producto = get_object_or_404(CarritoProducto, carrito=carrito, producto=producto)

    if carrito_producto.cantidad > 1:
        carrito_producto.cantidad -= 1
        carrito_producto.save()
    else:
        carrito_producto.delete()

    carrito.actualizar_total_mayorista()
    return redirect('factura')

@login_required
@permission_required('app.add_producto', raise_exception=True)
def reg_prod_factura(request):
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if request.method == "GET":
        return render(request, 'caja/reg_prod_factura.html', {})

    elif request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        stock = int(request.POST.get("stock", 0))
        precio_mayorista = int(request.POST.get("precio_mayorista", 0))

        # Manejo de Marca
        marca_id = request.POST.get("marca_id", None)
        marca_nombre = request.POST.get("marca_nombre", "").strip()
        if marca_id:
            marca = get_object_or_404(Marca, id=marca_id)
        elif marca_nombre:
            marca, _ = Marca.objects.get_or_create(nombre=marca_nombre, negocio=staff_profile.negocio)
        else:
            return JsonResponse({"success": False, "message": "Debes seleccionar o crear una marca."}, status=400)

        # Manejo de Categoría
        categoria_id = request.POST.get("categoria_id", None)
        categoria_nombre = request.POST.get("categoria_nombre", "").strip()
        if categoria_id:
            categoria = get_object_or_404(Categoria, id=categoria_id)
        elif categoria_nombre:
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre, negocio=staff_profile.negocio)
        else:
            return JsonResponse({"success": False, "message": "Debes seleccionar o crear una categoría."}, status=400)

        almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()
        if not almacen:
            return JsonResponse({"success": False, "message": "No se encontró un almacén asociado al negocio."}, status=400)

        # Crear el producto
        producto = Producto.objects.create(
            nombre=nombre,
            stock=stock,
            precio_mayorista=precio_mayorista or 0,
            descuento_mayorista=0,
            descuento=0,
            precio=0,
            marca=marca,
            categoria=categoria,
            estado="ingresado_manual",
            almacen=almacen,
        )

        # Agregar automáticamente al carrito de factura
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user, tipo="factura")
        carrito_producto, created = CarritoProducto.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 1, 'precio_unitario': producto.precio_mayorista},
        )
        if not created:
            carrito_producto.cantidad += 1
            carrito_producto.save()

        # Actualizar el total del carrito
        carrito.actualizar_total_mayorista()

        messages.success(request, f'El producto "{producto.nombre}" ha sido registrado y agregado al carrito de factura.')
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)


@login_required
@permission_required('app.change_producto', raise_exception=True)
def actualizar_descuento_factura(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    if request.method == 'POST':
        nuevo_descuento = request.POST.get('descuento', 0)  
        
        if nuevo_descuento:
            producto.descuento_mayorista = int(nuevo_descuento)
        
        producto.save()
        messages.success(request, f"El descuento de '{producto.nombre}' han sido actualizados.")


    return redirect('factura')

@login_required
def vaciar_carrito_factura(request):
    carrito = Carrito.objects.filter(usuario=request.user, tipo="factura").first()
    if carrito:
        carrito.carritoproducto_set.all().delete()  
        carrito.actualizar_total_mayorista() 
    messages.success(request, "El carrito ha sido vaciado.")
    return redirect('factura')  
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# VENTA EXISTOSA
@login_required
def compra_exitosa_boleta(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)

    detalles = compra.detalles.all()

    if 'pdf' in request.GET:
        template_path = 'comprobante/boleta_pdf.html'
        context = {
            'compra': compra,
            'detalles': detalles
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="comprobante_boleta.pdf"'

        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('Hubo un error al generar el PDF <pre>%s</pre>' % html)

        return response

    return render(request, 'comprobante/compra_exitosa_boleta.html', {
        'compra': compra,
        'detalles': detalles
    })


@login_required
def compra_exitosa_factura(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)

    detalles = compra.detalles.all()

    if 'pdf' in request.GET:
        template_path = 'comprobante/factura_pdf.html'
        context = {
            'compra': compra,
            'detalles': detalles
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="comprobante_factura.pdf"'

        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('Hubo un error al generar el PDF <pre>%s</pre>' % html)

        return response

    return render(request, 'comprobante/compra_exitosa_factura.html', {
        'compra': compra,
        'detalles': detalles
    })


def confirmar_compra_invitado(request):
    email = request.POST.get('email_invitado')
    carrito = get_object_or_404(Carrito, usuario=request.user)
    carrito_items = carrito.carritoproducto_set.all()

    if carrito_items:
        compra = Compra.objects.create(usuario=None, total=carrito.total, correo=email)

        for item in carrito_items:
            DetalleCompra.objects.create(
                compra=compra,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )

        carrito.carritoproducto_set.all().delete()
        carrito.total = 0
        carrito.save()

        return redirect('compra_exitosa', compra_id=compra.id)

    return redirect('home')


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# LOGIN Y LOGOUT
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
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio 

    if negocio.is_mayorista:
        FormularioProducto = ProductoFormMayorista
    else:
        FormularioProducto = ProductoFormMinorista

    if request.method == 'POST':
        producto_form = FormularioProducto(request.POST) 
        
        if producto_form.is_valid():
            producto = producto_form.save(commit=False)
            producto.almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first() 
            producto.save()
            return redirect('list_prod')
    else:
        producto_form = FormularioProducto() 

    return render(request, 'producto/add_prod.html', {
        'producto_form': producto_form
    })

@login_required
def buscar_categoria(request):
    term = request.GET.get('term', '').strip()

    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
    except StaffProfile.DoesNotExist:
        return JsonResponse([], safe=False)

    categorias = Categoria.objects.filter(
        nombre__icontains=term,
        negocio=negocio 
    ).values('id', 'nombre')[:10]
    
    results = [{'id': categoria['id'], 'label': categoria['nombre'], 'value': categoria['nombre']} for categoria in categorias]
    return JsonResponse(results, safe=False)

@login_required
def buscar_marca(request):
    term = request.GET.get('term', '').strip()

    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
    except StaffProfile.DoesNotExist:
        return JsonResponse([], safe=False)

    marcas = Marca.objects.filter(
        nombre__icontains=term,
        negocio=negocio
    ).values('id', 'nombre')[:10]
    
    results = [{'id': marca['id'], 'label': marca['nombre'], 'value': marca['nombre']} for marca in marcas]
    return JsonResponse(results, safe=False)

@login_required
@permission_required('app.add_producto', raise_exception=True)
def add_prod_modal(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio

    FormularioProducto = ProductoFormMayorista if negocio.is_mayorista else ProductoFormMinorista

    if request.method == 'POST':
        producto_form = FormularioProducto(request.POST)
        if producto_form.is_valid():
            producto = producto_form.save(commit=False)

            # Manejar categoría
            categoria_id = request.POST.get('categoria_id')
            categoria_nombre = request.POST.get('categoria_nombre', '').strip()
            if categoria_id:
                categoria = Categoria.objects.get(id=categoria_id)
            elif categoria_nombre:
                categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre, defaults={'negocio': negocio})
            else:
                categoria = None
            producto.categoria = categoria

            # Manejar marca
            marca_id = request.POST.get('marca_id')
            marca_nombre = request.POST.get('marca_nombre', '').strip()
            if marca_id:
                marca = Marca.objects.get(id=marca_id)
            elif marca_nombre:
                marca, _ = Marca.objects.get_or_create(nombre=marca_nombre, defaults={'negocio': negocio})
            else:
                marca = None
            producto.marca = marca

            # Manejar otros campos
            producto.descuento = producto.descuento or 0
            producto.precio = producto.precio or 0
            producto.precio_mayorista = producto.precio_mayorista or 0
            producto.descuento_mayorista = producto.descuento_mayorista or 0
            producto.almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()

            producto.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': producto_form.errors})
    else:
        producto_form = FormularioProducto()

    html_form = render_to_string(
        'producto/add_prod_modal_form.html', 
        {'producto_form': producto_form},
        request=request
    )
    return JsonResponse({'html_form': html_form})


@login_required
@permission_required('app.change_producto', raise_exception=True)
def mod_prod_modal(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio

    FormularioProducto = ProductoFormMayorista if negocio.is_mayorista else ProductoFormMinorista

    if request.method == 'POST':
        producto_form = FormularioProducto(request.POST, instance=producto)
        if producto_form.is_valid():
            producto = producto_form.save(commit=False)

            # Manejo de categoría
            categoria_id = request.POST.get('categoria_id')
            categoria_nombre = request.POST.get('categoria_nombre', '').strip()
            if categoria_id:
                try:
                    categoria = Categoria.objects.get(id=categoria_id)
                except Categoria.DoesNotExist:
                    return JsonResponse({'success': False, 'errors': {'categoria_id': 'Categoría no encontrada.'}})
            elif categoria_nombre:
                categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre, defaults={'negocio': negocio})
            else:
                categoria = None
            producto.categoria = categoria

            # Manejo de marca
            marca_id = request.POST.get('marca_id')
            marca_nombre = request.POST.get('marca_nombre', '').strip()
            if marca_id:
                try:
                    marca = Marca.objects.get(id=marca_id)
                except Marca.DoesNotExist:
                    return JsonResponse({'success': False, 'errors': {'marca_id': 'Marca no encontrada.'}})
            elif marca_nombre:
                marca, _ = Marca.objects.get_or_create(nombre=marca_nombre, defaults={'negocio': negocio})
            else:
                marca = None
            producto.marca = marca

            # Manejar otros campos
            producto.descuento = producto.descuento or 0
            producto.precio = producto.precio or 0
            producto.precio_mayorista = producto.precio_mayorista or 0
            producto.descuento_mayorista = producto.descuento_mayorista or 0
            producto.almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()

            # Guardar el producto actualizado
            producto.save()
            return JsonResponse({'success': True})
        else:
            # Retornar errores de validación
            return JsonResponse({'success': False, 'errors': producto_form.errors})
    else:
        producto_form = FormularioProducto(instance=producto)

    # Renderizar el formulario en HTML para el modal
    html_form = render_to_string('producto/mod_prod_modal_form.html', {
        'producto_form': producto_form,
        'producto': producto,
        'categoria_nombre': producto.categoria.nombre if producto.categoria else '',
        'categoria_id': producto.categoria.id if producto.categoria else '',
        'marca_nombre': producto.marca.nombre if producto.marca else '',
        'marca_id': producto.marca.id if producto.marca else '',
    }, request=request)
    return JsonResponse({'html_form': html_form})

from django.db import IntegrityError

@login_required
def list_prod(request):
    estado_filtro = request.GET.get('estado', None)
    negocio_filtro = request.GET.get('negocio', None)
    categoria_filtro = request.GET.get('categoria', None)

    error_message = None
    marca_form = MarcaForm()
    categoria_form = CategoriaForm()

    if request.user.is_superuser:
        negocios = Negocio.objects.all()
        productos = Producto.objects.exclude(estado='descontinuado').order_by(
            models.Case(
                models.When(estado='disponible', then=0),
                models.When(estado='sin_stock', then=1),
                models.When(estado='registrado_reciente', then=2),
                models.When(estado='ingresado_manual', then=3),
                default=4,
                output_field=models.IntegerField(),
            ),
            'nombre'
        )
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

        if categoria_filtro:
            try:
                categoria_filtro = int(categoria_filtro)
                productos = productos.filter(categoria_id=categoria_filtro)
            except (ValueError, Categoria.DoesNotExist):
                categoria_filtro = None

        categorias = Categoria.objects.all()
        marcas = Marca.objects.all()
    else:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
        productos = Producto.objects.filter(almacen__negocio=negocio).exclude(estado='descontinuado').order_by(
            models.Case(
                models.When(estado='disponible', then=0),
                models.When(estado='sin_stock', then=1),
                models.When(estado='registrado_reciente', then=2),
                models.When(estado='ingresado_manual', then=3),
                default=4,
                output_field=models.IntegerField(),
            ),
            'nombre'
        )
        categorias = Categoria.objects.filter(negocio=negocio)
        marcas = Marca.objects.filter(negocio=negocio)
        negocio_nombre = negocio.nombre
        negocios = None

        if estado_filtro:
            productos = productos.filter(estado=estado_filtro)

        if categoria_filtro and categoria_filtro.isdigit():
            productos = productos.filter(categoria_id=int(categoria_filtro))

        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            
            if form_type == "marca":
                # Manejo del formulario de Marca
                marca_form = MarcaForm(request.POST, negocio=negocio)
                if marca_form.is_valid():
                    try:
                        marca = marca_form.save(commit=False)
                        marca.negocio = negocio
                        marca.save()
                        messages.success(request, "Marca registrada exitosamente.")
                    except IntegrityError as e:
                        if "unique_marca_negocio" in str(e):
                            error_message = "Ya existe una marca con este nombre en tu negocio."
                        else:
                            error_message = "Ocurrió un error al registrar la marca. Por favor, inténtalo nuevamente."
                else:
                    error_message = "Error en el formulario de marca. Revisa los datos ingresados."

            elif form_type == 'categoria':
                # Manejo del formulario de Categoría
                categoria_form = CategoriaForm(request.POST, negocio=negocio)
                if categoria_form.is_valid():
                    try:
                        categoria = categoria_form.save(commit=False)
                        categoria.negocio = negocio
                        categoria.save()
                        messages.success(request, "Categoría registrada exitosamente.")
                    except IntegrityError as e:
                        if "unique_categoria_negocio" in str(e):
                            error_message = "Ya existe una categoría con este nombre en tu negocio."
                        else:
                            error_message = "Ocurrió un error al registrar la categoría. Por favor, inténtalo nuevamente."
                else:
                    error_message = "Error en el formulario de categoría. Revisa los datos ingresados."

    return render(request, 'producto/list_prod.html', {
        'productos': productos,
        'estado_filtro': estado_filtro,
        'negocios': negocios,
        'negocio_filtro': negocio_filtro,
        'negocio_nombre': negocio_nombre,
        'categorias': categorias,
        'marcas': marcas,
        'categoria_filtro': categoria_filtro,
        'marca_form': marca_form,
        'categoria_form': categoria_form,
        'error_message': error_message,
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
        
        # Actualizar el estado del producto según el stock restante
        if producto.stock <= 0:
            # Si el stock es 0 o menor, cambiar a "sin_stock"
            producto.estado = 'sin_stock'
        elif producto.stock > 0:
            # Si aún tiene stock, dejarlo en "disponible"
            producto.estado = 'disponible'
        
        # Guardar los cambios en el producto
        producto.save()

        # Mostrar mensaje de éxito
        messages.success(request, f"Devolución del lote {lote} registrada correctamente.")
        return redirect('list_prod')

    return render(request, 'producto/devolver_prod.html', {'producto': producto})

@login_required
@permission_required('app.change_producto', raise_exception=True)
def mod_prod(request, producto_id):
    producto = get_object_or_404(Producto, producto_id=producto_id)
    
    # Verificar que el producto pertenece al negocio del staff
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio  # Obtener el negocio del usuario

    if producto.almacen.negocio != negocio:
        return HttpResponseForbidden("No tienes permiso para modificar este producto.")

    # Determinar el formulario basado en el tipo de negocio
    if negocio.is_mayorista:
        FormularioProducto = ProductoFormMayorista
    else:
        FormularioProducto = ProductoFormMinorista

    if request.method == 'POST':
        producto_form = FormularioProducto(request.POST, instance=producto)

        if producto_form.is_valid():
            producto = producto_form.save()

            # Si el stock es 0, marcar como "sin_stock"
            if producto.stock == 0:
                producto.estado = 'sin_stock'
            producto.save()

            return redirect('list_prod')
    else:
        producto_form = FormularioProducto(instance=producto)

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
    return render(request, 'comprobante/pay_error.html')

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
    staff_profile = StaffProfile.objects.get(user=request.user)
    
    entradas = EntradaBodega.objects.filter(bodega__negocio=staff_profile.negocio).order_by('-fecha_recepcion')

    return render(request, 'bodega/historial_bodega.html', {'entradas': entradas})


@login_required
@permission_required('app.add_entradabodega', raise_exception=True)
def operaciones_bodega_modal(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio

    # Obtener el almacen una sola vez
    almacen = Almacen.objects.filter(negocio=negocio).first()

    EntradaBodegaProductoFormSet = modelformset_factory(
        EntradaBodegaProducto,
        form=EntradaBodegaProductoForm,
        extra=1,
    )

    if request.method == 'POST':
        entrada_form = EntradaBodegaForm(request.POST)
        producto_formset = EntradaBodegaProductoFormSet(
            request.POST,
            queryset=EntradaBodegaProducto.objects.none(),
            form_kwargs={'almacen': almacen}
        )

        if entrada_form.is_valid() and producto_formset.is_valid():
            with transaction.atomic():
                entrada_bodega = entrada_form.save(commit=False)
                entrada_bodega.bodega = almacen
                entrada_bodega.save()

                for producto_form in producto_formset:
                    if producto_form.cleaned_data:
                        entrada_producto = producto_form.save(commit=False)
                        entrada_producto.entrada_bodega = entrada_bodega
                        entrada_producto.save()

                        producto = entrada_producto.producto
                        producto.stock += entrada_producto.cantidad_recibida
                        producto.save()

            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('bodega/operaciones_bodega_modal_form.html', {
                'entrada_form': entrada_form,
                'producto_formset': producto_formset,
            }, request=request)
            return JsonResponse({'html_form': html_form})

    else:
        entrada_form = EntradaBodegaForm()
        producto_formset = EntradaBodegaProductoFormSet(
            queryset=EntradaBodegaProducto.objects.none(),
            form_kwargs={'almacen': almacen}
        )

        html_form = render_to_string('bodega/operaciones_bodega_modal_form.html', {
            'entrada_form': entrada_form,
            'producto_formset': producto_formset,
        }, request=request)
        return JsonResponse({'html_form': html_form})


@login_required
@permission_required('app.add_entradabodega', raise_exception=True)
def operaciones_bodega(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    almacen = Almacen.objects.filter(negocio=staff_profile.negocio).first()

    productos = Producto.objects.filter(almacen=almacen)  # Filtrar productos por almacén
    proveedores = Proveedor.objects.filter(negocio=staff_profile.negocio)  # Filtrar proveedores por negocio

    EntradaBodegaProductoFormSet = modelformset_factory(
        EntradaBodegaProducto,
        form=EntradaBodegaProductoForm,
        extra=1,
    )

    if request.method == 'POST':
        entrada_form = EntradaBodegaForm(request.POST, staff_profile=staff_profile)
        producto_formset = EntradaBodegaProductoFormSet(
            request.POST,
            queryset=EntradaBodegaProducto.objects.none(),
            form_kwargs={'almacen': almacen}
        )
        if entrada_form.is_valid() and producto_formset.is_valid():
            with transaction.atomic():
                # Guardar el formulario de EntradaBodega
                entrada_bodega = entrada_form.save(commit=False)
                entrada_bodega.fecha_recepcion = request.POST.get("fecha_recepcion")  # Obtener fecha de recepción del POST
                entrada_bodega.bodega = almacen  # Asignar el almacén al campo bodega
                entrada_bodega.save()

                # Guardar cada formulario de producto asociado a esta entrada de bodega
                for producto_form in producto_formset:
                    if producto_form.cleaned_data:  # Verificar que el formulario contiene datos
                        entrada_producto = producto_form.save(commit=False)
                        entrada_producto.entrada_bodega = entrada_bodega
                        entrada_producto.save()

                        # Actualizar el stock del producto
                        producto = entrada_producto.producto
                        producto.stock += entrada_producto.cantidad_recibida
                        producto.save()

                messages.success(request, 'Entrada de bodega y productos registrados exitosamente.')
            return redirect('operaciones_bodega')
    else:
        entrada_form = EntradaBodegaForm(staff_profile=staff_profile)
        producto_formset = EntradaBodegaProductoFormSet(
            queryset=EntradaBodegaProducto.objects.none(),
            form_kwargs={'almacen': almacen}
        )
    return render(request, 'bodega/operaciones_bodega.html', {
        'entrada_form': entrada_form,
        'producto_formset': producto_formset,
        'productos': productos,
        'proveedores': proveedores,
    })


@login_required
@permission_required('app.view_entradabodega', raise_exception=True)
def listar_entradas_bodega(request):
    # Obtener el perfil del staff y el negocio relacionado
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio

    # Filtrar entradas de bodega por el almacén del negocio
    entradas = EntradaBodega.objects.filter(bodega__negocio=negocio).order_by('-fecha_recepcion')

    # Renderizar el template con las entradas filtradas
    return render(request, 'bodega/lista_entradas_bodega.html', {
        'entradas': entradas,
    })



@login_required
@permission_required('app.view_entradabodega', raise_exception=True)
def detalle_entrada_bodega(request, entrada_id):
    # Obtener la entrada de bodega específica
    entrada = get_object_or_404(EntradaBodega, id=entrada_id)

    # Obtener los productos asociados a esta entrada, incluyendo las cantidades devueltas
    productos = EntradaBodegaProducto.objects.filter(entrada_bodega=entrada).annotate(
        subtotal=ExpressionWrapper(F('cantidad_recibida') * F('precio_unitario'), output_field=IntegerField()),
        cantidad_devuelta=Sum(
            'producto__devoluciones__cantidad_devuelta',
            filter=Q(producto__devoluciones__entrada_bodega=entrada),
            default=0
        ),
    ).annotate(
        cantidad_restante=F('cantidad_recibida') - F('cantidad_devuelta'),
        estado_devolucion=Case(
            When(cantidad_devuelta=0, then=Value('Sin Devolución')),
            When(cantidad_restante=0, then=Value('Devuelto Totalmente')),
            default=Value('Devuelto Parcialmente'),
            output_field=CharField(),
        )
    ).order_by('producto__nombre')

    # Contar el número total de productos
    total_productos = productos.count()
    # Calcular el total general
    total_general = productos.aggregate(total=Sum('subtotal'))['total'] or 0

    return render(request, 'bodega/detalle_entrada_bodega.html', {
        'entrada': entrada,
        'productos': productos,
        'total_productos': total_productos,
        'total_general': total_general,
    })



@login_required
@permission_required('app.view_entradabodega', raise_exception=True)
def detalle_prod_entrada_bodega(request, entrada_id, producto_id):
    # Obtener la entrada de bodega específica
    entrada = get_object_or_404(EntradaBodega, id=entrada_id)
    # Obtener el producto específico asociado a esta entrada
    producto_entrada = get_object_or_404(
        EntradaBodegaProducto,
        entrada_bodega=entrada,
        producto__producto_id=producto_id
    )
    
    return render(request, 'bodega/detalle_prod_entrada_bodega.html', {
        'entrada': entrada,
        'producto_entrada': producto_entrada,
    })


@login_required
@permission_required('app.add_productosdevueltos', raise_exception=True)
def devolver_factura(request, entrada_id):
    entrada = get_object_or_404(EntradaBodega, id=entrada_id)
    
    # Obtener los productos asociados a esta entrada
    productos_entrada = Producto.objects.filter(
        producto_id__in=EntradaBodegaProducto.objects.filter(entrada_bodega=entrada).values_list('producto_id', flat=True)
    )

    # Configuración del Formset con can_delete=True para permitir eliminar formularios
    DevolucionFormSet = modelformset_factory(
        ProductosDevueltos,
        form=DevolucionProductoForm,
        extra=1,
        #can_delete=True
    )

    if request.method == 'POST':
        formset = DevolucionFormSet(
            request.POST,
            queryset=ProductosDevueltos.objects.none(),
            form_kwargs={'productos_queryset': productos_entrada}
        )

        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        devolucion = form.save(commit=False)
                        devolucion.entrada_bodega = entrada
                        devolucion.proveedor = entrada.proveedor

                        # Verificar cantidad disponible
                        producto_entrada = EntradaBodegaProducto.objects.get(
                            entrada_bodega=entrada,
                            producto=devolucion.producto
                        )
                        cantidad_devuelta_anterior = ProductosDevueltos.objects.filter(
                            entrada_bodega=entrada,
                            producto=devolucion.producto
                        ).aggregate(total=Sum('cantidad_devuelta'))['total'] or 0
                        cantidad_disponible = producto_entrada.cantidad_recibida - cantidad_devuelta_anterior

                        if devolucion.cantidad_devuelta > cantidad_disponible:
                            messages.error(
                                request,
                                f"La cantidad a devolver de {devolucion.producto.nombre} excede el disponible."
                            )
                            return redirect('devolver_factura', entrada_id=entrada.id)

                        devolucion.save()
                        devolucion.producto.stock -= devolucion.cantidad_devuelta
                        devolucion.producto.actualizar_estado()
                        devolucion.producto.save()

                messages.success(request, "Devolución registrada exitosamente.")
            return redirect('detalle_entrada_bodega', entrada_id=entrada.id)
    else:
        formset = DevolucionFormSet(
            queryset=ProductosDevueltos.objects.none(),
            form_kwargs={'productos_queryset': productos_entrada}
        )

    return render(request, 'bodega/devolver_factura.html', {
        'entrada': entrada,
        'formset': formset,
    })

@login_required
@permission_required('app.view_productosdevueltos', raise_exception=True)
def historial_devoluciones(request):
    devoluciones = ProductosDevueltos.objects.select_related('producto', 'entrada_bodega', 'proveedor').order_by('-fecha_devolucion')

    return render(request, 'bodega/historial_devoluciones.html', {
        'devoluciones': devoluciones,
    })


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models.functions import TruncDay, TruncMonth
from django.db.models import Sum, Avg
import matplotlib
matplotlib.use('Agg')  # Usar un backend no interactivo para evitar problemas en el servidor

import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models import Sum, Avg
from django.db.models.functions import TruncDay, TruncMonth
from django.shortcuts import render
from .models import Compra, DetalleCompra, StaffProfile
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models import Sum, Avg, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para evitar errores en servidores
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDay
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

@login_required
@staff_member_required
def mi_negocio(request):
    staff_profile = StaffProfile.objects.get(user=request.user)
    negocio = staff_profile.negocio

    # KPIs
    total_ventas = Compra.objects.filter(usuario__staffprofile__negocio=negocio).aggregate(Sum('total'))['total__sum'] or 0
    promedio_ventas_diario = Compra.objects.filter(usuario__staffprofile__negocio=negocio).annotate(
        dia=TruncDay('fecha')
    ).values('dia').annotate(total_dia=Sum('total')).aggregate(Avg('total_dia'))['total_dia__avg'] or 0
    producto_mas_vendido = DetalleCompra.objects.filter(
        compra__usuario__staffprofile__negocio=negocio
    ).values('producto__nombre').annotate(cantidad_total=Sum('cantidad')).order_by('-cantidad_total').first()

    # Generar gráficos solo si hay datos
    grafico_producto_mas_vendido = None
    if producto_mas_vendido:
        productos = [producto_mas_vendido['producto__nombre']]
        cantidades = [producto_mas_vendido['cantidad_total']]
        fig, ax = plt.subplots()
        ax.bar(productos, cantidades, color='skyblue')
        ax.set_title('Producto Más Vendido')
        ax.set_ylabel('Cantidad')
        ax.set_xlabel('Producto')
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafico_producto_mas_vendido = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close(fig)

    grafico_ventas_dia = None
    ventas_por_dia = Compra.objects.filter(usuario__staffprofile__negocio=negocio).annotate(
        dia=TruncDay('fecha')
    ).values('dia').annotate(total_ventas=Sum('total')).order_by('dia')
    if ventas_por_dia.exists():
        dias = [venta['dia'].strftime('%Y-%m-%d') for venta in ventas_por_dia]
        ventas = [venta['total_ventas'] for venta in ventas_por_dia]
        fig, ax = plt.subplots()
        ax.bar(dias, ventas, color='green')
        ax.set_title('Ventas Totales por Día')
        ax.set_ylabel('Total Ventas')
        ax.set_xlabel('Días')
        plt.xticks(rotation=45, ha='right')
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafico_ventas_dia = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close(fig)

    context = {
        'total_ventas': total_ventas,
        'promedio_ventas_diario': promedio_ventas_diario,
        'producto_mas_vendido': producto_mas_vendido,
        'grafico_producto_mas_vendido': grafico_producto_mas_vendido,
        'grafico_ventas_dia': grafico_ventas_dia,
    }

    return render(request, 'business/mi_negocio.html', context)



#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE STAFF
@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_staff(request):
    grupos = Group.objects.all()  # Cargar los grupos disponibles una sola vez

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = StaffProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Crear usuario
            user = user_form.save(commit=False)
            user.is_staff = True
            user.is_superuser = False
            user.is_active = True
            user.save()

            # Asignar grupo al usuario
            grupo_seleccionado = request.POST.get('grupo')
            if grupo_seleccionado:
                grupo = Group.objects.get(id=grupo_seleccionado)
                user.groups.add(grupo)

            # Crear perfil de staff
            staff_profile = profile_form.save(commit=False)
            staff_profile.user = user
            staff_profile.save()

            return redirect('list_staff')
    else:
        user_form = UserForm()
        profile_form = StaffProfileForm()

    return render(request, 'administration/staff/register_staff.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'grupos': grupos,  # Pasar todos los grupos disponibles
        'grupo_actual': None  # Ningún grupo está asignado aún
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
@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_admin(request):
    admin_list = User.objects.filter(is_superuser=True) 
    return render(request, 'administration/admin/list_admin.html', {'admin_list': admin_list})

# Registrar nuevo administrador
@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_admin(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = StaffProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Crear el usuario administrador
            user = user_form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()

            # Crear y vincular el perfil de Staff
            staff_profile = profile_form.save(commit=False)
            staff_profile.user = user
            staff_profile.save()

            return redirect('list_admin')
    else:
        user_form = UserForm()
        profile_form = StaffProfileForm()

    return render(request, 'administration/admin/register_admin.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mod_admin_profile(request, admin_id):
    admin = get_object_or_404(User, pk=admin_id, is_superuser=True)
    staff_profile = get_object_or_404(StaffProfile, user=admin)

    grupos = Group.objects.all()

    if request.method == 'POST':
        profile_form = StaffProfileForm(request.POST, instance=staff_profile)
        if profile_form.is_valid():
            profile_form.save()

            # Asignar grupo al usuario
            grupo_seleccionado = request.POST.get('grupo')
            if grupo_seleccionado:
                grupo = Group.objects.get(id=grupo_seleccionado)
                admin.groups.clear()
                admin.groups.add(grupo)
            return redirect('list_admin')
    else:
        profile_form = StaffProfileForm(instance=staff_profile)

    return render(request, 'administration/admin/mod_admin_profile.html', {
        'profile_form': profile_form,
        'admin': admin,
        'grupos': grupos,
        'grupo_actual': admin.groups.first()
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
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
        StaffProfile.objects.filter(user=user).delete()
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
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            # Enviar correo de confirmación
            asunto = "¡Tu contraseña ha sido actualizada!"
            mensaje = (
                "Hola,\n\n"
                "Tu contraseña ha sido actualizada exitosamente. Si no realizaste este cambio, por favor "
                "contacta al jefe de tu negocio o informa de actividad sospechosa inmediatamente.\n\n"
                "Gracias por preferir Atlas Gestión."
            )
            enviar_correo_datos(
                destinatario=user.email,
                asunto=asunto,
                mensaje=mensaje
            )
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
#Fx mixta - lista y creación negocio/almacén
@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_negocios(request):
    negocios = Negocio.objects.all()  # Lista de negocios para mostrar

    if request.method == 'POST':
        form = NegocioForm(request.POST)
        if form.is_valid():
            # Crear el negocio pero no guardarlo aún
            negocio = form.save(commit=False)
            
            # Asignar las relaciones de región, provincia y comuna
            region_id = request.POST.get('region')
            provincia_id = request.POST.get('provincia')
            comuna_id = request.POST.get('comuna')
            
            negocio.region_id = region_id
            negocio.provincia_id = provincia_id
            negocio.comuna_id = comuna_id
            
            # Guardar el negocio
            negocio.save()
            
            almacen_direccion = form.cleaned_data['almacen_direccion']
            Almacen.objects.create(direccion=almacen_direccion, negocio=negocio)
            
            messages.success(request, 'Negocio y almacén creados exitosamente.')
            return redirect('list_negocios')
        else:
            for field, errors in form.errors.items():
                messages.error(request, f"Error en el campo {field}: {', '.join(errors)}")
            # Manejo de errores específicos
            if 'API' in str(errors):
                messages.error(request, "Hubo un problema al validar el RUT. Intenta nuevamente más tarde.")

    else:
        form = NegocioForm()

    regiones = Region.objects.all()

    return render(request, 'administration/negocio/list_negocios.html', {
        'form': form,
        'negocios': negocios,
        'regions': regiones,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mod_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, pk=negocio_id)
    almacen = Almacen.objects.filter(negocio=negocio).first() 

            
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

    regiones = Region.objects.all()

    return render(request, 'administration/negocio/mod_negocio.html', {
        'form': form,
        'regions': regiones,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def erase_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, pk=negocio_id)
    
    if request.method == 'POST':
        negocio.delete()
        return redirect('list_negocios')

    return render(request, 'administration/negocio/erase_negocio.html', {'negocio': negocio})

# Método para cambiar el estado del negocio y las cuentas afiliadas
def cambiar_estado_negocio_y_cuentas(negocio_id, estado):
    try:
        negocio = Negocio.objects.get(id=negocio_id)
        negocio.is_active = estado  # Cambiar el estado del negocio
        negocio.save()

        # Cambiar el estado de las cuentas afiliadas
        usuarios_afiliados = User.objects.filter(staffprofile__negocio=negocio)
        usuarios_afiliados.update(is_active=estado)  # Sincronizar el estado con el negocio

        return True
    except Negocio.DoesNotExist:
        return False

@login_required
@user_passes_test(lambda u: u.is_superuser)
def cambiar_estado_negocio(request, negocio_id):
    try:
        negocio = Negocio.objects.get(id=negocio_id)
        nuevo_estado = not negocio.is_active  # Alternar el estado actual
        if cambiar_estado_negocio_y_cuentas(negocio_id, nuevo_estado):
            if nuevo_estado:
                messages.success(request, 'Negocio y cuentas afiliadas activados.')
            else:
                messages.success(request, 'Negocio y cuentas afiliadas inactivados.')
        else:
            messages.error(request, 'No se pudo cambiar el estado del negocio.')
    except Negocio.DoesNotExist:
        messages.error(request, 'El negocio no existe.')

    return redirect('list_negocios')


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE PROVEEDORES
@login_required
@permission_required('app.add_proveedor', raise_exception=True)
def add_proveedor(request):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio

        if request.method == 'POST':
            proveedor_form = ProveedorForm(request.POST)

            if proveedor_form.is_valid():
                proveedor = proveedor_form.save(commit=False)

                # Asignar las relaciones de región, provincia y comuna
                region_id = request.POST.get('region')
                provincia_id = request.POST.get('provincia')
                comuna_id = request.POST.get('comuna')

                proveedor.region = Region.objects.get(id=region_id) if region_id else None
                proveedor.provincia = Provincia.objects.get(id=provincia_id) if provincia_id else None
                proveedor.comuna = Comuna.objects.get(id=comuna_id) if comuna_id else None

                proveedor.negocio = negocio
                proveedor.save()

                messages.success(request, "Proveedor registrado exitosamente.")
                return redirect('list_proveedores')
        else:
            proveedor_form = ProveedorForm()
        
        regiones = Region.objects.all()

        return render(request, 'administration/proveedor/add_proveedor.html', {
            'proveedor_form': proveedor_form,
            'regions': regiones,
        })
    except StaffProfile.DoesNotExist:
        return HttpResponseForbidden("No tienes un perfil asociado.")


@login_required
@permission_required('app.view_proveedor', raise_exception=True)
def list_proveedores(request):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio

        if request.user.is_superuser:
            negocios = Negocio.objects.all()
            proveedores = Proveedor.objects.all()
        else:
            negocios = None
            proveedores = Proveedor.objects.filter(negocio=negocio)

        negocio_filtro = request.GET.get('negocio', None)
        negocio_nombre = None
        if request.user.is_superuser and negocio_filtro:
            try:
                negocio_filtro = int(negocio_filtro)
                proveedores = proveedores.filter(negocio_id=negocio_filtro)
                negocio_nombre = Negocio.objects.get(id=negocio_filtro).nombre
            except (ValueError, Negocio.DoesNotExist):
                negocio_filtro = None

        if request.method == 'POST':
            form = ProveedorForm(request.POST)
            if form.is_valid():
                proveedor = form.save(commit=False)

                # Asignar las relaciones de región, provincia y comuna
                region_id = request.POST.get('region')
                provincia_id = request.POST.get('provincia')
                comuna_id = request.POST.get('comuna')

                proveedor.region = Region.objects.get(id=region_id) if region_id else None
                proveedor.provincia = Provincia.objects.get(id=provincia_id) if provincia_id else None
                proveedor.comuna = Comuna.objects.get(id=comuna_id) if comuna_id else None

                proveedor.negocio = negocio  
                proveedor.save()
                messages.success(request, "Proveedor registrado exitosamente.")
                return redirect('list_proveedores')
        else:
            form = ProveedorForm()

            regiones = Region.objects.all()

        return render(request, 'administration/proveedor/list_proveedores.html', {
            'proveedores': proveedores,
            'form': form,
            'negocios': negocios,
            'negocio_filtro': negocio_filtro,
            'negocio_nombre': negocio_nombre,
            'regions': regiones,
        })
    except StaffProfile.DoesNotExist:
        return HttpResponseForbidden("No tienes un perfil asociado.")

@login_required
@permission_required('app.change_proveedor', raise_exception=True)
def mod_proveedor(request, proveedor_id):
    try:
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        if request.method == 'POST':
            proveedor_form = ProveedorForm(request.POST, instance=proveedor)

            if proveedor_form.is_valid():
                proveedor = proveedor_form.save(commit=False)

                region_id = request.POST.get('region')
                provincia_id = request.POST.get('provincia')
                comuna_id = request.POST.get('comuna')

                proveedor.region = Region.objects.get(id=region_id) if region_id else None
                proveedor.provincia = Provincia.objects.get(id=provincia_id) if provincia_id else None
                proveedor.comuna = Comuna.objects.get(id=comuna_id) if comuna_id else None

                proveedor.save()

                messages.success(request, "Proveedor modificado exitosamente.")
                return redirect('list_proveedores')
        else:
            proveedor_form = ProveedorForm(instance=proveedor)
            regiones = Region.objects.all()

        return render(request, 'administration/proveedor/mod_proveedor.html', {
            'proveedor_form': proveedor_form,
            'regions': regiones,
            'proveedor': proveedor,
        })
    except Proveedor.DoesNotExist:
        return HttpResponseForbidden("Proveedor no encontrado.")

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
    try:
        # Determinar el negocio del usuario
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio

        if request.user.is_superuser:
            negocios = Negocio.objects.all()
            categorias = Categoria.objects.all()
        else:
            negocios = None
            categorias = Categoria.objects.filter(negocio=negocio)

        negocio_filtro = request.GET.get('negocio', None)
        negocio_nombre = None
        if request.user.is_superuser and negocio_filtro:
            try:
                negocio_filtro = int(negocio_filtro)
                categorias = categorias.filter(negocio_id=negocio_filtro)
                negocio_nombre = Negocio.objects.get(id=negocio_filtro).nombre
            except (ValueError, Negocio.DoesNotExist):
                negocio_filtro = None

        if request.method == 'POST':
            form = CategoriaForm(request.POST)
            if form.is_valid():
                categoria = form.save(commit=False)
                categoria.negocio = negocio
                categoria.save()
                messages.success(request, "Categoría registrada exitosamente.")
                return redirect('list_categorias')
        else:
            form = CategoriaForm()

        return render(request, 'categorias/list_categorias.html', {
            'categorias': categorias,
            'form': form,
            'negocios': negocios,
            'negocio_filtro': negocio_filtro,
            'negocio_nombre': negocio_nombre,
        })
    except StaffProfile.DoesNotExist:
        return HttpResponseForbidden("No tienes un perfil asociado.")


@login_required
@permission_required('app.add_categoria', raise_exception=True)
def add_categoria(request):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio

        if request.method == 'POST':
            form = CategoriaForm(request.POST)
            if form.is_valid():
                categoria = form.save(commit=False)
                categoria.negocio = negocio  
                categoria.save()
                messages.success(request, "Categoría registrada exitosamente.")
                return redirect('list_categorias')
        else:
            form = CategoriaForm()

        return render(request, 'categorias/add_categoria.html', {
            'form': form,
        })
    except StaffProfile.DoesNotExist:
        return HttpResponseForbidden("No tienes un perfil asociado.")


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
            return redirect('list_prod')
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
        return redirect('list_prod')

    return render(request, 'categorias/erase_categoria.html', {'categoria': categoria})

#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#MANEJO DE MARCAS
@login_required
@permission_required('app.add_marca', raise_exception=True)
def add_marca(request):
    try:
        # Determinar el negocio del usuario
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio

        error_message = None  # Variable para almacenar el mensaje de error

        if request.method == 'POST':
            form = MarcaForm(request.POST, negocio=negocio)
            if form.is_valid():
                try:
                    marca = form.save(commit=False)
                    marca.negocio = negocio  # Asociar la marca al negocio
                    marca.save()
                    messages.success(request, "Marca registrada exitosamente.")
                    return redirect('list_marcas')
                except IntegrityError as e:
                    # Captura el error de unicidad
                    if 'unique_marca_negocio' in str(e):  # Verifica el nombre de la restricción
                        error_message = "Ya existe una marca con este nombre en tu negocio."
                    else:
                        error_message = "Ocurrió un error al guardar la marca. Intenta nuevamente."
            else:
                error_message = "Error en el formulario. Verifica los datos ingresados."
        else:
            form = MarcaForm(negocio=negocio)

        # Renderiza la plantilla con el formulario y el mensaje de error (si existe)
        return render(request, 'marca/add_marca.html', {
            'form': form,
            'error_message': error_message,  # Pasamos el mensaje de error al contexto
        })
    except StaffProfile.DoesNotExist:
        return HttpResponseForbidden("No tienes un perfil asociado.")

@login_required
def list_marcas(request):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes un negocio asignado.")
        return redirect('home')

    marcas = Marca.objects.filter(negocio=negocio)

    if request.method == 'POST':
        marca_form = MarcaForm(request.POST, negocio=negocio)
        if marca_form.is_valid():
            nueva_marca = marca_form.save(commit=False)
            nueva_marca.negocio = negocio
            nueva_marca.save()
            messages.success(request, "Marca registrada exitosamente.")
            return redirect('list_marcas')
        else:
            messages.error(request, "Error al registrar la marca. Verifica los datos.")
    else:
        marca_form = MarcaForm(negocio=negocio)

    return render(request, 'marca/list_marcas.html', {
        'marcas': marcas,
        'marca_form': marca_form,
    })


@login_required
def mod_marca(request, marca_id):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes un negocio asignado.")
        return redirect('home')

    marca = get_object_or_404(Marca, id=marca_id, negocio=negocio)

    if request.method == 'POST':
        form = MarcaForm(request.POST, instance=marca, negocio=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, "Marca modificada exitosamente.")
            return redirect('list_marcas')
        else:
            messages.error(request, "Error al modificar la marca. Verifica los datos.")
    else:
        form = MarcaForm(instance=marca, negocio=negocio)

    return render(request, 'marca/mod_marca.html', {'form': form, 'marca': marca})



@login_required
def erase_marca(request, marca_id):
    try:
        staff_profile = StaffProfile.objects.get(user=request.user)
        negocio = staff_profile.negocio
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes un negocio asignado.")
        return redirect('home')

    marca = get_object_or_404(Marca, id=marca_id, negocio=negocio)

    if request.method == 'POST':
        marca.delete()
        messages.success(request, "Marca eliminada exitosamente.")
        return redirect('list_prod')

    return render(request, 'marca/erase_marca.html', {'marca': marca})


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# MANEJO DE TIPO DE PRODUCTO
@login_required
@permission_required('app.view_tipoproducto', raise_exception=True)
def list_tipos_producto(request):
    tipos = TipoProducto.objects.all()
    return render(request, 'tipoproducto/list_tipos_producto.html', {'tipos': tipos})

@login_required
@permission_required('app.add_tipoproducto', raise_exception=True)
def add_tipo_producto(request):
    if request.method == 'POST':
        form = TipoProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_tipos_producto')
    else:
        form = TipoProductoForm()
    return render(request, 'tipoproducto/add_tipo_producto.html', {'form': form})

@login_required
@permission_required('app.change_tipoproducto', raise_exception=True)
def mod_tipo_producto(request, tipo_id):
    tipo = get_object_or_404(TipoProducto, id=tipo_id)
    if request.method == 'POST':
        form = TipoProductoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('list_tipos_producto')
    else:
        form = TipoProductoForm(instance=tipo)
    return render(request, 'tipoproducto/mod_tipo_producto.html', {'form': form, 'tipo': tipo})

@login_required
@permission_required('app.delete_tipoproducto', raise_exception=True)
def erase_tipo_producto(request, tipo_id):
    tipo = get_object_or_404(TipoProducto, id=tipo_id)
    if request.method == 'POST':
        tipo.delete()
        return redirect('list_tipos_producto')
    return render(request, 'tipoproducto/erase_tipo_producto.html', {'tipo': tipo})


#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# MANEJO DE PERFIL DE CLIENTES
@login_required
def add_cliente(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        if correo:
            PerfilClientes.objects.get_or_create(correo=correo)
            return JsonResponse({'success': True, 'message': 'Cliente registrado'})
        return JsonResponse({'success': False, 'message': 'Correo inválido'})

@login_required
def list_clientes(request):
    clientes = PerfilClientes.objects.all()
    return render(request, 'administration/cuentas/list_cliente_modal.html', {'clientes': clientes})

@login_required
def mod_cliente(request, cliente_id):
    cliente = get_object_or_404(PerfilClientes, id=cliente_id)

    if request.method == 'POST':
        cliente_form = PerfilClientesForm(request.POST, instance=cliente)
        if cliente_form.is_valid():
            cliente_form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'html_form': render_to_string('administration/cuentas/mod_cliente_modal.html', {'cliente_form': cliente_form, 'cliente': cliente}, request=request)
            })
    else:
        cliente_form = PerfilClientesForm(instance=cliente)

    html_form = render_to_string('administration/cuentas/mod_cliente_modal.html', {
        'cliente_form': cliente_form,
        'cliente': cliente,
    }, request=request)
    return JsonResponse({'html_form': html_form})

@login_required
def erase_cliente(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(PerfilClientes, id=cliente_id)
        cliente.delete()
        return JsonResponse({'success': True, 'message': 'Cliente eliminado'})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# MANEJOS DE JEFE DE NEGOCIO - BOSS
# Registrar un nuevo staff (solo jefe de negocio)
@login_required
@jefe_required
def register_staff_for_boss(request):
    jefe_profile = StaffProfile.objects.get(user=request.user)

    if request.method == 'POST':
        user_form = UserForBossForm(request.POST)
        profile_form = StaffProfileForBossForm(request.POST)

        try:
            if user_form.is_valid() and profile_form.is_valid():
                # Crear usuario con contraseña generada
                user = user_form.save(commit=False)
                user.is_staff = True

                # Generar contraseña y asignarla en los campos de confirmación
                passw = gen_password()
                user.set_password(passw)
                user_form.cleaned_data['password1'] = passw
                user_form.cleaned_data['password2'] = passw

                user.save()

                # Asignar grupo
                grupo_seleccionado = request.POST.get('grupo')
                if grupo_seleccionado:
                    grupo = Group.objects.get(id=grupo_seleccionado)
                    user.groups.add(grupo)

                # Crear perfil del staff
                staff_profile = profile_form.save(commit=False)
                staff_profile.user = user
                staff_profile.negocio = jefe_profile.negocio
                staff_profile.save()

                # Enviar credenciales al correo
                asunto = 'Credenciales de acceso'
                mensaje = (
                    f"Hola {user.first_name},\n\n"
                    f"Tu cuenta ha sido creada exitosamente.\n\n"
                    f"Credenciales de acceso:\n"
                    f"Usuario: {user.username}\n"
                    f"Contraseña: {passw}\n\n"
                    f"Recuerda cambiar tu contraseña en el primer inicio de sesión."
                )
                destinatarios = [user.email, request.user.email]

                for destinatario in destinatarios:
                    enviar_correo_datos(destinatario, asunto, mensaje)  

                return redirect('list_staff_for_boss')
            else:
                # Mostrar errores de validación
                raise ValueError("Los formularios no son válidos. Por favor, verifica los datos ingresados.")
        except Exception as e:
            # Capturar errores y enviarlos al template para su visualización
            error_message = str(e)
            return render(request, 'administration/for_boss/register_staff_for_boss.html', {
                'user_form': user_form,
                'profile_form': profile_form,
                'grupos': Group.objects.filter(name__in=['staff_bodega', 'staff_vendedor']),
                'error_message': error_message,
            })
    else:
        user_form = UserForBossForm()
        profile_form = StaffProfileForBossForm()

    return render(request, 'administration/for_boss/register_staff_for_boss.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'grupos': Group.objects.filter(name__in=['staff_bodega', 'staff_vendedor']),
    })




@login_required
@jefe_required
def mod_staff_profile_for_boss(request, staff_id):
    jefe_profile = StaffProfile.objects.get(user=request.user)

    # Validar que el usuario pertenece al negocio del jefe
    user = get_object_or_404(User, pk=staff_id)
    staff_profile = get_object_or_404(StaffProfile, user=user, negocio=jefe_profile.negocio)

    grupos = Group.objects.all()

    if request.method == 'POST':
        profile_form = StaffProfileForBossForm(request.POST, instance=staff_profile)

        if profile_form.is_valid():
            # Guardar cambios en el perfil
            profile_form.save()

            # Actualizar el grupo asignado al usuario
            grupo_seleccionado = request.POST.get('grupo')
            if grupo_seleccionado:
                grupo = get_object_or_404(Group, id=grupo_seleccionado)
                user.groups.clear()  # Limpiar todos los grupos actuales
                user.groups.add(grupo)  # Asignar el nuevo grupo

            return redirect('list_staff_for_boss')  # Redirigir a la lista de staff del jefe
    else:
        profile_form = StaffProfileForBossForm(instance=staff_profile)

    return render(request, 'administration/for_boss/mod_staff_profile_for_boss.html', {
        'profile_form': profile_form,
        'staff': user,
        'grupos': Group.objects.filter(name__in=['staff_bodega', 'staff_vendedor']),
        'grupo_actual': user.groups.first()  # Obtener el primer grupo asignado (si existe)
    })



# Listar staff (solo jefe de negocio)
from django.core.paginator import Paginator
@login_required
@jefe_required
def list_staff_for_boss(request):
    negocio = StaffProfile.objects.get(user=request.user).negocio
    staff_list = User.objects.filter(
        staffprofile__negocio=negocio,
        is_staff=True,
        is_active=True
    )
    paginator = Paginator(staff_list, 10)  # Mostrar 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administration/for_boss/list_staff_for_boss.html', {
        'staff_list_for_boss': page_obj
    })



# Modificar cuenta staff (solo jefe de negocio)
@jefe_required
def mod_staff_account_for_boss(request, staff_id):
    user = get_object_or_404(User, pk=staff_id)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)

        if user_form.is_valid():
            user_form.save()
            return redirect('list_staff_for_boss')
    else:
        user_form = UserForm(instance=user)

    return render(request, 'administration/for_boss/mod_staff_account_for_boss.html', {
        'user_form': user_form,
        'staff': user,
    })

# Eliminar staff (solo jefe de negocio)
@jefe_required
def erase_staff_for_boss(request, staff_id):
    user = get_object_or_404(User, pk=staff_id)
    if request.method == 'POST':
        user.delete()
        return redirect('list_staff_for_boss')

    return render(request, 'administration/for_boss/erase_staff_for_boss.html', {
        'staff': user,
    })

