/**
 * sidebar.js — Lógica de apertura/cierre del sidebar en móvil.
 *
 * Elementos requeridos en el DOM:
 *   #burger           – botón hamburguesa (topbar móvil)
 *   #sidebar          – barra lateral de navegación
 *   #sidebar-overlay  – fondo oscuro detrás del sidebar abierto
 */
document.addEventListener('DOMContentLoaded', () => {
  const burger  = document.getElementById('burger');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  function toggleSidebar() {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  }

  burger?.addEventListener('click', toggleSidebar);
  overlay?.addEventListener('click', closeSidebar);
});
