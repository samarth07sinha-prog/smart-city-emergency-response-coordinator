const preview = document.querySelector("[data-map-preview]");
const options = preview.querySelectorAll("button[data-plan]");

for (const option of options) {
  option.addEventListener("click", () => {
    preview.dataset.plan = option.dataset.plan;
    for (const button of options) {
      button.setAttribute("aria-pressed", String(button === option));
    }
  });
}
