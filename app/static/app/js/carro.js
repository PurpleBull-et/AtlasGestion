document.addEventListener('DOMContentLoaded', function () {
    // Obtener el token CSRF desde las cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Mostrar mensaje de estado (cargando o error)
    function mostrarMensaje(mensaje, tipo = 'info') {
        const mensajeDiv = document.createElement('div');
        mensajeDiv.classList.add('mensaje', `mensaje-${tipo}`);
        mensajeDiv.innerText = mensaje;
        document.body.appendChild(mensajeDiv);
        setTimeout(() => {
            mensajeDiv.remove(); // Eliminar el mensaje después de unos segundos
        }, 3000);
    }

    // Guardar la posición del scroll
    function guardarPosicionScroll() {
        return window.scrollY;
    }

    // Restaurar la posición del scroll
    function restaurarPosicionScroll(posicion) {
        window.scrollTo(0, posicion);
    }

    // Actualizar el carrito con CSRF Token
    function actualizarCarrito(url, csrfToken) {
        const posicionScroll = guardarPosicionScroll();
        mostrarMensaje('Actualizando carrito...', 'info');  // Mostrar mensaje de carga

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta');
            }
            return response.json();
        })
        .then(data => {
            if (data.carrito_html) {
                document.querySelector('.cart-section').innerHTML = data.carrito_html;
                agregarEventosCarrito(); // Reasignar eventos
                restaurarPosicionScroll(posicionScroll);
                mostrarMensaje('Carrito actualizado correctamente', 'success');  // Mostrar mensaje de éxito
            } else {
                throw new Error('Datos del carrito no válidos');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Hubo un problema al actualizar el carrito. Por favor, intenta de nuevo.', 'error');
        });
    }

    // Función para manejar los formularios del carrito
    function manejarFormularioCarrito(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const url = form.action;
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value || csrftoken;
        
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true; // Deshabilitar el botón mientras se procesa la solicitud
        
        actualizarCarrito(url, csrfToken)
            .finally(() => {
                submitButton.disabled = false; // Habilitar el botón nuevamente después de la solicitud
            });
    }

    // Asignar eventos a los formularios del carrito
    function agregarEventosCarrito() {
        document.querySelectorAll('.form-agregar').forEach(form => {
            form.addEventListener('submit', manejarFormularioCarrito);
        });
        document.querySelectorAll('.form-restar').forEach(form => {
            form.addEventListener('submit', manejarFormularioCarrito);
        });
        document.querySelectorAll('.form-eliminar').forEach(form => {
            form.addEventListener('submit', manejarFormularioCarrito);
        });
    }

    agregarEventosCarrito();

    // Reasignar eventos después de actualizar los productos filtrados con AJAX
    document.querySelector('select[name="categoria"]').addEventListener('change', function () {
        const categoria = this.value;
        mostrarMensaje('Filtrando productos...', 'info');
        fetch(`/home/?categoria=${categoria}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#productos-lista').innerHTML = data.html;
            agregarEventosCarrito(); // Reasignar los eventos a los nuevos productos
            mostrarMensaje('Productos filtrados correctamente', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error al filtrar productos. Intenta de nuevo.', 'error');
        });
    });

    // Reasignar eventos cuando se usa la búsqueda manual
    document.querySelector('input[name="buscar"]').addEventListener('input', function () {
        const query = this.value;
        const categoria = document.querySelector('select[name="categoria"]').value;
        mostrarMensaje('Buscando productos...', 'info');
        fetch(`/home/?buscar=${query}&categoria=${categoria}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#productos-lista').innerHTML = data.html;
            agregarEventosCarrito(); // Reasignar los eventos a los nuevos productos
            mostrarMensaje('Búsqueda completada', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error en la búsqueda. Intenta de nuevo.', 'error');
        });
    });

    // Cargar carrito al inicio (dinámicamente si es necesario)
    fetch("/carrito/")
        .then(response => response.text())
        .then(html => {
            document.getElementById('carrito-container').innerHTML = html;
            agregarEventosCarrito();  // Reasignar eventos una vez que el carrito se carga
        })
        .catch(error => {
            console.error('Error al cargar el carrito:', error);
            mostrarMensaje('Error al cargar el carrito. Reintenta más tarde.', 'error');
        });
});
