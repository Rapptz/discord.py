const COPY = "fa-copy";
const COPIED = "fa-clipboard-check";

const copy = async (obj) => {
  // <div><span class="copy">  <i class="fas ...">the icon element</i>  </span><pre> code </pre></div>
  await navigator.clipboard.writeText(obj.children[1].innerText).then(
    () => {
      let icon = obj.children[0].children[0];
      icon.className = icon.className.replace(COPY, COPIED);
      setTimeout(() => (icon.className = icon.className.replace(COPIED, COPY)), 2500);
    },
    (r) => alert('Could not copy codeblock:\n' + r.toString())
  );
};

document.addEventListener("DOMContentLoaded", () => {
  let allCodeblocks = document.querySelectorAll("div[class='highlight']");

  for (let codeblock of allCodeblocks) {
      codeblock.parentNode.className += " relative-copy";
      let copyEl = document.createElement("span");
      copyEl.addEventListener('click', () => copy(codeblock));
      copyEl.className = "copy";

      let copyIcon = document.createElement("i");
      copyIcon.className = "fas " + COPY;
      copyEl.append(copyIcon);

      codeblock.prepend(copyEl);
  }
});
