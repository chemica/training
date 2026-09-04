function assessHypothesis() {
  const fields = ['context','setup','trigger','invalidation'];
  const values = Object.fromEntries(fields.map(id => [id, document.getElementById(id).value.trim()]));
  const missing = fields.filter(id => values[id].length < 12);
  const output = document.getElementById('feedback');
  output.style.display = 'block';
  if (missing.length) {
    output.textContent = `Incomplete: strengthen ${missing.join(', ')}. Each needs a specific observation or condition—not a label.`;
    return;
  }
  const triggerHasCondition = /if|when|close|break|reclaim|hold|reject/i.test(values.trigger);
  const invalidationHasCondition = /if|when|close|break|below|above|fails?/i.test(values.invalidation);
  output.textContent = triggerHasCondition && invalidationHasCondition
    ? 'Structurally valid. Now ask: could another person apply these words to the same chart without guessing? Save your four lines and send them to your LLM teacher for critique.'
    : 'You filled every field, but the trigger and invalidation should be observable conditions. Rewrite them with “if/when price…” and a level or structural event.';
}

function revealCheck(button, answer) {
  const output = button.nextElementSibling;
  output.style.display = 'block';
  output.textContent = answer;
}

function answerTest(button, correct, explanation) {
  const box = button.closest('.exercise');
  box.querySelectorAll('button').forEach(b => b.disabled = true);
  const output = box.querySelector('.feedback');
  output.style.display = 'block';
  output.textContent = `${correct ? 'Correct.' : 'Not quite.'} ${explanation}`;
}
