// Seleccionar el botón de toggle y el sidebar
const sidebarToggle = document.querySelector('.sidebar-toggle');
const sidebar = document.querySelector('.navbar-side');
const mainContent = document.querySelector('.main-content');

// Función para alternar el sidebar mediante el botón en pantallas pequeñas
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('show');
    if (sidebar.classList.contains('show')) {
        sidebar.style.width = '100%'; // Sidebar ocupa toda la pantalla en pantallas pequeñas
        mainContent.style.marginLeft = '0'; // Ajuste del contenido
    } else {
        sidebar.style.width = '0'; // Sidebar colapsado en pantallas pequeñas
        mainContent.style.marginLeft = '0'; // Ajuste del contenido
    }
});

// Función para ajustar el sidebar según el tamaño de la ventana
function handleResize() {
    if (window.innerWidth > 768) {
        sidebar.style.width = '60px'; // Sidebar colapsado por defecto en pantallas grandes
        mainContent.style.marginLeft = '60px'; // Ajuste del contenido en pantallas grandes
        sidebar.classList.remove('show'); // Remover clase 'show' en pantallas grandes
        sidebarToggle.style.display = 'none'; // Ocultar el botón de toggle en pantallas grandes

        // Añadir evento hover en pantallas grandes
        sidebar.addEventListener('mouseenter', handleHoverExpand);
        sidebar.addEventListener('mouseleave', handleHoverCollapse);

    } else {
        // Remover el evento hover en pantallas pequeñas para evitar interferencias
        sidebar.removeEventListener('mouseenter', handleHoverExpand);
        sidebar.removeEventListener('mouseleave', handleHoverCollapse);

        // Restaurar el estado del sidebar en pantallas pequeñas
        if (!sidebar.classList.contains('show')) {
            sidebar.style.width = '0'; // Sidebar colapsado en pantallas pequeñas
            mainContent.style.marginLeft = '0'; // Ajuste del contenido en pantallas pequeñas
        }
        sidebarToggle.style.display = 'block'; // Mostrar el botón de toggle en pantallas pequeñas
    }
}

// Función para expandir el sidebar al pasar el puntero (pantallas grandes)
function handleHoverExpand() {
    sidebar.style.width = '250px'; // Sidebar expandido al pasar el puntero en pantallas grandes
    mainContent.style.marginLeft = '250px';
}

// Función para colapsar el sidebar al retirar el puntero (pantallas grandes)
function handleHoverCollapse() {
    sidebar.style.width = '60px'; // Colapsar el sidebar al quitar el puntero en pantallas grandes
    mainContent.style.marginLeft = '60px';
}

// Ejecutar la función al cargar la página y al cambiar el tamaño de la ventana
window.addEventListener('resize', handleResize);
window.addEventListener('load', handleResize);
