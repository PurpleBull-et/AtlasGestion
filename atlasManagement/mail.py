import os
import sys
import django
from django.core.mail import send_mail

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlasManagement.settings')
django.setup()

def enviar_correo_prueba():
    send_mail(
        'Correo de prueba',
        'Este es un correo de prueba enviado desde Django.',
        'contacto@atlasgestion.cl',  # Remitente
        ['alan.vcntbull@gmail.com'],  # Destinatario
        fail_silently=False,
    )

if __name__ == "__main__":
    enviar_correo_prueba()
