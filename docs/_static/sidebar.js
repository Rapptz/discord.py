class Sidebar {
  constructor(element) {
    this.element = element;
    this.activeLink = null;

    this.element.addEventListener('click', (e) => {
      // If we click a navigation, close the hamburger menu
      if (e.target.tagName == 'A' && this.element.classList.contains('sidebar-toggle')) {
        this.element.classList.remove('sidebar-toggle');
        let button = hamburgerToggle.firstElementChild;
        button.textContent = 'menu';

        // Scroll a little up to actually see the header
        // Note: this is generally around ~55px
        // A proper solution is getComputedStyle but it can be slow
        // Instead let's just rely on this quirk and call it a day
        // This has to be done after the browser actually processes
        // the section movement
        setTimeout(() => window.scrollBy(0, -100), 75);
      }
    });
  }

  createCollapsableSections() {
    let toc = this.element.querySelector('ul');
    if (!toc) {
      return
    }
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
            this.collapseSection(icon);
          } else {
            this.expandSection(icon);
          }
        })

        ref.classList.add('ref-internal-padding')
        ref.parentNode.insertBefore(icon, ref);
      }
    }
  }

  resize() {
    let rect = this.element.getBoundingClientRect();
    this.element.style.height = `calc(100vh - 1em - ${rect.top + document.body.offsetTop}px)`;
  }

  collapseSection(icon) {
    icon.classList.remove('expanded');
    icon.classList.add('collapsed');
    let children = icon.nextElementSibling.nextElementSibling;
    // <arrow><heading>
    // --> <square><children>
    setTimeout(() => children.style.display = "none", 75)
  }

  expandSection(icon) {
    icon.classList.remove('collapse');
    icon.classList.add('expanded');
    let children = icon.nextElementSibling.nextElementSibling;
    setTimeout(() => children.style.display = "block", 75)
  }

  setActiveLink(section) {
    if (this.activeLink) {
      this.activeLink.parentElement.classList.remove('active');
    }
    if (section) {
      this.activeLink = document.querySelector(`#sidebar a[href="#${section.id}"]`);
      if (this.activeLink) {
        let headingChildren = this.activeLink.parentElement.parentElement;
        let heading = headingChildren.previousElementSibling.previousElementSibling;

        if (heading && headingChildren.style.display === 'none') {
          this.activeLink = heading;
        }
        this.activeLink.parentElement.classList.add('active');
      }
    }
  }

}

function getCurrentSection() {
  let currentSection;
  if (window.scrollY + window.innerHeight > bottomHeightThreshold) {
    currentSection = sections[sections.length - 1];
  }
  else {
    if (sections) {
      sections.forEach(section => {
        let rect = section.getBoundingClientRect();
        if (rect.top + document.body.offsetTop < 1) {
          currentSection = section;
        }
      });
    }
  }
  return currentSection;
}

document.addEventListener('DOMContentLoaded', () => {
  sidebar = new Sidebar(document.getElementById('sidebar'));
  sidebar.resize();
  sidebar.createCollapsableSections();

  window.addEventListener('scroll', () => {
    sidebar.setActiveLink(getCurrentSection());
    sidebar.resize();
  });
});
