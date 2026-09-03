document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-answer]');
  if (!button) return;
  const exercise = button.closest('.exercise');
  const feedback = exercise.querySelector('.feedback');
  const correct = button.dataset.answer === 'correct';
  feedback.textContent = correct ? button.dataset.correctFeedback : button.dataset.incorrectFeedback;
  feedback.className = `feedback ${correct ? 'good' : 'bad'}`;
});
