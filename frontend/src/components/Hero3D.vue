<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'

interface CardSpec {
  label: string
  glyph: string
}

interface HeroCapability {
  reducedMotion: boolean
  webgl: boolean
  lowEnd: boolean
  finePointer: boolean
}

interface CardState {
  basePosition: { x: number; y: number; z: number }
  baseRotation: { x: number; y: number; z: number }
  bobPhase: number
}

const CARD_SPECS: CardSpec[] = [
  { label: '租屋補貼', glyph: '🏠' },
  { label: '育兒津貼', glyph: '👶' },
  { label: '長照給付', glyph: '🩺' },
  { label: '身心障礙生活補助', glyph: '♿' },
  { label: '老人生活津貼', glyph: '👴' },
  { label: '助學金', glyph: '🎓' },
]

const MOBILE_BREAKPOINT = 640
const FOCUS_INDEX = 2
const PARALLAX_LIMIT = 0.05

const mode = ref<'static' | 'animated'>('static')
const rootEl = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)

let disposeScene: (() => void) | null = null

function detectHeroCapability(): HeroCapability {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches
  let webgl = false
  try {
    const probe = document.createElement('canvas')
    webgl = !!(probe.getContext('webgl2') || probe.getContext('webgl'))
  } catch {
    webgl = false
  }
  const nav = navigator as Navigator & { deviceMemory?: number }
  const lowEnd = (nav.deviceMemory ?? 8) <= 2 || navigator.hardwareConcurrency <= 2
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches

  // Dev-only override for QA of the fallback paths (dead-code-eliminated in production builds).
  if (import.meta.env.DEV) {
    const forced = new URLSearchParams(location.search).get('heroMode')
    if (forced === 'static') return { reducedMotion: false, webgl: false, lowEnd: false, finePointer }
    if (forced === 'reduced-motion') return { reducedMotion: true, webgl, lowEnd, finePointer }
  }

  return { reducedMotion, webgl, lowEnd, finePointer }
}

function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function drawCardTexture(spec: CardSpec, colors: { bg: string; fg: string }): HTMLCanvasElement {
  const width = 320
  const height = 400
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) return canvas

  roundRectPath(ctx, 8, 8, width - 16, height - 16, 32)
  ctx.fillStyle = colors.bg
  ctx.fill()
  ctx.lineWidth = 2
  ctx.strokeStyle = 'rgba(255,255,255,0.4)'
  ctx.stroke()

  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = colors.fg
  ctx.font = '120px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif'
  ctx.fillText(spec.glyph, width / 2, height / 2 - 30)

  ctx.font = '600 30px system-ui, sans-serif'
  ctx.fillText(spec.label, width / 2, height / 2 + 96)

  return canvas
}

function drawGlowTexture(color: string): HTMLCanvasElement {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (ctx) {
    const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    gradient.addColorStop(0, color)
    gradient.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, size, size)
  }
  return canvas
}

