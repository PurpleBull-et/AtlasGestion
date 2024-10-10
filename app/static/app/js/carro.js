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

    // Asegurarse de que todas las solicitudes AJAX incluyen el token CSRF
    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Actualizar el carrito con CSRF Token
    function actualizarCarrito(url, csrfToken) {
        const posicionScroll = guardarPosicionScroll();

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
            document.querySelector('.cart-section').innerHTML = data.carrito_html;
            agregarEventosCarrito(); // Reasignar eventos
            restaurarPosicionScroll(posicionScroll);
        })
        .catch(error => console.error('Error:', error));
    }

    // Función para manejar los formularios del carrito
    function manejarFormularioCarrito(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const url = form.action;
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value || csrftoken;
        actualizarCarrito(url, csrfToken); // Actualizar el carrito
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
        fetch(`/home/?categoria=${categoria}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#productos-lista').innerHTML = data.html;
            agregarEventosCarrito(); // Reasignar los eventos a los nuevos productos
        });
    });

    // Reasignar eventos cuando se usa la búsqueda manual
    document.querySelector('input[name="buscar"]').addEventListener('input', function () {
        const query = this.value;
        const categoria = document.querySelector('select[name="categoria"]').value;
        fetch(`/home/?buscar=${query}&categoria=${categoria}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#productos-lista').innerHTML = data.html;
            agregarEventosCarrito(); // Reasignar los eventos a los nuevos productos
        });
    });

    // Cargar carrito al inicio (dinámicamente si es necesario)
    fetch("/carrito/")
        .then(response => response.text())
        .then(html => {
            document.getElementById('carrito-container').innerHTML = html;
            agregarEventosCarrito();  // Reasignar eventos una vez que el carrito se carga
        });
});
