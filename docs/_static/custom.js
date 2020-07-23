'use-strict';

let activeModal = null;
let activeLink = null;
let bottomHeightThreshold, sections;
let settingsModal;
let hamburgerToggle;
let sidebar;

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

function changeDocumentation(element) {
  window.location = element.value;
}

function updateSetting(element) {
  localStorage.setItem(element.name, element.checked);
  if (element.name in settings) {
    settings[element.name](element.checked);
  }
}

function getRootAttributeToggle(attributeName, valueName) {
  function toggleRootAttribute(set) {
    if (set) {
      document.documentElement.setAttribute(`data-${attributeName}`, valueName);
    } else {
      document.documentElement.removeAttribute(`data-${attributeName}`);
    }
  }
  return toggleRootAttribute;
}

const settings = {
  useSerifFont: getRootAttributeToggle('font', 'serif'),
  useDarkTheme: getRootAttributeToggle('theme', 'dark')
};

Object.entries(settings).forEach(([name, setter]) => {
  let value = JSON.parse(localStorage.getItem(name));
  try {
    setter(value);
  } catch (error) {
    console.error(`Failed to apply setting "${name}" With value:`, value);
    console.error(error);
  }
});

document.addEventListener('DOMContentLoaded', () => {

  bottomHeightThreshold = document.documentElement.scrollHeight - 30;
  sections = document.querySelectorAll('section');
  settingsModal = document.querySelector('div#settings.modal');
  hamburgerToggle = document.getElementById("hamburger-toggle");
  sidebar = document.getElementById("sidebar");

  resizeSidebar();

  sidebar.addEventListener("click", (e) => {
    // If we click a navigation, close the hamburger menu
    if (e.target.tagName == "A" && sidebar.classList.contains("sidebar-toggle")) {
      sidebar.classList.remove("sidebar-toggle");
      let button = hamburgerToggle.firstElementChild;
      button.textContent = "menu";

      // Scroll a little up to actually see the header
      // Note: this is generally around ~55px
      // A proper solution is getComputedStyle but it can be slow
      // Instead let's just rely on this quirk and call it a day
      // This has to be done after the browser actually processes
      // the section movement
      setTimeout(() => window.scrollBy(0, -100), 75);
    }
  })

  hamburgerToggle.addEventListener("click", (e) => {
    sidebar.classList.toggle("sidebar-toggle");
    let button = hamburgerToggle.firstElementChild;
    if (button.textContent == "menu") {
      button.textContent = "close";
    }
    else {
      button.textContent = "menu";
    }
  });

  const tables = document.querySelectorAll('.py-attribute-table[data-move-to-id]');
  tables.forEach(table => {
    let element = document.getElementById(table.getAttribute('data-move-to-id'));
    let parent = element.parentNode;
    // insert ourselves after the element
    parent.insertBefore(table, element.nextSibling);
  });

  Object.keys(settings).forEach(name => {
    let value = JSON.parse(localStorage.getItem(name));
    let element = document.querySelector(`input[name=${name}]`);
    if (element) {
      element.checked = value === true;
    }
  });
});

window.addEventListener('scroll', () => {
  let currentSection = null;

  if (window.scrollY + window.innerHeight > bottomHeightThreshold) {
    currentSection = sections[sections.length - 1];
  }
  else {
    sections.forEach(section => {
      let rect = section.getBoundingClientRect();
      if (rect.top + document.body.offsetTop < 1) {
        currentSection = section;
      }
    });
  }

  if (activeLink) {
    activeLink.parentElement.classList.remove('active');
  }

  if (currentSection) {
    activeLink = document.querySelector(`#sidebar a[href="#${currentSection.id}"]`);
    if (activeLink) {
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
