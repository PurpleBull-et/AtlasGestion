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
        'view_marca', 'add_marca', 'change_marca', 'delete_marca',
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



@receiver(post_migrate)
def regiones_comunas_provincias(sender, **kwargs):
    chile_data = {
        "Región de Arica y Parinacota": {
            "Arica": ["Arica", "Camarones"],
            "Parinacota": ["Putre", "General Lagos"],
        },
        "Región de Tarapacá": {
            "Iquique": ["Iquique", "Alto Hospicio"],
            "Tamarugal": ["Pozo Almonte", "Pica", "Huara", "Camiña", "Colchane"],
        },
        "Región de Antofagasta": {
            "Antofagasta": ["Antofagasta", "Mejillones", "Taltal", "Sierra Gorda"],
            "El Loa": ["Calama", "San Pedro de Atacama", "Ollagüe"],
            "Tocopilla": ["Tocopilla", "María Elena"],
        },
        "Región de Atacama": {
            "Copiapó": ["Copiapó", "Tierra Amarilla"],
            "Chañaral": ["Chañaral", "Diego de Almagro"],
            "Huasco": ["Vallenar", "Freirina", "Huasco", "Alto del Carmen"],
        },
        "Región de Coquimbo": {
            "Elqui": ["La Serena", "Coquimbo", "Vicuña", "Andacollo", "Paiguano", "La Higuera"],
            "Limarí": ["Ovalle", "Monte Patria", "Combarbalá", "Punitaqui", "Río Hurtado"],
            "Choapa": ["Illapel", "Salamanca", "Los Vilos", "Canela"],
        },
        "Región de Valparaíso": {
            "Valparaíso": ["Valparaíso", "Viña del Mar", "Concón"],
            "Isla de Pascua": ["Rapa Nui"],
            "Los Andes": ["Los Andes", "San Esteban", "Calle Larga", "Rinconada"],
            "Petorca": ["La Ligua", "Papudo", "Petorca", "Zapallar", "Cabildo"],
            "Quillota": ["Quillota", "La Calera", "Hijuelas", "Nogales", "La Cruz"],
            "San Antonio": ["San Antonio", "Cartagena", "El Tabo", "El Quisco", "Algarrobo"],
            "San Felipe de Aconcagua": ["San Felipe", "Putaendo", "Santa María", "Panquehue", "Catemu", "Llay-Llay"],
            "Marga Marga": ["Quilpué", "Villa Alemana", "Limache", "Olmué"],
        },
        "Región Metropolitana de Santiago": {
            "Santiago": ["Santiago", "Providencia", "Las Condes", "La Florida", "Maipú", "La Reina", "Ñuñoa", "Independencia", 
                         "Recoleta", "Quilicura", "Lo Prado", "Cerro Navia", "Pudahuel", "Estación Central", "Pedro Aguirre Cerda",
                         "San Joaquín", "San Ramón", "La Pintana", "El Bosque", "La Cisterna", "Lo Espejo", "Macul", "Peñalolén", 
                         "San Miguel"],
            "Chacabuco": ["Colina", "Lampa", "Tiltil"],
            "Cordillera": ["San José de Maipo", "Pirque", "Puente Alto"],
            "Maipo": ["San Bernardo", "Buin", "Paine", "Calera de Tango"],
            "Melipilla": ["Melipilla", "San Pedro", "Alhué", "Curacaví", "María Pinto"],
            "Talagante": ["Talagante", "Peñaflor", "El Monte", "Padre Hurtado", "Isla de Maipo"],
        },
        "Región del Libertador General Bernardo O'Higgins": {
            "Cachapoal": ["Rancagua", "Machalí", "Graneros", "Requínoa", "Olivar", "Doñihue", "Codegua", "Mostazal", "Malloa", "Peumo"],
            "Colchagua": ["San Fernando", "Santa Cruz", "Chimbarongo", "Nancagua", "Placilla", "Palmilla", "Pumanque"],
            "Cardenal Caro": ["Pichilemu", "Marchigüe", "La Estrella", "Litueche", "Navidad", "Paredones"],
        },
        "Región del Maule": {
            "Talca": ["Talca", "Constitución", "Curepto", "Empedrado", "Maule", "Pelarco", "Pencahue", "Río Claro", "San Clemente", "San Rafael"],
            "Cauquenes": ["Cauquenes", "Chanco", "Pelluhue"],
            "Curicó": ["Curicó", "Hualañé", "Licantén", "Molina", "Rauco", "Romeral", "Sagrada Familia", "Teno", "Vichuquén"],
            "Linares": ["Linares", "Colbún", "Longaví", "Parral", "Retiro", "San Javier", "Villa Alegre", "Yerbas Buenas"],
        },
        "Región de Ñuble": {
            "Diguillín": ["Chillán", "Chillán Viejo", "Bulnes", "El Carmen", "Pemuco", "San Ignacio", "Yungay"],
            "Itata": ["Quirihue", "Cobquecura", "Coelemu", "Ninhue", "Portezuelo", "Ránquil", "Treguaco"],
            "Punilla": ["San Carlos", "Coihueco", "San Fabián", "Ñiquén"],
        },
        "Región del Biobío": {
            "Concepción": ["Concepción", "Talcahuano", "San Pedro de la Paz", "Hualpén", "Coronel", "Lota", "Santa Juana", "Hualqui", "Penco", "Tomé", "Chiguayante"],
            "Arauco": ["Arauco", "Cañete", "Contulmo", "Curanilahue", "Lebu", "Los Álamos", "Tirúa"],
            "Biobío": ["Los Ángeles", "Cabrero", "Laja", "Mulchén", "Nacimiento", "Negrete", "Quilaco", "Quilleco", "San Rosendo", "Santa Bárbara", "Tucapel", "Yumbel", "Antuco"],
        },
        "Región de La Araucanía": {
            "Cautín": ["Temuco", "Carahue", "Cholchol", "Cunco", "Curarrehue", "Freire", "Galvarino", "Gorbea", "Lautaro", "Loncoche", "Melipeuco", "Nueva Imperial", "Padre Las Casas", "Perquenco", "Pitrufquén", "Pucon", "Saavedra", "Teodoro Schmidt", "Toltén", "Vilcún", "Villarrica"],
            "Malleco": ["Angol", "Collipulli", "Curacautín", "Ercilla", "Lonquimay", "Los Sauces", "Lumaco", "Purén", "Renaico", "Traiguén", "Victoria"],
        },
        "Región de Los Ríos": {
            "Valdivia": ["Valdivia", "Corral", "Lanco", "Los Lagos", "Máfil", "Mariquina", "Paillaco", "Panguipulli"],
            "Ranco": ["La Unión", "Futrono", "Lago Ranco", "Río Bueno"],
        },
        "Región de Los Lagos": {
            "Llanquihue": ["Puerto Montt", "Puerto Varas", "Calbuco", "Fresia", "Frutillar", "Los Muermos", "Maullín"],
            "Chiloé": ["Castro", "Ancud", "Chonchi", "Curaco de Vélez", "Dalcahue", "Puqueldón", "Queilén", "Quellón", "Quemchi", "Quinchao"],
            "Osorno": ["Osorno", "Puerto Octay", "Purranque", "Puyehue", "Río Negro", "San Juan de la Costa", "San Pablo"],
            "Palena": ["Chaitén", "Futaleufú", "Hualaihué", "Palena"],
        },
        "Región de Aysén del General Carlos Ibáñez del Campo": {
            "Coyhaique": ["Coyhaique", "Lago Verde"],
            "Aysén": ["Puerto Aysén", "Cisnes", "Guaitecas"],
            "Capitán Prat": ["Cochrane", "O'Higgins", "Tortel"],
            "General Carrera": ["Chile Chico", "Río Ibáñez"],
        },
        "Región de Magallanes y de la Antártica Chilena": {
            "Magallanes": ["Punta Arenas", "Laguna Blanca", "Río Verde", "San Gregorio"],
            "Antártica Chilena": ["Cabo de Hornos (Puerto Williams)", "Antártica"],
            "Tierra del Fuego": ["Porvenir", "Primavera", "Timaukel"],
            "Última Esperanza": ["Natales", "Torres del Paine"],
        },
    }

    # Crear o buscar las regiones, provincias y comunas
    for region_nombre, provincias in chile_data.items():
        # Crear o buscar la región
        region, _ = Region.objects.get_or_create(nombre=region_nombre)
        for provincia_nombre, comunas in provincias.items():
            # Crear o buscar la provincia
            provincia, _ = Provincia.objects.get_or_create(nombre=provincia_nombre, region=region)
            for comuna_nombre in comunas:
                # Crear o buscar la comuna
                Comuna.objects.get_or_create(nombre=comuna_nombre, provincia=provincia)


