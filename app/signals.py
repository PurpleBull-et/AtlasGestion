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
def regiones_comunas_provincias_ciudades(sender, **kwargs):
    chile_data = {
        "Metropolitana de Santiago": {
            "Cordillera": {
                "Puente Alto": ["Puente Alto"],
                "Pirque": ["Pirque"],
                "San José de Maipo": ["San José de Maipo"],
                "San Bernardo": ["San Bernardo"],
            },
            "Santiago": {
                "Santiago": [
                    "Santiago", "Providencia", "Las Condes", "La Florida", "Maipú", "La Reina",
                    "Ñuñoa", "Independencia", "Recoleta", "Quilicura", "Lo Prado", "Cerro Navia",
                    "Pudahuel", "Estación Central", "Pedro Aguirre Cerda", "San Joaquín",
                    "San Ramón", "La Pintana", "El Bosque", "La Cisterna", "Lo Espejo",
                    "Macul", "Peñalolén", "San Miguel", "Conchalí", "Renca", "La Granja",
                    "Lo Barnechea", "Macul", "Huechuraba", "Quinta Normal", "Lo Prado",
                    "San Joaquín", "Renca", "Lo Espejo", "Lo Prado", "Renca"
                ],
                "Maipú": ["Maipú"],
                "La Florida": ["La Florida"],
                "Las Condes": ["Las Condes"],
                "Pudahuel": ["Pudahuel"],
                "Quilicura": ["Quilicura"],
                "Ñuñoa": ["Ñuñoa"],
                "La Pintana": ["La Pintana"],
                "El Bosque": ["El Bosque"],
                "Recoleta": ["Recoleta"],
                "Renca": ["Renca"],
                "Providencia": ["Providencia"],
                "Estación Central": ["Estación Central"],
                "Cerro Navia": ["Cerro Navia"],
                "Conchalí": ["Conchalí"],
                "Peñalolén": ["Peñalolén"],
                "Quinta Normal": ["Quinta Normal"],
                "San Miguel": ["San Miguel"],
                "Lo Barnechea": ["Lo Barnechea"],
                "Macul": ["Macul"],
                "La Granja": ["La Granja"],
                "Pedro Aguirre Cerda": ["Pedro Aguirre Cerda"],
                "Independencia": ["Independencia"],
                "Lo Espejo": ["Lo Espejo"],
                "Huechuraba": ["Huechuraba"],
                "Lo Prado": ["Lo Prado"],
                "San Joaquín": ["San Joaquín"],
                "La Reina": ["La Reina"],
            },
            "Maipo": {
                "San Bernardo": ["San Bernardo"],
                "Buin": ["Buin"],
                "Paine": ["Paine"],
                "Calera de Tango": ["Calera de Tango"],
            },
            "Chacabuco": {
                "Colina": ["Colina", "Chicureo"],
                "Lampa": ["Lampa", "Batuco"],
                "Tiltil": ["Tiltil"],
            },
            "Cordillera": {
                "Pirque": ["Pirque"],
                "Puente Alto": ["Puente Alto"],
                "San José de Maipo": ["San José de Maipo"],
            },
            "Talagante": {
                "Talagante": ["Talagante"],
                "Peñaflor": ["Peñaflor"],
                "El Monte": ["El Monte"],
                "Padre Hurtado": ["Padre Hurtado"],
                "Isla de Maipo": ["Isla de Maipo", "La Islita"],
            },
            "Melipilla": {
                "Melipilla": ["Melipilla"],
                "San Pedro": ["San Pedro"],
                "Alhué": ["Alhué"],
                "Curacaví": ["Curacaví"],
                "María Pinto": ["María Pinto"],
            },
        },
        "Antofagasta": {
            "Antofagasta": {
                "Antofagasta": ["Antofagasta"],
                "Mejillones": ["Mejillones"],
                "Taltal": ["Taltal"],
                "Sierra Gorda": ["Sierra Gorda"],
            },
            "El Loa": {
                "Calama": ["Calama"],
                "San Pedro de Atacama": ["San Pedro de Atacama"],
                "Ollagüe": ["Ollagüe"],
            },
            "Tocopilla": {
                "Tocopilla": ["Tocopilla"],
                "María Elena": ["María Elena"],
            },
        },
        "Valparaíso": {
            "Valparaíso": {
                "Viña del Mar": ["Viña del Mar"],
                "Valparaíso": ["Valparaíso"],
                "Concón": ["Concón"],
                "Quintero": ["Quintero"],
                "Vitacura": ["Vitacura"],
                "Calera de Tango": ["Calera de Tango"],
                "Quinta de Tilcoco": ["Quinta de Tilcoco"],
                "Concón": ["Concón"],
                "La Granja": ["La Granja"],
            },
            "Marga Marga": {
                "Quilpué": ["Quilpué"],
                "Villa Alemana": ["Villa Alemana"],
                "Limache": ["Limache"],
                "Olmué": ["Olmué"],
                "Llaillay": ["Llaillay"],
                "Limache": ["Limache"],
                "Olmué": ["Olmué"],
            },
            "San Antonio": {
                "San Antonio": ["San Antonio"],
                "Cartagena": ["Cartagena"],
                "El Tabo": ["El Tabo", "Las Cruces"],
                "El Quisco": ["El Quisco"],
                "Algarrobo": ["Algarrobo"],
                "Santo Domingo": ["Santo Domingo"],
                "El Tabo": ["El Tabo"],
            },
            "Los Andes": {
                "Los Andes": ["Los Andes"],
                "San Esteban": ["San Esteban"],
                "Calle Larga": ["Calle Larga"],
                "Rinconada": ["Rinconada"],
            },
            "Petorca": {
                "La Ligua": ["La Ligua"],
                "Papudo": ["Papudo"],
                "Petorca": ["Petorca"],
                "Zapallar": ["Zapallar"],
                "Cabildo": ["Cabildo"],
            },
            "Quillota": {
                "Quillota": ["Quillota"],
                "La Calera": ["La Calera"],
                "Hijuelas": ["Hijuelas"],
                "Nogales": ["Nogales"],
                "La Cruz": ["La Cruz"],
            },
            "Chiloé": {
                "Castro": ["Castro"],
                "Ancud": ["Ancud"],
                "Chonchi": ["Chonchi"],
                "Curaco de Vélez": ["Curaco de Vélez"],
                "Dalcahue": ["Dalcahue"],
                "Puqueldón": ["Puqueldón"],
                "Queilén": ["Queilén"],
                "Quellón": ["Quellón"],
                "Quemchi": ["Quemchi"],
                "Quinchao": ["Quinchao"],
            },
            "Palena": {
                "Chaitén": ["Chaitén"],
                "Futaleufú": ["Futaleufú"],
                "Hualaihué": ["Hualaihué"],
                "Palena": ["Palena"],
            },
        },
        "Biobío": {
            "Concepción": {
                "Concepción": ["Concepción"],
                "Talcahuano": ["Talcahuano"],
                "San Pedro de la Paz": ["San Pedro de la Paz"],
                "Hualpén": ["Hualpén"],
                "Coronel": ["Coronel"],
                "Lota": ["Lota"],
                "Santa Juana": ["Santa Juana"],
                "Hualqui": ["Hualqui"],
                "Penco": ["Penco"],
                "Tomé": ["Tomé"],
                "Chiguayante": ["Chiguayante"],
            },
            "Arauco": {
                "Arauco": ["Arauco"],
                "Cañete": ["Cañete"],
                "Contulmo": ["Contulmo"],
                "Curanilahue": ["Curanilahue"],
                "Lebu": ["Lebu"],
                "Los Álamos": ["Los Álamos"],
                "Tirúa": ["Tirúa"],
            },
            "Biobío": {
                "Los Ángeles": ["Los Ángeles"],
                "Cabrero": ["Cabrero"],
                "Laja": ["Laja"],
                "Mulchén": ["Mulchén"],
                "Nacimiento": ["Nacimiento"],
                "Negrete": ["Negrete"],
                "Quilaco": ["Quilaco"],
                "Quilleco": ["Quilleco"],
                "San Rosendo": ["San Rosendo"],
                "Santa Bárbara": ["Santa Bárbara"],
                "Tucapel": ["Tucapel"],
                "Yumbel": ["Yumbel"],
                "Antuco": ["Antuco"],
            },
        },
        "La Araucanía": {
            "Cautín": {
                "Temuco": ["Temuco"],
                "Carahue": ["Carahue"],
                "Cholchol": ["Cholchol"],
                "Cunco": ["Cunco"],
                "Curarrehue": ["Curarrehue"],
                "Freire": ["Freire"],
                "Galvarino": ["Galvarino"],
                "Gorbea": ["Gorbea"],
                "Lautaro": ["Lautaro"],
                "Loncoche": ["Loncoche"],
                "Melipeuco": ["Melipeuco"],
                "Nueva Imperial": ["Nueva Imperial"],
                "Padre Las Casas": ["Padre Las Casas"],
                "Perquenco": ["Perquenco"],
                "Pitrufquén": ["Pitrufquén"],
                "Pucon": ["Pucon"],
                "Saavedra": ["Saavedra"],
                "Teodoro Schmidt": ["Teodoro Schmidt"],
                "Toltén": ["Toltén"],
                "Vilcún": ["Vilcún"],
                "Villarrica": ["Villarrica"],
            },
            "Malleco": {
                "Angol": ["Angol"],
                "Collipulli": ["Collipulli"],
                "Curacautín": ["Curacautín"],
                "Ercilla": ["Ercilla"],
                "Lonquimay": ["Lonquimay"],
                "Los Sauces": ["Los Sauces"],
                "Lumaco": ["Lumaco"],
                "Purén": ["Purén"],
                "Renaico": ["Renaico"],
                "Traiguén": ["Traiguén"],
                "Victoria": ["Victoria"],
            },
        },
        "Libertador General Bernardo O'Higgins": {
            "Cachapoal": {
                "Rancagua": ["Rancagua"],
                "Machalí": ["Machalí"],
                "Graneros": ["Graneros"],
                "Requínoa": ["Requínoa"],
                "Olivar": ["Olivar"],
                "Doñihue": ["Doñihue"],
                "Codegua": ["Codegua"],
                "Mostazal": ["Mostazal"],
                "Malloa": ["Malloa"],
                "Peumo": ["Peumo"],
                "Graneros": ["Graneros"],
                "Requínoa": ["Requínoa"],
                "Rancagua": ["Rancagua"],
                "Mostazal": ["Mostazal"],
                "San Francisco de Mostazal": ["Mostazal"],
                "Requínoa": ["Requínoa"],
                "Rengo": ["Rengo"],
                "Peumo": ["Peumo"],
                "Requínoa": ["Requínoa"],
            },
            "Colchagua": {
                "San Fernando": ["San Fernando"],
                "Santa Cruz": ["Santa Cruz"],
                "Chimbarongo": ["Chimbarongo"],
                "Nancagua": ["Nancagua"],
                "Placilla": ["Placilla"],
                "Palmilla": ["Palmilla"],
                "Pumanque": ["Pumanque"],
            },
            "Cardenal Caro": {
                "Pichilemu": ["Pichilemu"],
                "Marchigüe": ["Marchigüe"],
                "La Estrella": ["La Estrella"],
                "Litueche": ["Litueche"],
                "Navidad": ["Navidad"],
                "Paredones": ["Paredones"],
                "Chépica": ["Chépica"],
            },
        },
        "Maule": {
            "Talca": {
                "Talca": ["Talca"],
                "Constitución": ["Constitución"],
                "Curepto": ["Curepto"],
                "Empedrado": ["Empedrado"],
                "Maule": ["Maule"],
                "Pelarco": ["Pelarco"],
                "Pencahue": ["Pencahue"],
                "Río Claro": ["Río Claro"],
                "San Clemente": ["San Clemente"],
                "San Rafael": ["San Rafael"],
                "Culenar (Gran Talca)": ["Culenar"],
            },
            "Cauquenes": {
                "Cauquenes": ["Cauquenes"],
                "Chanco": ["Chanco"],
                "Pelluhue": ["Pelluhue"],
            },
            "Curicó": {
                "Curicó": ["Curicó"],
                "Hualañé": ["Hualañé"],
                "Licantén": ["Licantén"],
                "Molina": ["Molina"],
                "Rauco": ["Rauco"],
                "Romeral": ["Romeral"],
                "Sagrada Familia": ["Sagrada Familia"],
                "Teno": ["Teno"],
                "Vichuquén": ["Vichuquén"],
            },
            "Linares": {
                "Linares": ["Linares"],
                "Colbún": ["Colbún"],
                "Longaví": ["Longaví"],
                "Parral": ["Parral"],
                "Retiro": ["Retiro"],
                "San Javier": ["San Javier"],
                "Villa Alegre": ["Villa Alegre"],
                "Yerbas Buenas": ["Yerbas Buenas"],
            },
        },
        "Ñuble": {
            "Diguillín": {
                "Chillán": ["Chillán"],
                "Chillán Viejo": ["Chillán Viejo"],
                "Bulnes": ["Bulnes"],
                "El Carmen": ["El Carmen"],
                "Pemuco": ["Pemuco"],
                "San Ignacio": ["San Ignacio"],
                "Yungay": ["Yungay"],
            },
            "Itata": {
                "Quirihue": ["Quirihue"],
                "Cobquecura": ["Cobquecura"],
                "Coelemu": ["Coelemu"],
                "Ninhue": ["Ninhue"],
                "Portezuelo": ["Portezuelo"],
                "Ránquil": ["Ránquil"],
                "Treguaco": ["Treguaco"],
            },
            "Punilla": {
                "San Carlos": ["San Carlos"],
                "Coihueco": ["Coihueco"],
                "San Fabián": ["San Fabián"],
                "Ñiquén": ["Ñiquén"],
            },
        },
        "Los Ríos": {
            "Valdivia": {
                "Valdivia": ["Valdivia"],
                "Corral": ["Corral"],
                "Lanco": ["Lanco"],
                "Los Lagos": ["Los Lagos"],
                "Máfil": ["Máfil"],
                "Mariquina": ["Mariquina"],
                "Paillaco": ["Paillaco"],
                "Panguipulli": ["Panguipulli"],
            },
            "Ranco": {
                "La Unión": ["La Unión"],
                "Futrono": ["Futrono"],
                "Lago Ranco": ["Lago Ranco"],
                "Río Bueno": ["Río Bueno"],
            },
        },
        "Los Lagos": {
            "Llanquihue": {
                "Puerto Montt": ["Puerto Montt"],
                "Puerto Varas": ["Puerto Varas"],
                "Calbuco": ["Calbuco"],
                "Fresia": ["Fresia"],
                "Frutillar": ["Frutillar"],
                "Los Muermos": ["Los Muermos"],
                "Maullín": ["Maullín"],
                "Alerce (Gran Puerto Montt)": ["Puerto Montt"],
                "Puerto Octay": ["Puerto Octay"],
                "Purranque": ["Purranque"],
                "Puyehue": ["Puyehue"],
                "Río Negro": ["Río Negro"],
                "San Juan de la Costa": ["San Juan de la Costa"],
                "San Pablo": ["San Pablo"],
                "Puerto Varas (Gran Puerto Montt)": ["Puerto Varas"],
                "Las Ventanas": ["Puchuncaví"],
                "Puerto Varas (Gran Puerto Montt)": ["Puerto Varas"],
            },
            "Chiloé": {
                "Castro": ["Castro"],
                "Ancud": ["Ancud"],
                "Chonchi": ["Chonchi"],
                "Curaco de Vélez": ["Curaco de Vélez"],
                "Dalcahue": ["Dalcahue"],
                "Puqueldón": ["Puqueldón"],
                "Queilén": ["Queilén"],
                "Quellón": ["Quellón"],
                "Quemchi": ["Quemchi"],
                "Quinchao": ["Quinchao"],
            },
            "Osorno": {
                "Osorno": ["Osorno"],
                "Puerto Octay": ["Puerto Octay"],
                "Purranque": ["Purranque"],
                "Puyehue": ["Puyehue"],
                "Río Negro": ["Río Negro"],
                "San Juan de la Costa": ["San Juan de la Costa"],
                "San Pablo": ["San Pablo"],
            },
            "Palena": {
                "Chaitén": ["Chaitén"],
                "Futaleufú": ["Futaleufú"],
                "Hualaihué": ["Hualaihué"],
                "Palena": ["Palena"],
            },
        },
        "Aysén del General Carlos Ibáñez del Campo": {
            "Coyhaique": {
                "Coyhaique": ["Coyhaique"],
                "Lago Verde": ["Lago Verde"],
            },
            "Aysén": {
                "Puerto Aysén": ["Puerto Aysén"],
                "Cisnes": ["Cisnes"],
                "Guaitecas": ["Guaitecas"],
            },
            "Capitán Prat": {
                "Cochrane": ["Cochrane"],
                "O'Higgins": ["O'Higgins"],
                "Tortel": ["Tortel"],
            },
            "General Carrera": {
                "Chile Chico": ["Chile Chico"],
                "Río Ibáñez": ["Río Ibáñez"],
            },
        },
        "Magallanes y de la Antártica Chilena": {
            "Magallanes": {
                "Punta Arenas": ["Punta Arenas"],
                "Laguna Blanca": ["Laguna Blanca"],
                "Río Verde": ["Río Verde"],
                "San Gregorio": ["San Gregorio"],
            },
            "Antártica Chilena": {
                "Cabo de Hornos (Puerto Williams)": ["Cabo de Hornos (Puerto Williams)"],
                "Antártica": ["Antártica"],
            },
            "Tierra del Fuego": {
                "Porvenir": ["Porvenir"],
                "Primavera": ["Primavera"],
                "Timaukel": ["Timaukel"],
            },
            "Última Esperanza": {
                "Natales": ["Natales"],
                "Torres del Paine": ["Torres del Paine"],
            },
        },
    }

    # Crear o buscar las regiones, provincias, comunas y ciudades
    for region_nombre, provincias in chile_data.items():
        # Crear o buscar la región
        region, created = Region.objects.get_or_create(nombre=region_nombre)
        for provincia_nombre, comunas in provincias.items():
            # Crear o buscar la provincia
            provincia, created = Provincia.objects.get_or_create(nombre=provincia_nombre, region=region)
            for comuna_nombre, ciudades in comunas.items():
                # Crear o buscar la comuna
                comuna, created = Comuna.objects.get_or_create(nombre=comuna_nombre, provincia=provincia)
                for ciudad_nombre in ciudades:
                    # Crear o buscar la ciudad
                    Ciudad.objects.get_or_create(nombre=ciudad_nombre, comuna=comuna)

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
