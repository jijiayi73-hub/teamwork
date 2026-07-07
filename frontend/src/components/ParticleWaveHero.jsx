import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const DEFAULT_IMAGE_URL = '/particle-wave-statue.jpg';

export default function ParticleWaveHero({
  imageUrl = DEFAULT_IMAGE_URL,
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
    controls.enablePan = false;
    controls.minDistance = 4.8;
    controls.maxDistance = 10;

    const textureLoader = new THREE.TextureLoader();
    const clock = new THREE.Clock();

    function resize() {
      const width = container.clientWidth || 1;
      const height = container.clientHeight || 1;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    }

    function animate() {
      if (isDisposed || !particles || !backgroundPlane || !particleMaterial) return;

      const elapsedTime = clock.getElapsedTime();
      particleMaterial.uniforms.uTime.value = elapsedTime;
      particles.rotation.y = Math.sin(elapsedTime * 0.2) * 0.08;
      backgroundPlane.rotation.y = particles.rotation.y;

      controls.update();
      renderer.render(scene, camera);
      animationFrame = window.requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', resize);

    loadImage(imageUrl).then((image) => {
      if (isDisposed) return;

      const imageRatio = image.width / image.height;
      const planeHeight = 6.6;
      const planeWidth = planeHeight * imageRatio;

      const texture = textureLoader.load(imageUrl);
      const backgroundGeometry = new THREE.PlaneGeometry(planeWidth, planeHeight);
      const backgroundMaterial = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        opacity: 0.16,
        depthWrite: false,
      });

      backgroundPlane = new THREE.Mesh(backgroundGeometry, backgroundMaterial);
      backgroundPlane.position.z = -0.25;
      scene.add(backgroundPlane);

      const sampleWidth = 260;
      const sampleHeight = Math.round(sampleWidth / imageRatio);
      const canvas = document.createElement('canvas');
      canvas.width = sampleWidth;
      canvas.height = sampleHeight;

      const context = canvas.getContext('2d');
      if (!context) return;

      context.drawImage(image, 0, 0, sampleWidth, sampleHeight);
      const imageData = context.getImageData(0, 0, sampleWidth, sampleHeight);
      const data = imageData.data;
      const positions = [];
      const colors = [];
      const randoms = [];
      const step = 2;

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
          colors.push(red, green, blue);
          randoms.push(Math.random());
        }
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aColor', new THREE.Float32BufferAttribute(colors, 3));
      geometry.setAttribute('aRandom', new THREE.Float32BufferAttribute(randoms, 1));

      particleMaterial = new THREE.ShaderMaterial({
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
            vec3 dreamColor = vec3(0.35, 0.45, 1.0);
            vec3 finalColor = mix(vColor, dreamColor, 0.22);
            finalColor *= 1.25 + strength * 0.8;

            gl_FragColor = vec4(finalColor, strength * vAlpha);
          }
        `,
      });

      particles = new THREE.Points(geometry, particleMaterial);
      scene.add(particles);
      animate();
    });

    return () => {
      isDisposed = true;
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener('resize', resize);
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
  }, [imageUrl, particleSize, waveSpeed, waveStrength]);

  return <div aria-hidden="true" className={`particle-wave-hero ${className}`} ref={containerRef} />;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
}
