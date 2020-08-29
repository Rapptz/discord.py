'use-strict';

let settingsModal;

function updateSetting(element) {
  let value;
  switch (element.type) {
    case 'checkbox':
      localStorage.setItem(element.name, element.checked);
      value = element.checked;
      break;
    case 'radio':
      localStorage.setItem(element.name, `"${element.value}"`);
      value = element.value;
      break;
  }
  if (element.name in settings) {
    settings[element.name]['setter'](value);
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
  if (value === 'automatic') {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }
  else {
    document.documentElement.setAttribute('data-theme', value);
  }
}

const settings = {
  useSerifFont: {
    settingType: 'checkbox',
    defaultValue: false,
    setter: getRootAttributeToggle('font', 'serif')
  },
  setTheme: {
    settingType: 'radio',
    defaultValue: 'automatic',
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

  settingsModal = document.querySelector('div#settings.modal');

  Object.entries(settings).forEach(([name, setting]) => {
    let { settingType, defaultValue, ..._ } = setting;
    let value = LoadSetting(name, defaultValue);
    if (settingType === 'checkbox') {
      let element = document.querySelector(`input[name=${name}]`);
      element.checked = value;
    } else {
      let element = document.querySelector(`input[name=${name}][value=${value}]`);
      element.checked = true;
    }
  });

});