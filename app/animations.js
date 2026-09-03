// Runtime animation manifest loader.
//
// Each state directory may contain an `animation.json` manifest published by
// the Sprite Harness consumer pipeline (tools/build_reimu_animations.py).
// This module fetches and strictly checks those manifests, preloads their
// frames, and upgrades each state's ordered `frames` list in place.
//
// A missing, malformed, or partially broken manifest never crashes the app
// and is never silently absorbed: the state keeps its static base.png
// fallback and records an explicit `animation.status` that the UI shows and
// the console logs.

const MANIFEST_VERSION = 1;

// A manifest frame path must stay inside the state directory.
function safeRelativePath(file) {
  return (
    typeof file === 'string' &&
    file.length > 0 &&
    !file.startsWith('/') &&
    !file.includes('\\') &&
    !file.split('/').includes('..') &&
    !file.includes(':')
  );
}

function parseManifest(manifest) {
  if (manifest === null || typeof manifest !== 'object') throw new Error('manifest is not an object');
  if (manifest.manifest_version !== MANIFEST_VERSION) {
    throw new Error(`unsupported manifest_version: ${manifest.manifest_version}`);
  }
  if (!Array.isArray(manifest.frames) || manifest.frames.length === 0) {
    throw new Error('manifest declares no frames');
  }
  const frames = manifest.frames.map((frame, i) => {
    if (frame === null || typeof frame !== 'object') throw new Error(`frame ${i} is not an object`);
    if (!safeRelativePath(frame.file)) throw new Error(`frame ${i} has an invalid file path`);
    if (!Number.isFinite(frame.duration_ms) || frame.duration_ms <= 0) {
      throw new Error(`frame ${i} has an invalid duration_ms`);
    }
    return { file: frame.file, durationMs: frame.duration_ms };
  });
  const loop = manifest.playback?.loop;
  if (typeof loop !== 'boolean') throw new Error('playback.loop must be a boolean');
  const reducedFrame = manifest.reduced_motion?.frame;
  if (!safeRelativePath(reducedFrame)) throw new Error('reduced_motion.frame is missing or invalid');
  if (!frames.some((f) => f.file === reducedFrame)) {
    throw new Error('reduced_motion.frame is not one of the declared frames');
  }
  return { frames, loop, reducedFrame };
}

function preloadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(src);
    img.onerror = () => reject(new Error(`frame image failed to load: ${src}`));
    img.src = src;
  });
}

async function loadOne(stateId, state) {
  try {
    const response = await fetch(state.manifest);
    if (!response.ok) throw new Error(`manifest fetch failed: HTTP ${response.status}`);
    const parsed = parseManifest(await response.json());
    const frameUrls = parsed.frames.map((f) => `${state.assetDir}/${f.file}`);
    await Promise.all(frameUrls.map(preloadImage));

    state.frames = frameUrls;
    state.durationsMs = parsed.frames.map((f) => f.durationMs);
    state.loop = parsed.loop;
    state.reducedMotionFrame = `${state.assetDir}/${parsed.reducedFrame}`;
    state.animation = {
      status: 'animated',
      detail: `${frameUrls.length} validated frame(s)${parsed.loop ? ', loop' : ''}`,
    };
  } catch (error) {
    state.animation = { status: 'static-fallback', detail: error.message };
    console.warn(`[animations] state "${stateId}": using static base.png — ${error.message}`);
  }
}

// Upgrade every state of a state set from its published runtime manifest.
// Resolves when all states are either animated or explicitly fallen back.
export function loadStateAnimations(stateSet) {
  return Promise.all(
    Object.entries(stateSet.states).map(([stateId, state]) => loadOne(stateId, state)),
  );
}
