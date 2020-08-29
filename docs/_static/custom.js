'use-strict';

let activeModal = null;
let activeLink = null;
let bottomHeightThreshold, sections;
let hamburgerToggle;
let sidebar;
let mobileSearch;
let openSearchButton;
let closeSearchButton;

function resizeSidebar() {
  let rect = sidebar.getBoundingClientRect();
  sidebar.style.height = `calc(100vh - 1em - ${rect.top + document.body.offsetTop}px)`;
}

function closeModal(modal) {
  activeModal = null;
  modal.hidden = true;
}

function openModal(modal) {
  if (activeModal) {
    closeModal(activeModal);
  }

  activeModal = modal;
  modal.hidden = false;
}

function openSearch() {
  openSearchButton.hidden = true;
  closeSearchButton.hidden = false;
  mobileSearch.style.width = "50vw";
}

function closeSearch() {
  openSearchButton.hidden = false;
  closeSearchButton.hidden = true;
  mobileSearch.style.width = "0px";
}

function changeDocumentation(element) {
  window.location = element.value;
}

document.addEventListener('DOMContentLoaded', () => {

  bottomHeightThreshold = document.documentElement.scrollHeight - 30;
  sections = document.querySelectorAll('section');
  hamburgerToggle = document.getElementById('hamburger-toggle');
  sidebar = document.getElementById('sidebar');
  mobileSearch = document.querySelector('nav .mobile-only.search');
  openSearchButton = document.getElementById('open-search');
  closeSearchButton = document.getElementById('close-search');

  resizeSidebar();

  sidebar.addEventListener('click', (e) => {
    // If we click a navigation, close the hamburger menu
    if (e.target.tagName == 'A' && sidebar.classList.contains('sidebar-toggle')) {
      sidebar.classList.remove('sidebar-toggle');
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
  })

  hamburgerToggle.addEventListener('click', (e) => {
    sidebar.classList.toggle('sidebar-toggle');
    let button = hamburgerToggle.firstElementChild;
    if (button.textContent == 'menu') {
      button.textContent = 'close';
    }
    else {
      button.textContent = 'menu';
    }
  });

  const tables = document.querySelectorAll('.py-attribute-table[data-move-to-id]');
  tables.forEach(table => {
    let element = document.getElementById(table.getAttribute('data-move-to-id'));
    let parent = element.parentNode;
    // insert ourselves after the element
    parent.insertBefore(table, element.nextSibling);
  });
});

window.addEventListener('scroll', () => {
  let currentSection = null;

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

  if (activeLink) {
    activeLink.parentElement.classList.remove('active');
  }

  if (currentSection) {
    activeLink = document.querySelector(`#sidebar a[href="#${currentSection.id}"]`);
    if (activeLink) {
      let headingChildren = activeLink.parentElement.parentElement;
      let heading = headingChildren.previousElementSibling.previousElementSibling;

      if (heading && headingChildren.style.display === 'none') {
        activeLink = heading;
      }
      activeLink.parentElement.classList.add('active');
    }
  }

  resizeSidebar();
});

document.addEventListener('keydown', (event) => {
  if (event.keyCode == 27 && activeModal) {
    closeModal(activeModal);
  }
});
