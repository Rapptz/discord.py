let classic = null;
let apiRef;

document.addEventListener("readystatechange", () => {
  if (document.readyState === "interactive")
    apiRef = document.getElementById("api-reference");
});

window.addEventListener("APIRefStyle", (e) => {
  let obj;
  if (e.detail.classic) {
    if (classic !== null) {
      expandAll();
    }
    obj = resolveClassicHash(window.location.href);
  } else {
    collapseSections();
    collapseClasses();

    obj = resolveHash(window.location.href);
  }
  apiRef.style.display = "block";
  obj.scrollIntoView();
  classic = e.detail.classic;
});

window.addEventListener("hashchange", (ev) => {
  ev.preventDefault();
  if (apiRef) {
    let func = resolveHash;
    if (classic) {
      func = resolveClassicHash;
    }
    func(ev.newURL).scrollIntoView();
    sidebar.setActiveLink(getCurrentSection());
  }
});

document.addEventListener("keydown", (ev) => {
  if (!apiRef) return;

  let currSection = apiRef.querySelector(
    "section[style='display: block;']:not(.class-anchor-offset)"
  );
  let hasClasses = currSection.querySelectorAll("section");
  if (hasClasses.length <= 1) return; // 0 and 1: no classes or only one class

  if (ev.key === "ArrowLeft") {
    previousClass(currSection)();
    ev.preventDefault();
  } else if (ev.key === "ArrowRight") {
    nextClass(currSection)();
    ev.preventDefault();
  }
});

/// classic-api-ref
function resolveClassicHash(url) {
  let hash = new URL(url).hash.slice(1);
  return document.getElementById(hash) || apiRef;
}

function expandAll() {
  let sections = apiRef.querySelectorAll("section");
  let controls = document.querySelectorAll("div.controls");

  for (let sect of sections) {
    sect.style.display = "block";
  }

  for (let control of controls) {
    control.remove();
  }
}

/// neo-api-ref
function resolveHash(url) {
  let obj = resolveClassicHash(url);

  if (obj === apiRef) {
    let firstSection = Array.from(apiRef.children).find(
      (v) => v.tagName === "SECTION"
    );
    switchSection(firstSection);
    return apiRef;
  }

  if (obj.tagName === "SECTION") {
    if (obj.parentNode === apiRef) {
      // section
      switchSection(obj);
    } else if (obj.parentNode.parentNode === apiRef) {
      // class
      switchSection(obj.parentNode);
      switchClass(obj);
    }
  } else {
    // class attribute
    let _class = obj.closest("section");
    switchSection(_class.parentNode);
    switchClass(_class);
  }
  return obj;
}

function collapseClasses() {
  let sections = apiRef.querySelectorAll("section");
  let currSect;
  let i = 0;
  for (let sect of sections) {
    if (sect.parentNode === apiRef) {
      currSect = sect;
      i = 0;
    } else {
      if (i === 0) {
        sect.style.display = "block";

        let controls = document.createElement("div");
        controls.className = "controls";

        let prev = document.createElement("span");
        prev.className = "material-icons control-left";
        prev.textContent = "arrow_back";
        prev.title = "previous";
        prev.addEventListener("click", previousClass(currSect));

        let next = document.createElement("span");
        next.className = "material-icons control-right";
        next.textContent = "arrow_forward";
        next.title = "next";
        next.addEventListener("click", nextClass(currSect));

        controls.append(prev, next);
        sect.insertAdjacentElement("beforebegin", controls);
      } else {
        sect.style.display = "none";
      }
      if (!sect.classList.contains("class-anchor-offset")) {
        sect.classList.add("class-anchor-offset");
      }
      i++;
    }
  }
}

function collapseSections() {
  let sections = Array.from(apiRef.children).filter(
    (el) => el.tagName === "SECTION"
  );

  sections.forEach((v, i) => (v.style.display = i === 0 ? "block" : "none"));
}

function nextClass(sect) {
  return () => {
    let classes = Array.from(sect.querySelectorAll("section"));
    let blockedClassIndex = classes.findIndex(
      (el) => el.style.display === "block"
    );

    let index =
      blockedClassIndex === classes.length - 1 ? 0 : blockedClassIndex + 1;
    window.location.hash = classes[index].id;
  };
}

function previousClass(sect) {
  return () => {
    let classes = Array.from(sect.querySelectorAll("section"));
    let blockedClassIndex = classes.findIndex(
      (el) => el.style.display === "block"
    );

    let index =
      blockedClassIndex === 0 ? classes.length - 1 : blockedClassIndex - 1;
    window.location.hash = classes[index].id;
  };
}

function switchSection(sect) {
  let blockedSection = Array.from(apiRef.children).find(
    (el) => el.style.display === "block" && el.tagName === "SECTION"
  );

  if (blockedSection) {
    blockedSection.style.display = "none";
  }
  sect.style.display = "block";
}

function switchClass(obj) {
  let parent = obj.parentNode;
  let blockedClass = Array.from(parent.children).find(
    (el) => el.style.display === "block" && el.tagName === "SECTION"
  );

  if (blockedClass) {
    blockedClass.style.display = "none";
  }
  obj.style.display = "block";
}
