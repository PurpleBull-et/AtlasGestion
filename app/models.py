import os
from django.contrib.auth.models import User
from django.db import models
from PIL import Image as PilImage
from django.core.files.base import ContentFile
import io
from django.utils.timezone import now

class Negocio(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_mayorista = models.BooleanField(default=False, verbose_name='¿Es Mayorista?')
    #logo = models.ImageField(upload_to='negocios_logos/', blank=True, null=True)  # Campo de imagen

    def __str__(self):
        return self.nombre
    
class Almacen(models.Model):
    id = models.AutoField(primary_key=True)
    direccion = models.CharField(max_length=255)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE) 

    def __str__(self):
        return f'Almacén en {self.direccion}'

class Proveedor(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre

    
class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='categorias') 

    def __str__(self):
        return self.nombre


# En el archivo models.py
class Producto(models.Model):
    producto_id = models.AutoField(primary_key=True)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)  # SKU para productos mayoristas
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    ESTADO_CHOICES = [
        ('registrado_reciente', 'Registrado Reciente'),
        ('disponible', 'Disponible'),
        ('sin_stock', 'Sin Stock'),
        ('ingresado_manual', 'Ingresado Manual'),
    ]
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    precio = models.IntegerField(default=0)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Solo para mayoristas
    descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Solo para mayoristas
    stock = models.IntegerField(default=0)
    almacen = models.ForeignKey('Almacen', on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='registrado_reciente')

    def __str__(self):
        return self.nombre

    def actualizar_estado(self):
        if self.stock <= 0:
            self.estado = 'sin_stock'
        elif self.stock > 0:
            self.estado = 'disponible'
        self.save()



class EntradaBodega(models.Model):
    id = models.AutoField(primary_key=True)
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
    id = models.AutoField(primary_key=True)
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


class PerfilClientes(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.CharField(max_length=100, null=True, blank=True)
    correo = models.EmailField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return f'{self.nombre or "Cliente sin nombre"} - {self.rut or "Sin RUT"}'


class Carrito(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, through='CarritoProducto')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField(default=0)  

    def __str__(self):
        return f'Carrito de {self.usuario.username}'


class CarritoProducto(models.Model):
    id = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def total_precio(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}' 


class Compra(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()  
    correo = models.EmailField(null=True, blank=True) 
    nombre_staff = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'Compra #{self.id} - {self.usuario}'


class DetalleCompra(models.Model):
    id = models.AutoField(primary_key=True)
    compra = models.ForeignKey(Compra, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.IntegerField()  

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre} en Compra {self.compra.id}'



class AdminProfile(models.Model):
    id = models.AutoField(primary_key=True)
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
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, default='Activo')
    membresia = models.CharField(max_length=20, choices=MEMBRESIA_CHOICES)
    fecha_membresia = models.DateField(default=now, null=True, blank=True) 



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