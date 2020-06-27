document.addEventListener('DOMContentLoaded', () => {
    let sidebar = document.getElementById('sidebar');
    let toc = sidebar.querySelector('ul');
    let allReferences = toc.querySelectorAll('a.reference.internal:not([href="#"])');

    for (let ref of allReferences) {
        let next = ref.nextElementSibling;
        if (next && next.tagName === "UL") {
            let icon = document.createElement('span');
            icon.className = 'fas fa-chevron-down collapsible-arrow';
            ref.classList.add('ref-internal-padding')
            if (next.parentElement.tagName == "LI") {
                next.parentElement.classList.add('no-list-style')
            }
            icon.addEventListener('click', () => {
                if (icon.classList.contains('fa-chevron-down')) {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-right');
                    let children = icon.nextElementSibling.nextElementSibling; 
                    // <arrow><heading> 
                    // --> <square><children>
                    children.style.display = "none";
                } else {
                    icon.classList.remove('fa-chevron-right');
                    icon.classList.add('fa-chevron-down');
                    let children = icon.nextElementSibling.nextElementSibling; 
                    children.style.display = "block";
                }
            })
            ref.parentNode.insertBefore(icon, ref);
        }
    }
});
