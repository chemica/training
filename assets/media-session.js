(() => {
  if (!("mediaSession" in navigator)) return;
  document.querySelectorAll("audio[data-title]").forEach((audio) => {
    audio.addEventListener("play", () => {
      document.querySelectorAll("audio").forEach((other) => {
        if (other !== audio) other.pause();
      });
      navigator.mediaSession.metadata = new MediaMetadata({
        title: audio.dataset.title,
        artist: "Piper Alba",
        album: audio.dataset.course,
      });
      const seek = (seconds) => {
        audio.currentTime = Math.max(0, Math.min(audio.duration || Infinity, audio.currentTime + seconds));
      };
      navigator.mediaSession.setActionHandler("play", () => audio.play());
      navigator.mediaSession.setActionHandler("pause", () => audio.pause());
      navigator.mediaSession.setActionHandler("seekbackward", (event) => seek(-(event.seekOffset || 15)));
      navigator.mediaSession.setActionHandler("seekforward", (event) => seek(event.seekOffset || 30));
      navigator.mediaSession.setActionHandler("seekto", (event) => {
        if (event.seekTime != null) audio.currentTime = event.seekTime;
      });
    });
  });
})();
