import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

const DEFAULT_IMAGE_URL = '/memory-garden-bg-soft.jpg';

const EFFECT = {
  flowStrength: 0.014,
  pointerStrength: 0.04,
  pointerRadius: 0.035,
  chromaticAberration: 0,
  contrast: 1.08,
  bloom: 0.12,
  timeScale: 0.18,
  particleTimeScale: 0.35,
  particleCount: 96,
};

export default function LiquidMemoryBackground({
  imageUrl = DEFAULT_IMAGE_URL,
  className = '',
  disabled = false,
}) {
  const containerRef = useRef(null);
  const [fallback, setFallback] = useState(disabled);

  useEffect(() => {
    if (disabled || prefersReducedMotion() || !supportsWebGL()) {
      setFallback(true);
      return undefined;
    }

    const container = containerRef.current;
    if (!container) return undefined;

    setFallback(false);

    let animationFrame = 0;
    let disposed = false;
    let texture = null;
    let particleTexture = null;
    let particleGeometry = null;
    let particleMaterial = null;
    let particleField = null;

    const pointer = new THREE.Vector2(0.5, 0.5);
    const smoothPointer = new THREE.Vector2(0.5, 0.5);
    const velocity = new THREE.Vector2(0, 0);
    const targetVelocity = new THREE.Vector2(0, 0);
    const lastPointer = new THREE.Vector2(0.5, 0.5);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const startedAt = window.performance.now();
    const renderer = new THREE.WebGLRenderer({
      antialias: false,
      alpha: true,
      powerPreference: 'high-performance',
    });

    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const uniforms = {
      uTexture: { value: null },
      uTime: { value: 0 },
      uResolution: { value: new THREE.Vector2(1, 1) },
      uImageResolution: { value: new THREE.Vector2(1, 1) },
      uPointer: { value: smoothPointer },
      uPointerVelocity: { value: velocity },
      uFlowStrength: { value: EFFECT.flowStrength },
      uPointerStrength: { value: EFFECT.pointerStrength },
      uPointerRadius: { value: EFFECT.pointerRadius },
      uChromatic: { value: EFFECT.chromaticAberration },
      uContrast: { value: EFFECT.contrast },
      uBloom: { value: EFFECT.bloom },
    };

    const material = new THREE.ShaderMaterial({
      depthWrite: false,
      depthTest: false,
      transparent: true,
      uniforms,
      vertexShader: `
        varying vec2 vUv;

        void main() {
          vUv = uv;
          gl_Position = vec4(position.xy, 0.0, 1.0);
        }
      `,
      fragmentShader: `
        precision highp float;

        uniform sampler2D uTexture;
        uniform float uTime;
        uniform vec2 uResolution;
        uniform vec2 uImageResolution;
        uniform vec2 uPointer;
        uniform vec2 uPointerVelocity;
        uniform float uFlowStrength;
        uniform float uPointerStrength;
        uniform float uPointerRadius;
        uniform float uChromatic;
        uniform float uContrast;
        uniform float uBloom;

        varying vec2 vUv;

        vec2 coverUv(vec2 uv, vec2 screenSize, vec2 imageSize) {
          vec2 screenRatio = screenSize / min(screenSize.x, screenSize.y);
          vec2 imageRatio = imageSize / min(imageSize.x, imageSize.y);
          vec2 scale = screenRatio / imageRatio;
          float fit = max(scale.x, scale.y);
          vec2 coverScale = scale / fit;
          return (uv - 0.5) * coverScale + 0.5;
        }

        float imageBounds(vec2 uv) {
          vec2 bounds = step(vec2(0.0), uv) * step(uv, vec2(1.0));
          return bounds.x * bounds.y;
        }

        float wave(vec2 p, float t) {
          float a = sin(p.x * 12.0 + t * 0.72);
          float b = cos(p.y * 10.0 - t * 0.58);
          float c = sin((p.x + p.y) * 9.0 + t * 0.42);
          float d = cos(length(p - 0.5) * 18.0 - t * 0.62);
          return (a + b + c + d) * 0.25;
        }

        void main() {
          vec2 uv = coverUv(vUv, uResolution, uImageResolution);
          float bounds = imageBounds(uv);
          vec2 centered = vUv - 0.5;
          float t = uTime;

          float lowWave = wave(vUv, t);
          float detailWave = wave(vUv * 1.85 + vec2(0.12, -0.08), t * 1.45);
          vec2 flow = vec2(
            sin(vUv.y * 8.0 + t * 0.42) + lowWave,
            cos(vUv.x * 7.5 - t * 0.38) + detailWave
          ) * uFlowStrength;

          vec2 toPointer = vUv - uPointer;
          float pointerDist = length(toPointer);
          float ripple = sin(pointerDist * 78.0 - t * 8.0);
          float falloff = 1.0 - smoothstep(0.0, uPointerRadius, pointerDist);
          vec2 radial = normalize(toPointer + 0.0001) * ripple * falloff;
          vec2 drag = -uPointerVelocity * falloff * 0.35;
          vec2 displacement = flow + radial * uPointerStrength + drag;

          float vignette = smoothstep(0.76, 0.2, length(centered));
          float ca = uChromatic + falloff * uChromatic * 1.2;
          vec2 chromaDir = normalize(displacement + centered * 0.18 + 0.0001);

          vec3 color;
          color.r = texture2D(uTexture, uv + displacement + chromaDir * ca).r;
          color.g = texture2D(uTexture, uv + displacement * 0.82).g;
          color.b = texture2D(uTexture, uv + displacement - chromaDir * ca).b;

          vec3 blurA = texture2D(uTexture, uv + displacement * 0.62 + vec2(0.0018, 0.0012)).rgb;
          vec3 blurB = texture2D(uTexture, uv + displacement * 0.62 - vec2(0.0018, 0.0012)).rgb;
          color = mix(color, (blurA + blurB) * 0.5, 0.18);

          color = (color - 0.5) * uContrast + 0.5;
          float glow = smoothstep(0.22, 1.0, dot(color, vec3(0.299, 0.587, 0.114)));
          color += color * glow * uBloom;
          color += vec3(0.06, 0.08, 0.12) * falloff * 0.2;
          color *= mix(0.78, 1.0, vignette);

          gl_FragColor = vec4(color, bounds);
        }
      `,
    });

    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
    scene.add(mesh);

    function resize() {
      const width = Math.max(1, container.clientWidth);
      const height = Math.max(1, container.clientHeight);
      const pixelRatio = Math.min(window.devicePixelRatio || 1, width < 900 ? 1.25 : 1.75);
      renderer.setPixelRatio(pixelRatio);
      renderer.setSize(width, height, false);
      uniforms.uResolution.value.set(width, height);
    }

    function handlePointerMove(event) {
      const x = event.clientX / Math.max(1, window.innerWidth);
      const y = 1 - event.clientY / Math.max(1, window.innerHeight);
      pointer.set(x, y);
      targetVelocity.set(x - lastPointer.x, y - lastPointer.y);
      lastPointer.set(x, y);
    }

    function buildParticles() {
      const geometry = new THREE.BufferGeometry();
      const positions = [];
      const sizes = [];
      const phases = [];

      for (let index = 0; index < EFFECT.particleCount; index += 1) {
        positions.push(Math.random() * 2 - 1, Math.random() * 2 - 1, 0);
        sizes.push(16 + Math.random() * 36);
        phases.push(Math.random() * Math.PI * 2);
      }

      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aSize', new THREE.Float32BufferAttribute(sizes, 1));
      geometry.setAttribute('aPhase', new THREE.Float32BufferAttribute(phases, 1));

      const canvas = document.createElement('canvas');
      canvas.width = 64;
      canvas.height = 64;
      const context = canvas.getContext('2d');
      const gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32);
      gradient.addColorStop(0, 'rgba(255,255,255,1)');
      gradient.addColorStop(0.28, 'rgba(210,235,255,0.72)');
      gradient.addColorStop(1, 'rgba(160,205,255,0)');
      context.fillStyle = gradient;
      context.fillRect(0, 0, 64, 64);

      particleTexture = new THREE.CanvasTexture(canvas);
      const materialPoints = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0 },
          uPointer: { value: smoothPointer },
          uTexture: { value: particleTexture },
        },
        vertexShader: `
          uniform float uTime;
          uniform vec2 uPointer;

          attribute float aSize;
          attribute float aPhase;

          varying float vAlpha;

          void main() {
            vec3 pos = position;
            pos.x += sin(uTime * 0.12 + aPhase) * 0.035;
            pos.y += cos(uTime * 0.16 + aPhase) * 0.045;

            vec2 pointerClip = vec2(uPointer.x * 2.0 - 1.0, uPointer.y * 2.0 - 1.0);
            float d = distance(pos.xy, pointerClip);
            float lift = 1.0 - smoothstep(0.0, 0.12, d);
            pos.xy += normalize(pos.xy - pointerClip + 0.0001) * lift * 0.02;

            gl_Position = vec4(pos, 1.0);
            gl_PointSize = aSize * (1.0 + lift * 0.35);
            vAlpha = 0.24 + lift * 0.24 + sin(uTime * 0.5 + aPhase) * 0.08;
          }
        `,
        fragmentShader: `
          uniform sampler2D uTexture;
          varying float vAlpha;

          void main() {
            vec4 tex = texture2D(uTexture, gl_PointCoord);
            gl_FragColor = vec4(tex.rgb, tex.a * vAlpha);
          }
        `,
      });

      particleGeometry = geometry;
      particleMaterial = materialPoints;
      particleField = new THREE.Points(geometry, materialPoints);
      scene.add(particleField);
    }

    function animate() {
      if (disposed) return;

      const elapsed = (window.performance.now() - startedAt) / 1000;
      smoothPointer.lerp(pointer, 0.12);
      velocity.lerp(targetVelocity, 0.16);
      targetVelocity.multiplyScalar(0.9);

      uniforms.uTime.value = elapsed * EFFECT.timeScale;
      if (particleMaterial) {
        particleMaterial.uniforms.uTime.value = elapsed * EFFECT.particleTimeScale;
      }

      renderer.render(scene, camera);
      animationFrame = window.requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('pointermove', handlePointerMove, { passive: true });

    const loader = new THREE.TextureLoader();
    loader.load(
      imageUrl,
      (loadedTexture) => {
        if (disposed) {
          loadedTexture.dispose();
          return;
        }

        texture = loadedTexture;
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.minFilter = THREE.LinearFilter;
        texture.magFilter = THREE.LinearFilter;
        texture.wrapS = THREE.ClampToEdgeWrapping;
        texture.wrapT = THREE.ClampToEdgeWrapping;
        uniforms.uTexture.value = texture;
        uniforms.uImageResolution.value.set(texture.image.width || 1, texture.image.height || 1);

        buildParticles();
        animate();
      },
      undefined,
      () => {
        if (!disposed) setFallback(true);
      },
    );

    return () => {
      disposed = true;
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', handlePointerMove);
      scene.remove(mesh);
      if (particleField) scene.remove(particleField);
      mesh.geometry.dispose();
      material.dispose();
      if (texture) texture.dispose();
      if (particleTexture) particleTexture.dispose();
      if (particleGeometry) particleGeometry.dispose();
      if (particleMaterial) particleMaterial.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [disabled, imageUrl]);

  return (
    <div
      aria-hidden="true"
      className={`liquid-memory-background ${fallback ? 'liquid-memory-background-static' : ''} ${className}`}
      ref={containerRef}
      style={{ '--memory-bg-image': `url("${imageUrl}")` }}
    />
  );
}

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
  } catch {
    return false;
  }
}
