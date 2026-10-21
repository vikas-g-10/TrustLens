export const VIDEO_ACCEPT = 'video/mp4,video/quicktime,video/webm,video/x-msvideo,.mp4,.mov,.webm,.avi';
export const MAX_VIDEO_BYTES = 30 * 1024 * 1024;

export type VideoFrame = { blob: Blob; timestamp: number };
export type VideoValidation = { duration: number; width: number; height: number; frames: VideoFrame[]; thumbnailUrl: string };

const VIDEO_EXTENSIONS = /\.(mp4|mov|webm|avi)$/i;

export function isSupportedVideo(file: File) {
  return file.type.startsWith('video/') || VIDEO_EXTENSIONS.test(file.name);
}

function waitForEvent(video: HTMLVideoElement, name: string) {
  return new Promise<void>((resolve, reject) => {
    const onDone = () => { cleanup(); resolve(); };
    const onError = () => { cleanup(); reject(new Error("This video format can't be read in your browser. Try an MP4 (H.264) file.")); };
    const cleanup = () => { video.removeEventListener(name, onDone); video.removeEventListener('error', onError); };
    video.addEventListener(name, onDone, { once: true });
    video.addEventListener('error', onError, { once: true });
  });
}

async function seek(video: HTMLVideoElement, time: number) {
  if (Math.abs(video.currentTime - time) < 0.01) return;
  const pending = waitForEvent(video, 'seeked');
  video.currentTime = time;
  await pending;
}

export async function validateAndExtractVideo(file: File): Promise<VideoValidation> {
  if (!isSupportedVideo(file)) throw new Error('Choose an MP4, MOV, WebM, or AVI video file.');
  if (file.size > MAX_VIDEO_BYTES) throw new Error('This video is too large. The maximum supported video size is 30 MB.');

  const objectUrl = URL.createObjectURL(file);
  const video = document.createElement('video');
  video.muted = true;
  video.playsInline = true;
  video.preload = 'metadata';
  video.setAttribute('aria-hidden', 'true');
  video.style.position = 'fixed';
  video.style.width = '1px';
  video.style.height = '1px';
  video.style.opacity = '0';
  video.style.pointerEvents = 'none';
  document.body.appendChild(video);

  try {
    video.src = objectUrl;
    await waitForEvent(video, 'loadedmetadata');
    if (!Number.isFinite(video.duration) || video.duration <= 0 || video.videoWidth <= 0 || video.videoHeight <= 0) {
      throw new Error("This video format can't be read in your browser. Try an MP4 (H.264) file.");
    }
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 1280 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    const timestamps = [0, Math.max(0, video.duration / 2), Math.max(0, video.duration - Math.min(0.05, video.duration / 10))];
    const frames: VideoFrame[] = [];
    for (const timestamp of timestamps) {
      await seek(video, timestamp);
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Your browser could not prepare a video preview. Try an MP4 (H.264) file.');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85));
      if (!blob) throw new Error('Your browser could not create a video preview. Try an MP4 (H.264) file.');
      frames.push({ blob, timestamp });
    }
    return { duration: video.duration, width: video.videoWidth, height: video.videoHeight, frames, thumbnailUrl: URL.createObjectURL(frames[1].blob) };
  } finally {
    video.pause();
    video.removeAttribute('src');
    video.load();
    video.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
  }
}
