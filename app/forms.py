from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from .models import *

# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import StaffProfile

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Primer Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña',
        }

    def __init__(self, *args, **kwargs):
        disable_username = kwargs.pop('disable_username', False)
        super(UserForm, self).__init__(*args, **kwargs)
        if disable_username:
            self.fields['username'].disabled = True  # Bloquea el campo si se indica
 

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['rut', 'direccion', 'telefono', 'region', 'provincia']
        
class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['rut', 'direccion', 'telefono', 'region', 'provincia', 'membresia', 'negocio']
        labels = {
            'rut': 'RUT',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'region': 'Región',
            'provincia': 'Provincia',
            'membresia': 'Membresía',
            'negocio': 'Negocio',
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']

#PRODUCTO
class ProductoForm(forms.ModelForm):
    proveedores = forms.ModelMultipleChoiceField(queryset=Proveedor.objects.all(), required=False)

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'categoria', 'descripcion']  # Campos limitados

    def save(self, commit=True):
        producto = super().save(commit=False)
        # Solo establecer stock a 0 si el producto es nuevo (es decir, si no tiene un ID)
        if not producto.pk:
            producto.stock = 0  # Stock por defecto en 0 al crear
            producto.precio = 0  # Precio por defecto en 0 al crear
        if commit:
            producto.save()
            self.save_m2m()  # Guardar relaciones many-to-many si las hay
        return producto

class ActualizarPrecioForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['precio']
        labels = {
            'precio': 'Precio del Producto',
        }
        widgets = {
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }



class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['imagen']
        labels = {
            'imagen': 'Imagen del Producto',
        }
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing, make the image non-mandatory
        if self.instance and self.instance.pk:
            self.fields['imagen'].required = False



class CarritoProductoForm(forms.ModelForm):
    class Meta:
        model = CarritoProducto
        fields = ['producto', 'cantidad']
        labels = {
            'producto': 'Producto',
            'cantidad': 'Cantidad',
        }


class PerfilClientesForm(forms.ModelForm):
    class Meta:
        model = PerfilClientes
        fields = ['nombre', 'rut', 'direccion', 'telefono', 'region', 'provincia']


class EntradaBodegaForm(forms.ModelForm):
    class Meta:
        model = EntradaBodega
        fields = ['producto', 'cantidad_recibida', 'proveedor', 'precio_unitario', 'lote', 'medio_pago']

    def __init__(self, *args, **kwargs):
        almacen = kwargs.pop('almacen', None)  # Recibe el almacén como parámetro
        super(EntradaBodegaForm, self).__init__(*args, **kwargs)
        if almacen:
            # Filtrar productos por el almacén del negocio y estado
            self.fields['producto'].queryset = Producto.objects.filter(
                almacen=almacen, estado__in=['disponible', 'sin_stock']
            )

class NegocioForm(forms.ModelForm):
    almacen_direccion = forms.CharField(label="Dirección del Almacén", max_length=255)

    class Meta:
        model = Negocio
        fields = ['nombre', 'direccion', 'telefono', 'region', 'provincia', 'logo']

    def save(self, commit=True):
        negocio = super().save(commit=False)
        if commit:
            negocio.save()

            Almacen.objects.create(direccion=self.cleaned_data['almacen_direccion'], negocio=negocio)
        
        return negocio


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut_empresa', 'telefono', 'direccion']
