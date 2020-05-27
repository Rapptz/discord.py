'use-strict';

let activeModal = null;
let activeLink = null;
let bottomHeightThreshold, sections;
let settingsModal;

function closeModal(modal) {
  activeModal = null;
  modal.style.display = 'none';
}

function openModal(modal) {
  if (activeModal) {
    closeModal(activeModal);
  }

  activeModal = modal;
  modal.style.removeProperty('display');
}

function updateSetting(element) {
  localStorage.setItem(element.name, element.checked);
  if (element.name in settings) {
    settings[element.name](element.checked);
  }
}

function getBodyClassToggle(className) {
  function toggleBodyClass(add) {
    document.body.classList.toggle(className, add);
  }
  return toggleBodyClass;
}

const settings = {
  useSansFont: getBodyClassToggle('sans')
};

document.addEventListener('DOMContentLoaded', () => {

  bottomHeightThreshold = document.documentElement.scrollHeight - 30;
  sections = document.querySelectorAll('div.section');
  settingsModal = document.querySelector('div#settings.modal')

  const tables = document.querySelectorAll('.py-attribute-table[data-move-to-id]');
  tables.forEach(table => {
    let element = document.getElementById(table.getAttribute('data-move-to-id'));
    let parent = element.parentNode;
    // insert ourselves after the element
    parent.insertBefore(table, element.nextSibling);
  });

  Object.entries(settings).forEach(([name, setter]) => {
    let value = JSON.parse(localStorage.getItem(name));

    try {
      setter(value);
      let element = document.querySelector(`input[name=${name}]`);
      if (element) {
        element.checked = value === true;
      }
    } catch (error) {
      console.error(`Failed to apply setting "${name}" With value:`, value);
      console.error(error);
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
    activeLink = document.querySelector(`.sphinxsidebar a[href="#${currentSection.id}"]`);
    if (activeLink) {
      activeLink.parentElement.classList.add('active');
    }
  }
});

document.addEventListener('keydown', (event) => {
  if (event.keyCode == 27 && activeModal) {
    closeModal(activeModal);
  }
});
