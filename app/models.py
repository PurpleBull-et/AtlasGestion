import os
from django.contrib.auth.models import User
from django.db import models
from PIL import Image as PilImage
from django.core.files.base import ContentFile
import io
from django.utils.timezone import now

class Negocio(models.Model):
    nombre = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='negocios_logos/', blank=True, null=True)  # Campo de imagen

    def __str__(self):
        return self.nombre
    
class Almacen(models.Model):
    id = models.AutoField(primary_key=True)
    direccion = models.CharField(max_length=255)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)  # Relación con negocio

    def __str__(self):
        return f'Almacén en {self.direccion} - Capacidad: {self.capacidad}'

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)  # Relacionar con negocio
    
    def __str__(self):
        return self.nombre

    
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='categorias')  # Relacionar con negocio

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    proveedores = models.ManyToManyField(Proveedor, blank=True)  # Relación con varios proveedores
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('sin_stock', 'Sin Stock'),
        ('descontinuado', 'Descontinuado'),
    ]
    producto_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    precio = models.IntegerField(default=0) 
    stock = models.IntegerField(default=0)  
    descripcion = models.TextField()
    almacen = models.ForeignKey('Almacen', on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='sin_stock')

    def __str__(self):
        return self.nombre

    def actualizar_estado(self):
        if self.stock == 0:
            self.estado = 'sin_stock'
        self.save()

class ProductoAlmacen(Producto):
    pass  # Productos como yogurt, galletas, etc.

class ProductoTienda(Producto):
    talla = models.CharField(max_length=3, choices=[('S', 'Small'), ('M', 'Medium'), ('L', 'Large')])

    def __str__(self):
        return f'{self.nombre} (Talla: {self.talla})'

class ProductoBar(Producto):
    cc_por_unidad = models.DecimalField(max_digits=5, decimal_places=1)  # Cantidad de cc por unidad del producto

class EntradaBodega(models.Model):
    MEDIOS_PAGO = [
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito o Débito'),
        ('efectivo', 'Efectivo')
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_recibida = models.PositiveIntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    precio_unitario = models.IntegerField()
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    medio_pago = models.CharField(max_length=20, choices=MEDIOS_PAGO, default='efectivo')
    lote = models.CharField(max_length=100, blank=True, null=True)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    estado_devolucion = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Entradas a Bodega"

    def total_entrada(self):
        """Método para calcular el precio total de la entrada"""
        return self.cantidad_recibida * self.precio_unitario

    def __str__(self):
        return f"Entrada {self.producto.nombre} - Lote {self.lote}"

    
class ProductosDevueltos(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    entrada_bodega = models.ForeignKey(EntradaBodega, on_delete=models.CASCADE)  # Relación con la entrada original
    cantidad_devuelta = models.PositiveIntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    lote = models.CharField(max_length=100, blank=True, null=True)
    motivo_devolucion = models.TextField(blank=True, null=True)  

    class Meta:
        verbose_name_plural = "Productos Devueltos"

    def __str__(self):
        return f"Devolución de {self.producto.nombre} - Lote {self.lote}"



class DevolucionProveedor(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()  
    proveedor = models.CharField(max_length=255)  
    fecha_devolucion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Devoluciones a Proveedor"

    def __str__(self):
        return f'Devolución de {self.producto.nombre} al proveedor {self.proveedor}'

class Imagen(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class PerfilClientes(models.Model):
    id_cliente = models.AutoField(primary_key=True)  
    nombre = models.CharField(max_length=255)  
    rut = models.CharField(max_length=12, unique=True) 
    direccion = models.CharField(max_length=255) 
    telefono = models.CharField(max_length=20) 
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.nombre} - {self.rut}'


class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, through='CarritoProducto')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'Carrito de {self.usuario.username}'


class CarritoProducto(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def total_precio(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}' 


class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    correo = models.EmailField(null=True, blank=True)  # Campo opcional para correo de invitados

    def __str__(self):
        return f'Compra {self.id} - {self.usuario.username if self.usuario else "Invitado"}'


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre} en Compra {self.compra.id}'


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username}"

class StaffProfile(models.Model):
    MEMBRESIA_CHOICES = [
        ('Mensual', 'Mensual'),
        ('Semestral', 'Semestral'),
        ('Anual', 'Anual'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, default='Activo')  # Activo/Inactivo
    membresia = models.CharField(max_length=20, choices=MEMBRESIA_CHOICES)
    fecha_membresia = models.DateField(default=now, null=True, blank=True)  # Asignar un valor por defecto



    estado_pago = models.CharField(max_length=20, default='Pendiente')
    negocio = models.ForeignKey('Negocio', on_delete=models.CASCADE, related_name='staff')

    def __str__(self):
        return f"{self.user.username} - {self.negocio.nombre}"


#MODELOS DE AUDITORIA
class HistorialProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cambio = models.TextField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.producto.nombre} modificado por {self.usuario.username}'

class HistorialUsuario(models.Model):
    usuario_modificado = models.ForeignKey(User, related_name='usuario_modificado', on_delete=models.CASCADE)
    usuario_accion = models.ForeignKey(User, related_name='usuario_accion', on_delete=models.SET_NULL, null=True)
    cambio = models.TextField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Usuario {self.usuario_modificado.username} modificado por {self.usuario_accion.username}'

class RegistroErrores(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ruta = models.CharField(max_length=255)
    metodo = models.CharField(max_length=10)
    error = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Error en {self.ruta} por {self.usuario.username if self.usuario else 'desconocido'}"