@receiver(post_migrate)
def create_membresia_plans(sender, **kwargs):
    # Definimos los planes de membresía
    membresias_data = [
        {"nombre": "Básico", "val_mensual": 10000, "val_adicional": 0, "duracion_dias": 30, "max_users": 5, "descripcion": "Plan Básico con un máximo de 5 cuentas y sin costo adicional."},
        {"nombre": "Medio", "val_mensual": 15000, "val_adicional": 10000, "duracion_dias": 30, "max_users": 10, "descripcion": "Plan Medio con un máximo de 10 cuentas y un costo adicional de $10,000."},
        {"nombre": "Premium", "val_mensual": 30000, "val_adicional": 9000, "duracion_dias": 30, "max_users": 15, "descripcion": "Plan Premium con un máximo de 15 cuentas y un costo adicional de $9,000."},
        {"nombre": "Avanzado", "val_mensual": 40000, "val_adicional": 8000, "duracion_dias": 30, "max_users": 20, "descripcion": "Plan Avanzado con un máximo de 20 cuentas y un costo adicional de $8,000."},
        {"nombre": "Corporativo", "val_mensual": 50000, "val_adicional": 7000, "duracion_dias": 30, "max_users": 30, "descripcion": "Plan Corporativo con un máximo de 30 cuentas y un costo adicional de $7,000 para rangos superiores."},
    ]

    for membresia_data in membresias_data:
        Membresia.objects.get_or_create(nombre=membresia_data["nombre"], defaults=membresia_data)
