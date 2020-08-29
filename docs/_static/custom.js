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
  switch (element.type) {
    case "checkbox":
      localStorage.setItem(element.name, element.checked);
      break;
    case "radio":
      localStorage.setItem(element.name, `"${element.value}"`);
      break;
  }
  if (element.name in settings) {
    settings[element.name]["setter"](element.value);
  }
}

function LoadSetting(name, defaultValue) {
  let value = JSON.parse(localStorage.getItem(name));
  return value === null ? defaultValue : value;
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

function setTheme(value) {
  if (value === "automatic") {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)')) {
      document.documentElement.setAttribute(`data-theme`, "dark");
    }
  }
  else {
    document.documentElement.setAttribute(`data-theme`, value);
  }
}

const settings = {
  useSerifFont: {
    settingType: "checkbox",
    defaultValue: false,
    setter: getRootAttributeToggle('font', 'serif')
  },
  setTheme: {
    settingType: "radio",
    defaultValue: "automatic",
    setter: setTheme
  }
};

Object.entries(settings).forEach(([name, setting]) => {
  let { defaultValue, setter, ..._ } = setting;
  let value = LoadSetting(name, defaultValue);
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

  Object.entries(settings).forEach(([name, setting]) => {
    let { settingType, defaultValue, ..._ } = setting;
    let value = LoadSetting(name, defaultValue);
    if (settingType === "checkbox") {
      let element = document.querySelector(`input[name=${name}]`);
      element.checked = value;
    } else {
      let element = document.querySelector(`input[name=${name}][value=${value}]`);
      element.checked = true;
    }
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

      if (heading && headingChildren.style.display === "none") {
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
