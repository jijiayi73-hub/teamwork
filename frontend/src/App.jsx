import React from 'react';

export default function App() {
  const memoryCount = getMemoryCount();
  const gardenStatus =
    memoryCount > 0
      ? `Your garden has ${memoryCount} ${memoryCount === 1 ? 'memory' : 'memories'} blooming.`
      : '你的花园还很安静，从一次倾诉开始。';

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#10131e] font-body text-white">
      <div className="absolute inset-0 bg-night-garden" />
      <div className="absolute inset-0 bg-watercolor-mist" />
      <div className="particles" aria-hidden="true">
        {Array.from({ length: 34 }, (_, index) => (
          <span key={index} style={particleStyle(index)} />
        ))}
      </div>

      <nav className="relative z-10 flex items-center justify-between px-8 py-6 text-sm text-white/72 lg:px-14">
        <a className="font-display text-lg tracking-wide text-white" href="#/">
          Mindful Memory Diary
        </a>
        <div className="flex items-center gap-6 rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 shadow-glow backdrop-blur-xl">
          <a className="transition hover:text-white" href="#/">
            Home
          </a>
          <a className="transition hover:text-white" href="#/memory-garden">
            Memory Garden
          </a>
          <a className="transition hover:text-white" href="#/about">
            About
          </a>
        </div>
      </nav>

      <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-20 pt-6">
        <div className="w-full max-w-4xl rounded-[28px] border border-white/16 bg-white/[0.08] px-6 py-12 text-center shadow-glow backdrop-blur-2xl sm:px-10 lg:px-16">
          <p className="mb-4 text-sm uppercase tracking-[0.38em] text-[#c8e0ff]/80">
            Inner Garden
          </p>
          <h1 className="font-display text-5xl leading-tight text-white sm:text-6xl lg:text-7xl">
            Mindful Memory Diary
          </h1>
          <p className="mt-5 text-lg text-[#e6eefc]/90 sm:text-xl">
            把今天的情绪，种成一座记忆花园
          </p>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-white/68 sm:text-lg">
            Talk gently with AI, let your feelings settle into words, and keep each day as a quiet
            bloom in your memory garden.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              className="w-full rounded-full bg-[#e8f1ff] px-8 py-4 text-center text-sm font-semibold text-[#182036] shadow-button transition hover:-translate-y-0.5 hover:bg-white sm:w-auto"
              href="#/ai-companion-chat"
            >
              开始记录今天
            </a>
            <a
              className="w-full rounded-full border border-white/18 bg-white/[0.08] px-8 py-4 text-center text-sm font-semibold text-white shadow-glow backdrop-blur-xl transition hover:-translate-y-0.5 hover:bg-white/[0.14] sm:w-auto"
              href="#/memory-garden"
            >
              进入 Memory Garden
            </a>
          </div>
        </div>
      </section>

      <p className="absolute bottom-6 left-1/2 z-10 w-full -translate-x-1/2 px-5 text-center text-sm text-white/56">
        {gardenStatus}
      </p>
    </main>
  );
}

function getMemoryCount() {
  if (typeof window === 'undefined') {
    return 0;
  }

  const possibleKeys = [
    'mindful_memory_diary_memories',
    'mindful-memory-diary:memories',
    'memory_garden_memories',
    'memoryGarden',
    'memories',
  ];

  for (const key of possibleKeys) {
    const value = window.localStorage.getItem(key);
    if (!value) continue;

    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.length;
      }
    } catch {
      continue;
    }
  }

  return 0;
}

function particleStyle(index) {
  const left = (index * 29) % 100;
  const top = (index * 47) % 100;
  const size = 2 + (index % 4);
  const delay = (index % 9) * 0.7;
  const duration = 11 + (index % 7);

  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  };
}

