"use strict";
// Server validation remains authoritative; focus helps keyboard users find errors.
document.addEventListener("DOMContentLoaded", () => {
  const invalid = document.querySelector(".field-invalid input");
  if (invalid) { invalid.setAttribute("aria-invalid", "true"); invalid.focus(); }
});
