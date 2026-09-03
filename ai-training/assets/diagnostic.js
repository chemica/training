(() => {
  const form = document.querySelector("#diagnostic");
  const result = document.querySelector("#result");
  if (!form || !result) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const foundations = ["terminal", "git", "http", "code", "aws"]
      .reduce((sum, key) => sum + Number(data.get(key) || 0), 0);
    const profile = foundations <= 3 ? "new builder" : foundations <= 7 ? "developing builder" : "experienced builder";
    const payload = {
      profile,
      weekly_hours: data.get("weekly_hours") || "not answered",
      language: data.get("language") || "not answered",
      business_outcome: data.get("business_outcome") || "not answered",
      business_data: data.get("business_data") || "not answered",
      community: data.get("community") || "not answered"
    };
    localStorage.setItem("aws-course-diagnostic", JSON.stringify(payload));
    result.innerHTML = `<h3>Your provisional starting point: ${profile}</h3>
      <p>This is placement, not a score. Copy the summary below into your next message so the course can adapt.</p>
      <textarea readonly>${JSON.stringify(payload, null, 2)}</textarea>`;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  });
})();
