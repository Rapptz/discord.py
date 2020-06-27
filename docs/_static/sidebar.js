document.addEventListener('DOMContentLoaded', () => {
    let sidebar = document.getElementById('sidebar');
    let toc = sidebar.querySelector('ul');
    let allReferences = toc.querySelectorAll('a.reference.internal:not([href="#"])');

    for (let ref of allReferences) {
        let next = ref.nextElementSibling;
        if (next && next.tagName === "UL") {
            let icon = document.createElement('span');
            icon.className = 'fas fa-chevron-down collapsible-arrow';
            icon.addEventListener('click', () => {
                if (icon.classList.contains('fa-chevron-down')) {
                    icon.classList.remove('fa-chevron-down'); // safari doesn't support .replace yet(!)
                    icon.classList.add('fa-chevron-left');
                    let children = icon.nextElementSibling; 
                    // <arrow><heading> 
                    // --> <arrow><children>
                    children.style.display = "none";
                } else {
                    icon.classList.remove('fa-chevron-left');
                    icon.classList.add('fa-chevron-down');
                    let children = icon.nextElementSibling; 
                    children.style.display = "block";
                }
            })
            ref.parentNode.insertBefore(icon, ref.nextElementSibling);
        }
    }
});
