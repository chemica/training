(() => {
  const form = document.querySelector("#request-path-check");
  const output = document.querySelector("#request-path-result");
  if (!form || !output) return;

  const answers = {
    authenticate: "gateway",
    execute: "lambda",
    buffer: "sqs",
    persist: "s3"
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const misses = Object.entries(answers).filter(([key, value]) => data.get(key) !== value);
    if (misses.length === 0) {
      output.innerHTML = "<strong>Path established.</strong> You placed identity, execution, buffering, and storage at appropriate seams. Now explain aloud why Lambda should not wait synchronously for a slow ingestion job.";
      output.style.color = "var(--good)";
    } else {
      const names = misses.map(([key]) => key).join(", ");
      output.innerHTML = `<strong>Revisit:</strong> ${names}. Trace the request from the public boundary inward and ask which component owns each responsibility.`;
      output.style.color = "var(--accent)";
    }
  });
})();
