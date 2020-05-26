const COPY = "Copy";
const COPIED = "Copied!";

var copy = (obj) => {
  navigator.clipboard.writeText(obj.children[1].innerText);

  obj.children[0].textContent = COPIED;
  setTimeout(() => (obj.children[0].textContent = COPY), 2500);
};

document.addEventListener("DOMContentLoaded", () => {
  let allCodeblocks = document.querySelectorAll("div[class='highlight']");

  for (let codeblock of allCodeblocks) {
      codeblock.parentNode.className += " relative-copy";
      let copyEl = document.createElement("span");
      copyEl.onclick = () => copy(codeblock);
      copyEl.className = "copy";
      copyEl.textContent = COPY;
      codeblock.prepend(copyEl);
  }
});
