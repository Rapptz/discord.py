"use-strict";

let settingsModal;

class Setting {
  constructor(name, defaultValue, setter, waitsForDOM = false) {
    this.name = name;
    this.defaultValue = defaultValue;
    this.setValue = setter;
    this.waitsForDOM = waitsForDOM;
  }

  setElement() {
    throw new TypeError("Abstract methods should be implemented.");
  }

  load() {
    let value = JSON.parse(localStorage.getItem(this.name));
    this.value = value === null ? this.defaultValue : value;
    try {
      this.setValue(this.value);
    } catch (error) {
      console.error(
        `Failed to apply setting "${this.name}" With value:`,
        this.value
      );
      console.error(error);
    }
  }

  update() {
    throw new TypeError("Abstract methods should be implemented.");
  }
}

class CheckboxSetting extends Setting {
  setElement() {
    let element = document.querySelector(`input[name=${this.name}]`);
    element.checked = this.value;
  }

  update(element) {
    localStorage.setItem(this.name, element.checked);
    this.setValue(element.checked);
  }
}

class RadioSetting extends Setting {
  setElement() {
    let element = document.querySelector(
      `input[name=${this.name}][value=${this.value}]`
    );
    element.checked = true;
  }

  update(element) {
    localStorage.setItem(this.name, `"${element.value}"`);
    this.setValue(element.value);
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

function setTheme(value) {
  if (value === "automatic") {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
    }
  } else {
    document.documentElement.setAttribute("data-theme", value);
  }
}

function toggleClassicAPIRef(add) {
  if (apiReference) {
    if (apiReference.parentElement.tagName !== "MAIN") {
      let event = new CustomEvent("APIRefStyle", { detail: { classic: true } });
      window.dispatchEvent(event);
      enableScroll = add;
      return;
    }
    let event = new CustomEvent("APIRefStyle", { detail: { classic: add } });
    window.dispatchEvent(event);
    enableScroll = add;
  } else {
    enableScroll = true;
  }
}

const settings = [
  new CheckboxSetting(
    "useSerifFont",
    false,
    getRootAttributeToggle("font", "serif")
  ),
  new RadioSetting("setTheme", "automatic", setTheme),
  new CheckboxSetting("useClassicAPIRef", false, toggleClassicAPIRef, true),
];

function updateSetting(element) {
  let setting = settings.find((s) => s.name == element.name);
  if (setting) {
    setting.update(element);
  }
}

for (const setting of settings) {
  if (!setting.waitsForDOM) {
    setting.load();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  settingsModal = new Modal(document.querySelector("div#settings.modal"));
  for (const setting of settings) {
    if (setting.waitsForDOM) {
      setting.load();
    }
    setting.setElement();
  }
});
