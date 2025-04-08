// Selecionar todos os links do menu
const menuLinks = document.querySelectorAll('.menu a');

// Adicionar um evento de clique a cada link
menuLinks.forEach(link => {
    link.addEventListener('click', function(event) {
        // Remover a classe "active" de todos os links
        menuLinks.forEach(link => link.classList.remove('active'));

        // Adicionar a classe "active" ao link clicado
        this.classList.add('active');
    });
});