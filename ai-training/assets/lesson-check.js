(() => {
  for (const form of document.querySelectorAll("form[data-answer-key]")) {
    const result = form.querySelector("[data-result]");
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const key = JSON.parse(form.dataset.answerKey);
      const data = new FormData(form);
      const missed = Object.entries(key).filter(([name, answer]) => data.get(name) !== answer);
      if (missed.length === 0) {
        result.innerHTML = "<strong>Recall established.</strong> Continue to the application task.";
        result.style.color = "var(--good)";
      } else {
        result.innerHTML = `<strong>Review needed:</strong> ${missed.map(([name]) => name).join(", ")}. Return to the named concept, then try again from memory.`;
        result.style.color = "var(--accent)";
      }
    });
  }
})();
