document.addEventListener('DOMContentLoaded', () => {
    let sidebar = document.getElementById('sidebar');
    let toc = sidebar.querySelector('ul');
    let allReferences = toc.querySelectorAll('a.reference.internal');

    for (let ref of allReferences) {
        let next = ref.nextElementSibling;
        if (next && next.tagName === "UL") {
            let icon = document.createElement('span');
            icon.className = 'fas fa-chevron-down';
            icon.addEventListener('click', () => {
                if (icon.classList.contains('fa-chevron-down')) {
                    icon.classList.remove('fa-chevron-down'); // safari doesn't support .replace yet(!)
                    icon.classList.add('fa-chevron-right');
                    icon.nextElementSibling.style.display = "block";
                } else {
                    icon.classList.remove('fa-chevron-right'); // safari doesn't support .replace yet(!)
                    icon.classList.add('fa-chevron-down');
                    icon.nextElementSibling.style.display = "none";
                }
            })
            ref.parentNode.insertBefore(icon, ref);
        }
    }
});
