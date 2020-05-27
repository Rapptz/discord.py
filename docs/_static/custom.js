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
}

function setFont(useSans) {
  if (useSans === true) {
    document.body.classList.add('sans');
  } else {
    document.body.classList.remove('sans');
  }
}

const settings = [['useSansFont', setFont]];

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

  settings.forEach(([settingName, settingFunction]) => {
    let settingValue = JSON.parse(localStorage.getItem(settingName));
    settingFunction(settingValue);
    let element = document.querySelector(`input[name=${settingName}]`);
    if (element) {
      element.checked = settingValue === true;
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