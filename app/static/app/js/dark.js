// JavaScript para togglear el modo oscuro
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('dark-mode-toggle');
    
    const isDarkMode = localStorage.getItem('dark-mode');
    
    if (isDarkMode === 'enabled') {
      document.body.classList.add('dark-mode');
    }
    
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('dark-mode', 'enabled');
      } else {
        localStorage.setItem('dark-mode', 'disabled');
      }
    });
  });
  

