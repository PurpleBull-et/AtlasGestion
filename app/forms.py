from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from .models import *
from .utils import *  

class UserForBossForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Primer Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si el correo ya existe en otro usuario
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            self.add_error('email', "Este correo ya está registrado en otra cuenta.")
        
        return email

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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verificar si el correo ya existe
        if User.objects.filter(email=email).exists():
            self.add_error('email', "Este correo ya está registrado en otra cuenta.")
        return email
         
class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['rut', 'direccion', 'telefono', 'negocio']
        labels = {
            'rut': 'RUT',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'negocio': 'Negocio',
        }

    def clean(self):
        cleaned_data = super().clean()

        # Verificar si el usuario asociado existe antes de acceder a su correo
        if self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            user_email = self.instance.user.email
        else:
            user_email = None

        # Validar si el correo ya existe en StaffProfile
        if user_email and StaffProfile.objects.filter(user__email=user_email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este correo ya está registrado como usuario Staff.")

        # Validar si el correo ya existe en otros modelos
        if user_email:
            if Negocio.objects.filter(correo=user_email).exists():
                raise ValidationError("Este correo ya está registrado como Negocio.")
            if Proveedor.objects.filter(correo=user_email).exists():
                raise ValidationError("Este correo ya está registrado como Proveedor.")
            if PerfilClienteEmpresa.objects.filter(correo=user_email).exists():
                raise ValidationError("Este correo ya está registrado como Cliente de Empresa.")
            if PerfilClientes.objects.filter(correo=user_email).exists():
                raise ValidationError("Este correo ya está registrado como Cliente.")

        return cleaned_data

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        self.negocio = kwargs.pop('negocio', None)
        super().__init__(*args, **kwargs)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        self.negocio = kwargs.pop('negocio', None)
        super().__init__(*args, **kwargs)



class TipoProductoForm(forms.ModelForm):
    class Meta:
        model = TipoProducto
        fields = ['tipo', 'nombre']


#PRODUCTO para mayorista y minorista
class ProductoFormMayorista(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'sku', 
            'nombre', 
            'precio',           
            'precio_mayorista',   
            'descuento', 
            'descuento_mayorista',
            'tasa_ila',
        ]
        widgets = {
            'tasa_ila': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        producto = super().save(commit=False)
        
        if not producto.pk and producto.precio is None:
            producto.precio = 0
        if commit:
            producto.save()
        return producto


class ProductoFormMinorista(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'sku', 
            'nombre', 
            'precio',           
            'descuento', 
            'tasa_ila',
        ]
        widgets = {
            'tasa_ila': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        producto = super().save(commit=False)
        
        if not producto.pk and producto.precio is None:
            producto.precio = 0 
        if commit:
            producto.save()
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

class CarritoProductoForm(forms.ModelForm):
    class Meta:
        model = CarritoProducto
        fields = ['producto', 'cantidad']
        labels = {
            'producto': 'Producto',
            'cantidad': 'Cantidad',
        }

class PerfilClienteEmpresaForm(forms.ModelForm):
    rut_empresa = forms.CharField(
        max_length=12,
        required=True,
        label="RUT Empresa",
        error_messages={
            'required': 'Por favor, ingresa un RUT válido.',
            'max_length': 'El RUT no puede exceder los 12 caracteres.'
        }
    )
    class Meta:
        model = PerfilClienteEmpresa
        ordering = ['nombre']
        fields = [
            'nombre', 'raz_social', 'giro', 'rut_empresa', 'direccion', 'correo', 'telefono', 'linea_credito', 'descuento_fijo', 'dias_pago'
        ]
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_rut_empresa(self):
        rut = self.cleaned_data.get('rut_empresa')
        if not validar_rut_empresa(rut):
            raise ValidationError("El RUT ingresado no es válido.")
        return rut

class PerfilClientesForm(forms.ModelForm):
    class Meta:
        model = PerfilClientes
        fields = [
            'nombre', 'rut', 'direccion', 'comuna', 'region', 'provincia',
            'correo', 'telefono', 'linea_credito', 'descuento_fijo', 'dias_pago'
        ]
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EntradaBodegaForm(forms.ModelForm):
    class Meta:
        model = EntradaBodega
        fields = ['numero_factura', 'proveedor', 'orden_compra', 'forma_pago']

    def __init__(self, *args, **kwargs):
        staff_profile = kwargs.pop('staff_profile', None) 
        super(EntradaBodegaForm, self).__init__(*args, **kwargs)
        if staff_profile:
            self.fields['proveedor'].queryset = Proveedor.objects.filter(negocio=staff_profile.negocio)


        
class EntradaBodegaProductoForm(forms.ModelForm):
    class Meta:
        model = EntradaBodegaProducto
        fields = ['producto', 'cantidad_recibida', 'precio_total']
    
    def __init__(self, *args, **kwargs):
        almacen = kwargs.pop('almacen', None) 
        super(EntradaBodegaProductoForm, self).__init__(*args, **kwargs)
        if almacen:
            self.fields['producto'].queryset = Producto.objects.filter(almacen=almacen)

       
            
class DevolucionProductoForm(forms.ModelForm):
    class Meta:
        model = ProductosDevueltos
        fields = ['producto', 'cantidad_devuelta', 'motivo_devolucion']
        widgets = {
            'motivo_devolucion': forms.Textarea(attrs={'placeholder': 'Ingrese el motivo de la devolución'}),
            'cantidad_devuelta': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        productos_queryset = kwargs.pop('productos_queryset', None)
        super().__init__(*args, **kwargs)
        if productos_queryset is not None:
            self.fields['producto'].queryset = productos_queryset

class NegocioForm(forms.ModelForm):
    rut_empresa = forms.CharField(
        max_length=12,
        required=True,
        label="RUT Empresa",
        error_messages={
            'required': 'Por favor, ingresa un RUT válido.',
            'max_length': 'El RUT no puede exceder los 12 caracteres.'
        }
    )
    almacen_direccion = forms.CharField(
        max_length=255, 
        required=True, 
        label="Dirección del Almacén"
    )

    membresia = forms.ModelChoiceField(
        queryset=Membresia.objects.all(),
        required=True,
        label="Tipo de Membresía",
        help_text="Selecciona una membresía para este negocio."
    )

    class Meta:
        model = Negocio
        fields = ['nombre', 'giro', 'direccion', 'telefono', 'rut_empresa', 'is_mayorista', 'almacen_direccion', 'membresia']
        widgets = {
            'is_mayorista': forms.CheckboxInput(),
        }

    def clean_rut_empresa(self):
        rut = self.cleaned_data.get('rut_empresa')
        if not validar_rut_empresa(rut):
            raise ValidationError("El RUT ingresado no es válido.")
        return rut

    def save(self, commit=True):
        negocio = super().save(commit=False)
        if commit:
            negocio.save()
        return negocio



class ProveedorForm(forms.ModelForm):
    rut_empresa = forms.CharField(
        max_length=12,
        required=True,
        label="RUT Empresa",
        error_messages={
            'required': 'Por favor, ingresa un RUT válido.',
            'max_length': 'El RUT no puede exceder los 12 caracteres.'
        }
    )
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut_empresa', 'telefono', 'correo']

    def clean_rut_empresa(self):
        rut = self.cleaned_data.get('rut_empresa')
        if not validar_rut_empresa(rut):
            raise ValidationError("El RUT ingresado no es válido.")
        return rut
    
    def save(self, commit=True):
        proveedor = super().save(commit=False)
        if commit:
            proveedor.save()
        return proveedor


class ProductoFormBoleta(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'categoria', 'precio', 'stock']
        widgets = {
            'marca': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class CompraFacturaForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['medio_pago', 'glosa']
        widgets = {
            'glosa': forms.Textarea(attrs={'required': True, 'placeholder': 'Ingrese una descripción o detalles adicionales'}),
        }


class RegistroUbicacionForm(forms.Form):
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=True, label="Región")
    provincia = forms.ModelChoiceField(queryset=Provincia.objects.none(), required=True, label="Provincia")
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.none(), required=True, label="Comuna")

    def __init__(self, *args, **kwargs):
        region_id = kwargs.pop('region_id', None)
        provincia_id = kwargs.pop('provincia_id', None)
        super().__init__(*args, **kwargs)

        if region_id:
            self.fields['provincia'].queryset = Provincia.objects.filter(region_id=region_id)
        if provincia_id:
            self.fields['comuna'].queryset = Comuna.objects.filter(provincia_id=provincia_id)



class StaffProfileForBossForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        
        fields = ['rut', 'direccion', 'telefono'] 
        labels = {
            'rut': 'RUT',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'negocio': 'Negocio',
        }

    def __init__(self, *args, **kwargs):
        negocio = kwargs.pop('negocio', None) 
        super().__init__(*args, **kwargs)
        if negocio:
            self.fields['negocio'].initial = negocio
            self.fields['negocio'].widget = forms.HiddenInput()

