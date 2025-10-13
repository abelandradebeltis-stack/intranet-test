document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const menuToggles = document.querySelectorAll('.menu-toggle');

    // Lógica para alternar a visibilidade da sidebar
    const toggleSidebar = () => {
        sidebar.classList.toggle('is-collapsed');
    };

    // Adiciona o evento de clique a todos os botões de menu
    menuToggles.forEach(toggle => {
        toggle.addEventListener('click', toggleSidebar);
    });

    // Opcional: Manter o estado da sidebar (recolhida ou não) entre as páginas
    // Usando localStorage
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        sidebar.classList.add('is-collapsed');
    }

    // Salva o estado da sidebar sempre que for alterado
    sidebar.addEventListener('transitionend', () => {
        localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('is-collapsed'));
    });
});
