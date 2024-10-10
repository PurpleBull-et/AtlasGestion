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


#PRODUCTO
class ProductoForm(forms.ModelForm):
    proveedores = forms.ModelMultipleChoiceField(queryset=Proveedor.objects.all(), required=False)

    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'precio', 'descripcion', 'proveedores']  # Añadir proveedores

    def save(self, commit=True):
        producto = super().save(commit=False)
        if commit:
            producto.stock = 0  # Stock por defecto en 0
            producto.save()
            self.save_m2m()  # Guardar las relaciones many-to-many
        return producto



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
        fields = ['producto', 'cantidad_recibida', 'proveedor', 'precio_unitario', 'medio_pago']

    def __init__(self, *args, **kwargs):
        almacen = kwargs.pop('almacen', None)  # Recibe el almacén como parámetro
        super(EntradaBodegaForm, self).__init__(*args, **kwargs)
        if almacen:
            # Filtrar productos por el almacén del negocio y estado
            self.fields['producto'].queryset = Producto.objects.filter(
                almacen=almacen, estado__in=['disponible', 'sin_stock']
            )

class NegocioForm(forms.ModelForm):
    class Meta:
        model = Negocio
        fields = ['nombre', 'direccion', 'telefono', 'region', 'provincia', 'logo']


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut_empresa', 'telefono', 'direccion']
