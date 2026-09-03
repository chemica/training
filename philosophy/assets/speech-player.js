(() => {
  const voiceSelect = document.querySelector('[data-speech-voice]');
  const rateInput = document.querySelector('[data-speech-rate]');
  const rateOutput = document.querySelector('[data-speech-rate-output]');
  const pitchInput = document.querySelector('[data-speech-pitch]');
  const pitchOutput = document.querySelector('[data-speech-pitch-output]');
  const status = document.querySelector('[data-speech-status]');
  const text = document.querySelector('[data-speech-text]');
  if (!voiceSelect || !text || !('speechSynthesis' in window)) {
    if (status) status.textContent = 'Speech synthesis is unavailable in this browser.';
    return;
  }

  let voices = [];
  const loadVoices = () => {
    voices = speechSynthesis.getVoices();
    voiceSelect.replaceChildren(...voices.map((voice, index) => {
      const option = document.createElement('option');
      option.value = String(index);
      option.textContent = `${voice.name} — ${voice.lang}${voice.localService ? ' (device)' : ''}`;
      return option;
    }));
    status.textContent = voices.length ? `${voices.length} voices available on this device.` : 'Waiting for this browser to provide voices…';
  };

  loadVoices();
  speechSynthesis.addEventListener('voiceschanged', loadVoices);
  rateInput.addEventListener('input', () => { rateOutput.value = `${Number(rateInput.value).toFixed(2)}×`; });
  pitchInput.addEventListener('input', () => { pitchOutput.value = Number(pitchInput.value).toFixed(2); });

  document.querySelector('[data-speech-play]').addEventListener('click', () => {
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.textContent.trim());
    utterance.voice = voices[Number(voiceSelect.value)] || null;
    utterance.rate = Number(rateInput.value);
    utterance.pitch = Number(pitchInput.value);
    utterance.onstart = () => { status.textContent = 'Speaking…'; };
    utterance.onend = () => { status.textContent = 'Finished. Try another voice or speed.'; };
    utterance.onerror = () => { status.textContent = 'This browser could not play the selected voice.'; };
    speechSynthesis.speak(utterance);
  });
  document.querySelector('[data-speech-stop]').addEventListener('click', () => {
    speechSynthesis.cancel();
    status.textContent = 'Stopped.';
  });
})();
