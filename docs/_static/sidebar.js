function collapseSection(icon) {
    icon.classList.remove('expanded');
    icon.classList.add('collapsed');
    icon.innerText = 'chevron_right';
    let children = icon.nextElementSibling.nextElementSibling;
    // <arrow><heading> 
    // --> <square><children>
    children.style.display = "none";
}

function expandSection(icon) {
    icon.classList.remove('collapse');
    icon.classList.add('expanded');
    icon.innerText = 'expand_more';
    let children = icon.nextElementSibling.nextElementSibling;
    children.style.display = "block";
}

document.addEventListener('DOMContentLoaded', () => {
    let sidebar = document.getElementById('sidebar');
    let toc = sidebar.querySelector('ul');
    let allReferences = toc.querySelectorAll('a.reference.internal:not([href="#"])');

    for (let ref of allReferences) {

        let next = ref.nextElementSibling;
        
        if (next && next.tagName === "UL") {
            
            let icon = document.createElement('span');
            icon.className = 'material-icons collapsible-arrow expanded';
            icon.innerText = 'expand_more';
            
            if (next.parentElement.tagName == "LI") {
                next.parentElement.classList.add('no-list-style')
            }
            
            icon.addEventListener('click', () => {
                if (icon.classList.contains('expanded')) {
                    collapseSection(icon);
                } else {
                    expandSection(icon);
                }
            })

            ref.classList.add('ref-internal-padding')
            ref.parentNode.insertBefore(icon, ref);
        }
    }
});
