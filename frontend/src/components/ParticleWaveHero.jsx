import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const DEFAULT_IMAGE_URL = '/particle-wave-statue.jpg';

export default function ParticleWaveHero({
  backgroundOpacity = 0.16,
  fit = 'contain',
  imageUrl = DEFAULT_IMAGE_URL,
  interactive = false,
  className = '',
  particleSize = 18,
  waveStrength = 0.22,
  waveSpeed = 1.1,
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    let isDisposed = false;
    let animationFrame = 0;
    let particles = null;
    let backgroundPlane = null;
    let particleMaterial = null;
    const keyboardRotation = { x: 0, y: 0, z: 0 };
    const pointer = { x: 0, y: 0 };

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050510);

    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100);
    camera.position.set(0, 0, 7.5);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.enabled = interactive;
    controls.enablePan = false;
    controls.minDistance = 4.8;
    controls.maxDistance = 10;
    controls.enableZoom = interactive;
    controls.enableRotate = interactive;

    const textureLoader = new THREE.TextureLoader();
    const clock = new THREE.Clock();
    renderer.domElement.tabIndex = interactive ? 0 : -1;

    function resize() {
      const width = container.clientWidth || 1;
      const height = container.clientHeight || 1;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    }

    function animate() {
      if (isDisposed || !particles || !particleMaterial) return;

      const elapsedTime = clock.getElapsedTime();
      particleMaterial.uniforms.uTime.value = elapsedTime;
      particles.rotation.x = keyboardRotation.x + pointer.y * 0.08;
      particles.rotation.y = keyboardRotation.y + pointer.x * 0.12 + Math.sin(elapsedTime * 0.2) * 0.08;
      particles.rotation.z = keyboardRotation.z;
      if (backgroundPlane) {
        backgroundPlane.rotation.copy(particles.rotation);
      }

      controls.update();
      renderer.render(scene, camera);
      animationFrame = window.requestAnimationFrame(animate);
    }

    function handlePointerMove(event) {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / Math.max(rect.width, 1) - 0.5) * 2;
      pointer.y = -(((event.clientY - rect.top) / Math.max(rect.height, 1) - 0.5) * 2);
    }

    function handleKeyDown(event) {
      if (!interactive) return;

      const tagName = event.target?.tagName;
      if (tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT') return;

      const rotationStep = 0.07;
      const zoomStep = 0.45;
      const key = event.key.toLowerCase();

      if (key === 'arrowleft' || key === 'a') keyboardRotation.y -= rotationStep;
      else if (key === 'arrowright' || key === 'd') keyboardRotation.y += rotationStep;
      else if (key === 'arrowup' || key === 'w') keyboardRotation.x -= rotationStep;
      else if (key === 'arrowdown' || key === 's') keyboardRotation.x += rotationStep;
      else if (key === 'q') keyboardRotation.z -= rotationStep;
      else if (key === 'e') keyboardRotation.z += rotationStep;
      else if (key === '+' || key === '=') camera.position.z = Math.max(controls.minDistance, camera.position.z - zoomStep);
      else if (key === '-' || key === '_') camera.position.z = Math.min(controls.maxDistance, camera.position.z + zoomStep);
      else if (key === '0' || key === 'r') {
        keyboardRotation.x = 0;
        keyboardRotation.y = 0;
        keyboardRotation.z = 0;
        camera.position.set(0, 0, 7.5);
      } else {
        return;
      }

      event.preventDefault();
    }

    resize();
    window.addEventListener('resize', resize);
    container.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('keydown', handleKeyDown);

    // Helper function to create shader material
    function createParticleMaterial() {
      return new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0 },
          uSize: { value: particleSize },
          uWaveStrength: { value: waveStrength },
          uWaveSpeed: { value: waveSpeed },
        },
        vertexShader: `
          uniform float uTime;
          uniform float uSize;
          uniform float uWaveStrength;
          uniform float uWaveSpeed;

          attribute vec3 aColor;
          attribute float aRandom;

          varying vec3 vColor;
          varying float vAlpha;

          void main() {
            vec3 pos = position;

            float wave1 = sin(pos.y * 3.0 + uTime * uWaveSpeed + aRandom * 6.28);
            float wave2 = cos(pos.x * 4.0 - uTime * 0.8 + aRandom * 6.28);
            float lightWave = sin(pos.x * 2.2 + pos.y * 1.4 - uTime * 2.2);

            pos.z += wave1 * uWaveStrength;
            pos.x += wave2 * uWaveStrength * 0.18;
            pos.y += sin(uTime * 0.7 + aRandom * 10.0) * 0.035;

            vec4 modelPosition = modelMatrix * vec4(pos, 1.0);
            vec4 viewPosition = viewMatrix * modelPosition;
            gl_Position = projectionMatrix * viewPosition;
            gl_PointSize = uSize * (1.0 / -viewPosition.z);

            vColor = aColor;
            float brightness = dot(aColor, vec3(0.299, 0.587, 0.114));
            float glow = smoothstep(-0.4, 1.0, lightWave);
            vAlpha = 0.25 + brightness * 0.75 + glow * 0.35;
          }
        `,
        fragmentShader: `
          varying vec3 vColor;
          varying float vAlpha;

          void main() {
            vec2 center = gl_PointCoord - vec2(0.5);
            float dist = length(center);

            if (dist > 0.5) {
              discard;
            }

            float strength = 1.0 - smoothstep(0.0, 0.5, dist);
            vec3 dreamColor = vec3(0.75, 0.86, 1.0);
            vec3 finalColor = mix(vColor, dreamColor, 0.12);
            finalColor *= 1.45 + strength * 0.95;

            gl_FragColor = vec4(finalColor, strength * vAlpha);
          }
        `,
      });
    }

    // Helper function to create fallback particles
    function createFallbackParticles() {
      console.warn('[ParticleWaveHero] Creating fallback particles without image');
      const positions = [];
      const colors = [];
      const randoms = [];
      const particleCount = 1500;
      const radius = 3;

      for (let i = 0; i < particleCount; i++) {
        const angle = (i / particleCount) * Math.PI * 2;
        const r = radius * Math.sqrt(i / particleCount);
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;

        positions.push(x, y, (Math.random() - 0.5) * 0.5);
        colors.push(0.5 + Math.random() * 0.3, 0.7 + Math.random() * 0.2, 1.0);
        randoms.push(Math.random());
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aColor', new THREE.Float32BufferAttribute(colors, 3));
      geometry.setAttribute('aRandom', new THREE.Float32BufferAttribute(randoms, 1));

      particleMaterial = createParticleMaterial();
      particles = new THREE.Points(geometry, particleMaterial);
      scene.add(particles);
      animate();
    }

    // Helper function to create particles from image data
    function createParticlesFromImage(imageData, planeWidth, planeHeight) {
      const data = imageData.data;
      const positions = [];
      const colors = [];
      const randoms = [];
      const step = 2;
      const sampleWidth = imageData.width;
      const sampleHeight = imageData.height;

      for (let y = 0; y < sampleHeight; y += step) {
        for (let x = 0; x < sampleWidth; x += step) {
          const index = (y * sampleWidth + x) * 4;
          const red = data[index] / 255;
          const green = data[index + 1] / 255;
          const blue = data[index + 2] / 255;
          const brightness = red * 0.299 + green * 0.587 + blue * 0.114;

          if (brightness < 0.03) continue;

          positions.push((x / sampleWidth - 0.5) * planeWidth);
          positions.push(-(y / sampleHeight - 0.5) * planeHeight);
          positions.push((Math.random() - 0.5) * 0.25);
          colors.push(Math.min(red * 1.18, 1), Math.min(green * 1.14, 1), Math.min(blue * 1.12, 1));
          randoms.push(Math.random());
        }
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aColor', new THREE.Float32BufferAttribute(colors, 3));
      geometry.setAttribute('aRandom', new THREE.Float32BufferAttribute(randoms, 1));

      particleMaterial = createParticleMaterial();
      particles = new THREE.Points(geometry, particleMaterial);
      scene.add(particles);
      animate();
    }

    loadImage(imageUrl)
      .catch((error) => {
        console.warn('[ParticleWaveHero] Failed to load image, trying default:', imageUrl, error);
        return loadImage(DEFAULT_IMAGE_URL);
      })
      .catch((error) => {
        console.error('[ParticleWaveHero] Failed to load default image, using fallback particles:', error);
        return null;
      })
      .then((image) => {
        if (isDisposed) return;

        if (!image) {
          createFallbackParticles();
          return;
        }

        const sourceUrl = image.currentSrc || image.src;
        const imageRatio = image.width / image.height;
        const { width: planeWidth, height: planeHeight } = getPlaneSize(imageRatio, camera, fit);

        const texture = textureLoader.load(sourceUrl);
        const backgroundGeometry = new THREE.PlaneGeometry(planeWidth, planeHeight);
        const backgroundMaterial = new THREE.MeshBasicMaterial({
          map: texture,
          transparent: true,
          opacity: backgroundOpacity,
          depthWrite: false,
        });

        backgroundPlane = new THREE.Mesh(backgroundGeometry, backgroundMaterial);
        backgroundPlane.position.z = -0.25;
        scene.add(backgroundPlane);

        const sampleWidth = 300;
        const sampleHeight = Math.round(sampleWidth / imageRatio);
        const canvas = document.createElement('canvas');
        canvas.width = sampleWidth;
        canvas.height = sampleHeight;

        const context = canvas.getContext('2d');
        if (!context) {
          console.warn('[ParticleWaveHero] Failed to get canvas context, using fallback');
          createFallbackParticles();
          return;
        }

        try {
          context.drawImage(image, 0, 0, sampleWidth, sampleHeight);
          const imageData = context.getImageData(0, 0, sampleWidth, sampleHeight);
          createParticlesFromImage(imageData, planeWidth, planeHeight);
        } catch (error) {
          console.warn('[ParticleWaveHero] Failed to process image data, using fallback:', error);
          createFallbackParticles();
        }
      });

    return () => {
      isDisposed = true;
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener('resize', resize);
      window.removeEventListener('keydown', handleKeyDown);
      container.removeEventListener('pointermove', handlePointerMove);
      controls.dispose();
      scene.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach((material) => material.dispose());
          } else {
            object.material.dispose();
          }
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [backgroundOpacity, fit, imageUrl, interactive, particleSize, waveSpeed, waveStrength]);

  return (
    <div
      aria-hidden={!interactive}
      aria-label={interactive ? 'Interactive particle wave background' : undefined}
      className={`particle-wave-hero ${interactive ? 'is-interactive' : ''} ${className}`}
      ref={containerRef}
      tabIndex={interactive ? 0 : -1}
    />
  );
}

function getPlaneSize(imageRatio, camera, fit) {
  if (fit !== 'cover') {
    const height = 6.6;
    return { width: height * imageRatio, height };
  }

  const distance = camera.position.z + 0.25;
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const visibleHeight = 2 * Math.tan(fov / 2) * distance;
  const visibleWidth = visibleHeight * camera.aspect;
  const viewportRatio = visibleWidth / visibleHeight;
  const padding = 1.12;

  if (imageRatio > viewportRatio) {
    const height = visibleHeight * padding;
    return { width: height * imageRatio, height };
  }

  const width = visibleWidth * padding;
  return { width, height: width / imageRatio };
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
}