async function initHero(capability: HeroCapability): Promise<() => void> {
  await nextTick()
  const root = rootEl.value
  const canvas = canvasEl.value
  if (!root || !canvas) return () => {}

  const [THREE, { gsap }, { ScrollTrigger }] = await Promise.all([
    import('three'),
    import('gsap'),
    import('gsap/ScrollTrigger'),
  ])
  gsap.registerPlugin(ScrollTrigger)

  const styles = getComputedStyle(document.documentElement)
  const readVar = (name: string, fallback: string) => styles.getPropertyValue(name).trim() || fallback
  let cardBg = readVar('--hero-card-bg', 'rgba(255,255,255,0.6)')
  let cardFg = readVar('--hero-card-fg', '#08060d')
  const glowColor = readVar('--hero-glow', '#c084fc')

  const isMobile = root.clientWidth < MOBILE_BREAKPOINT
  const specs = isMobile ? CARD_SPECS.slice(0, 4) : CARD_SPECS
  const focusIndex = Math.min(FOCUS_INDEX, specs.length - 1)

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(root.clientWidth, root.clientHeight, false)

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(35, root.clientWidth / Math.max(root.clientHeight, 1), 0.1, 100)
  camera.position.z = 8

  const ambient = new THREE.AmbientLight(0xffffff, 0.9)
  const directional = new THREE.DirectionalLight(0xffffff, 0.6)
  directional.position.set(2, 3, 4)
  scene.add(ambient, directional)

  const cardGroup = new THREE.Group()
  // Desktop: sit the stack in the right-hand portion of the hero so it never covers
  // the left-aligned headline/CTA. Mobile: no side room, so drop the (scaled-down)
  // stack low behind the text instead of beside it.
  if (isMobile) {
    cardGroup.position.set(0, 1.5, -1.2)
    cardGroup.scale.setScalar(0.6)
  } else {
    cardGroup.position.set(2.4, -0.15, 0)
  }
  scene.add(cardGroup)

  const cardStates: CardState[] = []
  const cards = specs.map((spec, i) => {
    const texture = new THREE.CanvasTexture(drawCardTexture(spec, { bg: cardBg, fg: cardFg }))
    texture.colorSpace = THREE.SRGBColorSpace
    const geometry = new THREE.PlaneGeometry(1.8, 2.25)
    const material = new THREE.MeshStandardMaterial({ map: texture, transparent: true, roughness: 0.5, metalness: 0.05 })
    const mesh = new THREE.Mesh(geometry, material)
    const state: CardState = {
      basePosition: { x: i * 0.1, y: -i * 0.06, z: -i * 0.05 },
      baseRotation: { x: 0, y: 0, z: (i - (specs.length - 1) / 2) * 0.03 },
      bobPhase: i * 0.7,
    }
    mesh.position.set(state.basePosition.x, state.basePosition.y, state.basePosition.z)
    mesh.rotation.set(state.baseRotation.x, state.baseRotation.y, state.baseRotation.z)
    cardGroup.add(mesh)
    cardStates.push(state)
    return mesh
  })

  const glowTexture = new THREE.CanvasTexture(drawGlowTexture(glowColor))
  const glowMaterial = new THREE.SpriteMaterial({
    map: glowTexture,
    transparent: true,
    opacity: 0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })
  const glowSprite = new THREE.Sprite(glowMaterial)
  glowSprite.scale.set(4, 4, 1)
  glowSprite.position.z = -0.5
  cardGroup.add(glowSprite)

  const clock = new THREE.Clock()
  let parallaxTargetX = 0
  let parallaxTargetY = 0
  const canParallax = capability.finePointer && !capability.reducedMotion

  function onPointerMove(event: PointerEvent) {
    const rect = root!.getBoundingClientRect()
    const nx = (event.clientX - rect.left) / rect.width - 0.5
    const ny = (event.clientY - rect.top) / rect.height - 0.5
    parallaxTargetX = -ny * PARALLAX_LIMIT
    parallaxTargetY = nx * PARALLAX_LIMIT
  }
  if (canParallax) root.addEventListener('pointermove', onPointerMove)

  function tick() {
    const elapsed = clock.getElapsedTime()
    cards.forEach((card, i) => {
      const state = cardStates[i]
      const bob = Math.sin(elapsed * 1.1 + state.bobPhase) * 0.02
      card.position.set(state.basePosition.x, state.basePosition.y + bob, state.basePosition.z)
      card.rotation.set(state.baseRotation.x, state.baseRotation.y, state.baseRotation.z + bob * 0.05)
    })
    if (canParallax) {
      cardGroup.rotation.x += (parallaxTargetX - cardGroup.rotation.x) * 0.05
      cardGroup.rotation.y += (parallaxTargetY - cardGroup.rotation.y) * 0.05
    }
    renderer.render(scene, camera)
  }
  renderer.setAnimationLoop(tick)

  const heroSection = root.closest<HTMLElement>('.landing-hero') ?? root
  const heroContent = heroSection.querySelector<HTMLElement>('.landing-hero-content')

  const timeline = gsap.timeline({
    scrollTrigger: {
      trigger: heroSection,
      start: 'top top',
      end: () => `+=${window.innerHeight * 3}`,
      scrub: 1,
      pin: true,
      invalidateOnRefresh: true,
    },
  })

  // Scene 1 (15–45%): fan the stack out into a shallow arc.
  cardStates.forEach((state, i) => {
    const angle = (i - (specs.length - 1) / 2) * 0.5
    timeline.to(state.basePosition, { x: Math.sin(angle) * 2.4, y: Math.cos(angle) * 0.3, z: -Math.abs(i - focusIndex) * 0.7, duration: 0.3 }, 0.15)
    timeline.to(state.baseRotation, { y: angle * 0.4, duration: 0.3 }, 0.15)
  })

  // Scene 2 (45–75%): focus card comes forward, the rest dim/shrink, glow + light intensify.
  cards.forEach((card, i) => {
    const state = cardStates[i]
    if (i === focusIndex) {
      timeline.to(state.basePosition, { x: 0, y: 0, z: 2.6, duration: 0.3 }, 0.45)
      timeline.to(state.baseRotation, { y: 0, duration: 0.3 }, 0.45)
    } else {
      timeline.to(card.material, { opacity: 0.15, duration: 0.3 }, 0.45)
      timeline.to(card.scale, { x: 0.85, y: 0.85, z: 0.85, duration: 0.3 }, 0.45)
    }
  })
  timeline.to(glowMaterial, { opacity: 0.6, duration: 0.3 }, 0.45)
  timeline.to(directional, { intensity: 1.4, duration: 0.3 }, 0.45)

  // Scene 3 (75–100%): collapse and fade into the sections below.
  cardStates.forEach((state) => {
    timeline.to(state.basePosition, { z: '+=1.5', duration: 0.25 }, 0.75)
  })
  timeline.to(cardGroup.scale, { x: 0.7, y: 0.7, z: 0.7, duration: 0.25 }, 0.75)
  timeline.to(root, { opacity: 0, duration: 0.15 }, 0.9)
  if (heroContent) {
    timeline.to(heroContent, { opacity: 0, y: -20, duration: 0.2 }, 0.8)
  }

  // Only the renderer/camera react to the observer (fires on any layout change,
  // including GSAP's own pin-spacer insertion) — calling ScrollTrigger.refresh()
  // from here would re-measure the trigger while it's mid-pin (already `position:
  // fixed`) and corrupt the computed pin-spacer height. A real viewport resize is
  // handled separately, debounced, via `window`'s `resize` event instead.
  function updateRendererSize() {
    const w = root!.clientWidth
    const h = Math.max(root!.clientHeight, 1)
    renderer.setSize(w, h, false)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
  }
  const resizeObserver = new ResizeObserver(updateRendererSize)
  resizeObserver.observe(root)

  let resizeRefreshTimer = 0
  function handleWindowResize() {
    window.clearTimeout(resizeRefreshTimer)
    resizeRefreshTimer = window.setTimeout(() => ScrollTrigger.refresh(), 200)
  }
  window.addEventListener('resize', handleWindowResize)

  const darkModeQuery = matchMedia('(prefers-color-scheme: dark)')
  function handleSchemeChange() {
    const liveStyles = getComputedStyle(document.documentElement)
    cardBg = liveStyles.getPropertyValue('--hero-card-bg').trim() || cardBg
    cardFg = liveStyles.getPropertyValue('--hero-card-fg').trim() || cardFg
    cards.forEach((card, i) => {
      const nextTexture = new THREE.CanvasTexture(drawCardTexture(specs[i], { bg: cardBg, fg: cardFg }))
      nextTexture.colorSpace = THREE.SRGBColorSpace
      card.material.map?.dispose()
      card.material.map = nextTexture
      card.material.needsUpdate = true
    })
  }
  darkModeQuery.addEventListener('change', handleSchemeChange)

  return () => {
    renderer.setAnimationLoop(null)
    timeline.scrollTrigger?.kill()
    timeline.kill()
    resizeObserver.disconnect()
    window.clearTimeout(resizeRefreshTimer)
    window.removeEventListener('resize', handleWindowResize)
    darkModeQuery.removeEventListener('change', handleSchemeChange)
    if (canParallax) root.removeEventListener('pointermove', onPointerMove)
    cards.forEach((card) => {
      card.geometry.dispose()
      card.material.map?.dispose()
      card.material.dispose()
    })
    glowTexture.dispose()
    glowMaterial.dispose()
    renderer.dispose()
  }
}

onMounted(() => {
  const capability = detectHeroCapability()
  if (!capability.webgl || capability.reducedMotion || capability.lowEnd) return
  mode.value = 'animated'
  initHero(capability)
    .then((disposer) => {
      disposeScene = disposer
    })
    .catch(() => {
      mode.value = 'static'
    })
})

onUnmounted(() => {
  disposeScene?.()
  disposeScene = null
})
</script>

<template>
  <div ref="rootEl" class="hero3d-layer" aria-hidden="true">
    <canvas v-if="mode === 'animated'" ref="canvasEl" class="hero3d-canvas"></canvas>
  </div>
</template>

<style scoped>
.hero3d-layer {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background: var(--hero-gradient);
}
.hero3d-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
