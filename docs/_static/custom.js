'use-strict';

let activeLink = null;
let bottomHeightThreshold, sections;

document.addEventListener('DOMContentLoaded', () => {
  bottomHeightThreshold = document.documentElement.scrollHeight - 30;
  sections = document.querySelectorAll('div.section');

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
    sections.forEach(section => {
      let rect = section.getBoundingClientRect();
      if (rect.top + document.body.scrollTop - 1 < window.scrollY) {
        currentSection = section;
      }
    });
  }

  if (activeLink) {
    activeLink.parentElement.classList.remove('active');
  }

  if (currentSection) {
    activeLink = document.querySelector(`.sphinxsidebar a[href="#${currentSection.id}"]`);
    activeLink.parentElement.classList.add('active');
  }

});