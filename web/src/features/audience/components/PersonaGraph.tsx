import { useMemo, useState, type CSSProperties } from 'react'

import { cn } from '@/lib/utils'

export type SimPersona = {
  id: string
  name: string
  age: number
  city: string
  cohort: string
  listenHabit: string
  dropTriggers: string[]
  x: number
  y: number
  wobbleDelay: number
  size: number
}

type PersonaSeed = Omit<SimPersona, 'x' | 'y' | 'wobbleDelay' | 'size'>

/** Seeded PRNG so layout stays stable across renders */
function mulberry32(seed: number) {
  let t = seed >>> 0
  return () => {
    t += 0x6d2b79f5
    let r = Math.imul(t ^ (t >>> 15), 1 | t)
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r)
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296
  }
}

const PERSONA_SEEDS: PersonaSeed[] = [
  { id: 'p1', name: 'Ananya', age: 24, city: 'Bengaluru', cohort: 'Commute binge', listenHabit: '45–60 min metro rides, one earbud', dropTriggers: ['Slow cold open', 'Unclear stakes'] },
  { id: 'p2', name: 'Rohan', age: 31, city: 'Mumbai', cohort: 'Night thriller', listenHabit: 'Late nights, full episodes back-to-back', dropTriggers: ['Weak cliff', 'Predictable twist'] },
  { id: 'p3', name: 'Meera', age: 28, city: 'Delhi NCR', cohort: 'Romance + tension', listenHabit: 'Household chores, background listen', dropTriggers: ['Dialogue-heavy stretches', 'Low emotion'] },
  { id: 'p4', name: 'Kabir', age: 22, city: 'Hyderabad', cohort: 'Short-form hop', listenHabit: 'Skips aggressively, high dopamine', dropTriggers: ['No hook in 30s', 'Flat SFX'] },
  { id: 'p5', name: 'Isha', age: 26, city: 'Ahmedabad', cohort: 'Hinglish loyalist', listenHabit: 'Prefers Hindi vernacular, dinner-time listen', dropTriggers: ['Stiff Hindi', 'Over-English lines'] },
  { id: 'p6', name: 'Dev', age: 29, city: 'Noida', cohort: 'Office rewind', listenHabit: 'Replays twists on lunch break', dropTriggers: ['Confusing timeline', 'Too many cast'] },
  { id: 'p7', name: 'Sana', age: 19, city: 'Kolkata', cohort: 'Campus share', listenHabit: 'Shares clips with friends', dropTriggers: ['No quotable line', 'Confusing cast'] },
  { id: 'p8', name: 'Neha', age: 33, city: 'Indore', cohort: 'Kitchen radio', listenHabit: 'Hands-busy listening while cooking', dropTriggers: ['Quiet whispers', 'Dense exposition'] },
  { id: 'p9', name: 'Farhan', age: 25, city: 'Lucknow', cohort: 'Suspense purist', listenHabit: 'Needs rising dread every 2 minutes', dropTriggers: ['Flat middle', 'Safe ending'] },
  { id: 'p10', name: 'Tara', age: 21, city: 'Chandigarh', cohort: 'Clip culture', listenHabit: 'Screenshots lines for Stories', dropTriggers: ['No punch dialogue', 'Generic names'] },
  { id: 'p11', name: 'Arjun', age: 27, city: 'Jaipur', cohort: 'Crime addict', listenHabit: 'Walks + gym, high volume', dropTriggers: ['Soft antagonist', 'Moral lecture'] },
  { id: 'p12', name: 'Priya', age: 35, city: 'Pune', cohort: 'Loyalty listener', listenHabit: 'Series follow, finishes every part', dropTriggers: ['Cast inconsistency', 'Broken continuity'] },
  { id: 'p13', name: 'Omar', age: 38, city: 'Bhopal', cohort: 'Family serial', listenHabit: 'Evenings with spouse on speaker', dropTriggers: ['Cruel shock', 'Crude language'] },
  { id: 'p14', name: 'Ritu', age: 30, city: 'Nagpur', cohort: 'Emotional drip', listenHabit: 'Cries easily, loves betrayal arcs', dropTriggers: ['Cold tone', 'No relationship stakes'] },
  { id: 'p15', name: 'Harsh', age: 23, city: 'Surat', cohort: 'Speed skipper', listenHabit: '1.5x playback, ruthless skips', dropTriggers: ['Long narrator bridges', 'Repeat info'] },
  { id: 'p16', name: 'Leela', age: 44, city: 'Coimbatore', cohort: 'Classic drama', listenHabit: 'Afternoon rest, one episode a day', dropTriggers: ['Rushed plot', 'Unclear motives'] },
  { id: 'p17', name: 'Vikram', age: 41, city: 'Chennai', cohort: 'Weekend deep dive', listenHabit: 'Long weekend sessions', dropTriggers: ['Cheap twist', 'Rushed ending'] },
  { id: 'p18', name: 'Zoya', age: 27, city: 'Kochi', cohort: 'Atmosphere seeker', listenHabit: 'Rain + headphones, loves SFX beds', dropTriggers: ['Silent gaps', 'Weak ambience'] },
  { id: 'p19', name: 'Manav', age: 32, city: 'Patna', cohort: 'Whodunit', listenHabit: 'Pauses to guess the culprit', dropTriggers: ['Spoiler-y dialogue', 'Obvious red herring'] },
  { id: 'p20', name: 'Kiran', age: 20, city: 'Vizag', cohort: 'First-timer', listenHabit: 'Trying audio serials for first time', dropTriggers: ['Hard to follow cast', 'No recap'] },
  { id: 'p21', name: 'Asha', age: 36, city: 'Varanasi', cohort: 'Myth-thriller', listenHabit: 'Loves local folklore + modern crime mix', dropTriggers: ['Generic setting', 'No cultural texture'] },
  { id: 'p22', name: 'Siddharth', age: 28, city: 'Gurgaon', cohort: 'Prestige binge', listenHabit: 'Finishes seasons in one sitting', dropTriggers: ['Filler episode', 'Soft cliff'] },
  { id: 'p23', name: 'Pooja', age: 25, city: 'Bhubaneswar', cohort: 'Voice-first', listenHabit: 'Judges casting before plot', dropTriggers: ['Wrong voice age', 'Same-sounding cast'] },
  { id: 'p24', name: 'Imran', age: 34, city: 'Srinagar', cohort: 'Slow-burn loyal', listenHabit: 'Patient for payoff if tone holds', dropTriggers: ['Tone break', 'Forced comedy'] },
  { id: 'p25', name: 'Diya', age: 23, city: 'Thane', cohort: 'Twist hunter', listenHabit: 'Rewinds reveals on loop', dropTriggers: ['Telegraphed twist', 'Soft middle'] },
  { id: 'p26', name: 'Yash', age: 29, city: 'Vadodara', cohort: 'True-crime adjacent', listenHabit: 'Prefers procedural dread', dropTriggers: ['Romance detour', 'No evidence trail'] },
  { id: 'p27', name: 'Naina', age: 31, city: 'Amritsar', cohort: 'Family gossip', listenHabit: 'Discusses plot with sister nightly', dropTriggers: ['Unsympathetic lead', 'Cruel ending'] },
  { id: 'p28', name: 'Reyansh', age: 18, city: 'Ranchi', cohort: 'Gen-Z hop', listenHabit: 'Jumps apps mid-episode', dropTriggers: ['Slow setup', 'No meme line'] },
  { id: 'p29', name: 'Kavya', age: 26, city: 'Mysuru', cohort: 'Soft horror', listenHabit: 'Lights-off listening', dropTriggers: ['Jump-scare spam', 'Weak lore'] },
  { id: 'p30', name: 'Aditya', age: 37, city: 'Nashik', cohort: 'Drive-time', listenHabit: 'Car speakers, traffic windows', dropTriggers: ['Quiet mix', 'Long silence'] },
  { id: 'p31', name: 'Shreya', age: 22, city: 'Guwahati', cohort: 'Dialect curious', listenHabit: 'Notices regional speech texture', dropTriggers: ['Flat accents', 'Stereotype cast'] },
  { id: 'p32', name: 'Nikhil', age: 40, city: 'Udaipur', cohort: 'Legacy serial', listenHabit: 'Grew up on radio plays', dropTriggers: ['Style whiplash', 'Meta jokes'] },
  { id: 'p33', name: 'Ira', age: 27, city: 'Dehradun', cohort: 'Mood listener', listenHabit: 'Picks shows by sonic vibe', dropTriggers: ['Harsh EQ', 'Thin score'] },
  { id: 'p34', name: 'Sameer', age: 33, city: 'Aligarh', cohort: 'Plot accountant', listenHabit: 'Tracks clues in notes', dropTriggers: ['Plot hole', 'Forgotten prop'] },
  { id: 'p35', name: 'Malini', age: 45, city: 'Madurai', cohort: 'Evening ritual', listenHabit: 'Tea + one episode, no binge', dropTriggers: ['Cliff every scene', 'Exhausting pace'] },
  { id: 'p36', name: 'Kabirya', age: 24, city: 'Siliguri', cohort: 'Border binge', listenHabit: 'Late bus rides, spotty network', dropTriggers: ['Needs perfect stream', 'No offline feel'] },
  { id: 'p37', name: 'Trisha', age: 29, city: 'Raipur', cohort: 'Cast chemistry', listenHabit: 'Stays for voices, not plot', dropTriggers: ['Recast mid-arc', 'Flat banter'] },
  { id: 'p38', name: 'Ayaan', age: 21, city: 'Alappuzha', cohort: 'Rain playlist', listenHabit: 'Ambient-heavy monsoon listens', dropTriggers: ['Dry mix', 'No weather bed'] },
  { id: 'p39', name: 'Heena', age: 34, city: 'Jodhpur', cohort: 'Moral stakes', listenHabit: 'Needs clear right/wrong tension', dropTriggers: ['Amoral fog', 'No consequence'] },
  { id: 'p40', name: 'Parth', age: 26, city: 'Rajkot', cohort: 'Hook skeptic', listenHabit: 'Drops shows in first 90 seconds', dropTriggers: ['Generic cold open', 'Narrator dump'] },
  { id: 'p41', name: 'Lavanya', age: 30, city: 'Tirupati', cohort: 'Faith + fear', listenHabit: 'Loves sacred-space dread', dropTriggers: ['Cheap sacrilege', 'No reverence'] },
  { id: 'p42', name: 'Gaurav', age: 39, city: 'Kanpur', cohort: 'Office cab', listenHabit: 'Shared Uber, one earbud polite', dropTriggers: ['Loud swearing', 'Embarrassing twists'] },
  { id: 'p43', name: 'Mira', age: 17, city: 'Shimla', cohort: 'Hidden listen', listenHabit: 'Quiet volume under homework', dropTriggers: ['Sudden loud stingers', 'Adult-only tone'] },
  { id: 'p44', name: 'Raghav', age: 48, city: 'Jamshedpur', cohort: 'Sunday only', listenHabit: 'One long session weekly', dropTriggers: ['Serialized crumbs', 'No payoff block'] },
  { id: 'p45', name: 'Simran', age: 25, city: 'Ludhiana', cohort: 'Share-first', listenHabit: 'Forwards WhatsApp voice notes of lines', dropTriggers: ['No shareable beat', 'Muddy dialogue'] },
  { id: 'p46', name: 'Eshan', age: 28, city: 'Mangalore', cohort: 'Coastal noir', listenHabit: 'Night walks by the sea', dropTriggers: ['City-generic setting', 'No humidity in SFX'] },
  { id: 'p47', name: 'Pallavi', age: 32, city: 'Hubli', cohort: 'Second-screen', listenHabit: 'Scrolls while listening', dropTriggers: ['Needs eyes', 'Complex geography'] },
  { id: 'p48', name: 'Jatin', age: 23, city: 'Bareilly', cohort: 'Rival-show hopper', listenHabit: 'Compares to three other serials', dropTriggers: ['Familiar trope', 'No unique hook'] },
]

type ClusterSpec = {
  cx: number
  cy: number
  spreadX: number
  spreadY: number
  ids: string[]
}

function buildGraph(): { personas: SimPersona[]; edges: Array<[string, string]> } {
  const rand = mulberry32(0x6b155a)

  // Irregular clusters + floating isolates (knowledge-graph feel)
  const clusters: ClusterSpec[] = [
    {
      cx: 38,
      cy: 42,
      spreadX: 28,
      spreadY: 26,
      ids: ['p1', 'p2', 'p3', 'p6', 'p7', 'p8', 'p9', 'p11', 'p12', 'p13', 'p14', 'p15', 'p17', 'p18', 'p19', 'p22', 'p25', 'p26', 'p34'],
    },
    {
      cx: 72,
      cy: 28,
      spreadX: 18,
      spreadY: 16,
      ids: ['p4', 'p5', 'p10', 'p20', 'p23', 'p28', 'p40', 'p45', 'p48'],
    },
    {
      cx: 22,
      cy: 72,
      spreadX: 16,
      spreadY: 14,
      ids: ['p16', 'p21', 'p24', 'p29', 'p32', 'p35', 'p41'],
    },
    // small satellite clique, weakly linked later
    {
      cx: 82,
      cy: 74,
      spreadX: 10,
      spreadY: 10,
      ids: ['p33', 'p38', 'p46'],
    },
  ]

  const isolateIds = ['p27', 'p30', 'p31', 'p36', 'p37', 'p39', 'p42', 'p43', 'p44', 'p47']
  const placed = new Map<string, { x: number; y: number }>()

  for (const cluster of clusters) {
    for (const id of cluster.ids) {
      // jittered blob, not a ring
      const angle = rand() * Math.PI * 2
      const radius = 0.25 + rand() * 0.75
      const x = cluster.cx + Math.cos(angle) * cluster.spreadX * radius * (0.55 + rand() * 0.7)
      const y = cluster.cy + Math.sin(angle) * cluster.spreadY * radius * (0.55 + rand() * 0.7)
      placed.set(id, {
        x: Math.min(94, Math.max(6, x + (rand() - 0.5) * 6)),
        y: Math.min(92, Math.max(8, y + (rand() - 0.5) * 6)),
      })
    }
  }

  // Scattered isolates around the edges
  const isolateSlots = [
    [8, 18],
    [92, 48],
    [12, 48],
    [50, 8],
    [94, 18],
    [6, 88],
    [48, 94],
    [88, 58],
    [30, 6],
    [64, 92],
  ] as const
  isolateIds.forEach((id, i) => {
    const [bx, by] = isolateSlots[i % isolateSlots.length]
    placed.set(id, {
      x: Math.min(95, Math.max(5, bx + (rand() - 0.5) * 8)),
      y: Math.min(94, Math.max(6, by + (rand() - 0.5) * 8)),
    })
  })

  // Hubs: high degree; spokes: few links; isolates: none
  const hubs = ['p2', 'p7', 'p13', 'p18', 'p4']
  const edges: Array<[string, string]> = []
  const edgeKey = (a: string, b: string) => (a < b ? `${a}|${b}` : `${b}|${a}`)
  const seen = new Set<string>()

  const addEdge = (a: string, b: string) => {
    if (a === b) return
    const key = edgeKey(a, b)
    if (seen.has(key)) return
    // never connect full isolates into the main graph
    if (isolateIds.includes(a) || isolateIds.includes(b)) return
    seen.add(key)
    edges.push([a, b])
  }

  const mainIds = PERSONA_SEEDS.map((p) => p.id).filter((id) => !isolateIds.includes(id))

  // Hub → many nearby / random spokes
  for (const hub of hubs) {
    const others = mainIds.filter((id) => id !== hub)
    others.sort((a, b) => {
      const pa = placed.get(a)!
      const pb = placed.get(b)!
      const ph = placed.get(hub)!
      const da = (pa.x - ph.x) ** 2 + (pa.y - ph.y) ** 2
      const db = (pb.x - ph.x) ** 2 + (pb.y - ph.y) ** 2
      return da - db
    })
    const degree = 5 + Math.floor(rand() * 5) // 5–9
    for (let i = 0; i < degree; i++) {
      // prefer near neighbors, occasionally long-range
      const pick = rand() < 0.72 ? others[i] : others[Math.floor(rand() * others.length)]
      addEdge(hub, pick)
    }
  }

  // Sparse local mesh inside each cluster (messy, not complete)
  for (const cluster of clusters) {
    const ids = cluster.ids
    for (let i = 0; i < ids.length; i++) {
      if (rand() < 0.35) continue
      const j = (i + 1 + Math.floor(rand() * 3)) % ids.length
      addEdge(ids[i], ids[j])
      if (rand() < 0.4) {
        const k = Math.floor(rand() * ids.length)
        addEdge(ids[i], ids[k])
      }
    }
  }

  // A few cross-cluster bridges
  const bridges: Array<[string, string]> = [
    ['p3', 'p5'],
    ['p12', 'p16'],
    ['p9', 'p23'],
    ['p22', 'p33'],
    ['p15', 'p40'],
    ['p21', 'p8'],
    ['p46', 'p18'],
  ]
  for (const [a, b] of bridges) {
    if (rand() < 0.9) addEdge(a, b)
  }

  // Tiny satellite internal edges (already in cluster loop); keep it a clique-ish trio
  addEdge('p33', 'p38')
  addEdge('p38', 'p46')

  // Degree → node size
  const degree = new Map<string, number>()
  for (const id of PERSONA_SEEDS.map((p) => p.id)) degree.set(id, 0)
  for (const [a, b] of edges) {
    degree.set(a, (degree.get(a) ?? 0) + 1)
    degree.set(b, (degree.get(b) ?? 0) + 1)
  }

  const personas: SimPersona[] = PERSONA_SEEDS.map((seed, i) => {
    const pos = placed.get(seed.id) ?? { x: 50, y: 50 }
    const d = degree.get(seed.id) ?? 0
    const size = d === 0 ? 0.85 : Math.min(1.55, 0.95 + d * 0.07)
    return {
      ...seed,
      x: pos.x,
      y: pos.y,
      wobbleDelay: (i * 0.17) % 2.4,
      size,
    }
  })

  return { personas, edges }
}

const { personas: PERSONAS, edges: EDGES } = buildGraph()

type Props = {
  active?: boolean
  className?: string
}

export function PersonaGraph({ active = false, className }: Props) {
  const [hovered, setHovered] = useState<string | null>(null)
  const byId = useMemo(() => Object.fromEntries(PERSONAS.map((p) => [p.id, p])), [])
  const hoveredPersona = hovered ? byId[hovered] : null

  const neighborIds = useMemo(() => {
    if (!hovered) return new Set<string>()
    const set = new Set<string>()
    for (const [a, b] of EDGES) {
      if (a === hovered) set.add(b)
      if (b === hovered) set.add(a)
    }
    return set
  }, [hovered])

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-[14px] border border-[var(--folio-border)] bg-[var(--surface-0)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background:
            'radial-gradient(ellipse 70% 55% at 50% 45%, color-mix(in srgb, var(--brand) 12%, transparent), transparent 70%)',
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, color-mix(in srgb, var(--text-muted) 35%, transparent) 1px, transparent 0)',
          backgroundSize: '22px 22px',
        }}
      />

      <svg
        viewBox="0 0 100 100"
        className="relative z-[1] h-[min(56vh,460px)] w-full md:h-[500px]"
        role="img"
        aria-label="Audience persona knowledge graph"
      >
        <defs>
          <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.12" />
            <stop offset="50%" stopColor="var(--brand)" stopOpacity="0.4" />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.12" />
          </linearGradient>
        </defs>

        {EDGES.map(([a, b]) => {
          const pa = byId[a]
          const pb = byId[b]
          if (!pa || !pb) return null
          const lit = hovered === a || hovered === b
          const dimmed = hovered != null && !lit
          // slight curve via mid control offset for organic KG look
          const mx = (pa.x + pb.x) / 2 + (pa.y - pb.y) * 0.08
          const my = (pa.y + pb.y) / 2 + (pb.x - pa.x) * 0.08
          return (
            <path
              key={`${a}-${b}`}
              d={`M ${pa.x} ${pa.y} Q ${mx} ${my} ${pb.x} ${pb.y}`}
              fill="none"
              stroke={lit ? 'var(--brand)' : 'url(#edgeGrad)'}
              strokeWidth={lit ? 0.36 : 0.16}
              strokeOpacity={dimmed ? 0.18 : lit ? 0.9 : active ? 0.65 : 0.45}
              className={cn(active && 'persona-edge-pulse')}
            />
          )
        })}

        {PERSONAS.map((p) => {
          const isHover = hovered === p.id
          const neighbor = neighborIds.has(p.id)
          const dimmed = hovered != null && !isHover && !neighbor
          const rCore = (isHover ? 2.15 : 1.55) * p.size
          const rHalo = (isHover ? 4.4 : neighbor ? 3.5 : 2.8) * p.size
          const gStyle = {
            animationDelay: `${p.wobbleDelay}s`,
            transformOrigin: `${p.x}px ${p.y}px`,
            cursor: 'pointer',
            opacity: dimmed ? 0.35 : 1,
          } as CSSProperties

          return (
            <g
              key={p.id}
              className="persona-node-wobble"
              style={gStyle}
              onMouseEnter={() => setHovered(p.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <circle
                cx={p.x}
                cy={p.y}
                r={rHalo}
                fill="var(--brand)"
                opacity={isHover ? 0.22 : active ? 0.1 : 0.06}
                className="transition-[r,opacity] duration-200"
              />
              <circle
                cx={p.x}
                cy={p.y}
                r={rCore}
                fill="var(--surface-2)"
                stroke="var(--brand)"
                strokeWidth={isHover ? 0.5 : 0.28}
                className="transition-[r,stroke-width] duration-200"
              />
              <circle
                cx={p.x}
                cy={p.y}
                r={0.5 * p.size}
                fill="var(--brand)"
                opacity={isHover ? 1 : 0.85}
              />
              <text
                x={p.x}
                y={p.y + 3.6 + p.size}
                textAnchor="middle"
                fill="var(--text-secondary)"
                style={{ fontSize: '1.7px', fontWeight: 600 }}
                opacity={dimmed ? 0.5 : 0.9}
              >
                {p.name}
              </text>
              <circle cx={p.x} cy={p.y} r={4.6} fill="transparent" />
            </g>
          )
        })}
      </svg>

      {hoveredPersona ? (
        <div
          className="pointer-events-none absolute z-[2] w-[240px] rounded-[12px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] p-3.5 shadow-[var(--shadow-card)]"
          style={{
            left: `clamp(12px, calc(${hoveredPersona.x}% - 120px), calc(100% - 252px))`,
            top: `clamp(12px, calc(${hoveredPersona.y}% + 28px), calc(100% - 180px))`,
          }}
        >
          <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--brand)] uppercase">
            {hoveredPersona.cohort}
          </p>
          <p className="mt-1 text-[15px] font-semibold text-[var(--text-primary)]">
            {hoveredPersona.name}
            <span className="ml-1.5 text-[12px] font-normal text-[var(--text-muted)]">
              {hoveredPersona.age} · {hoveredPersona.city}
            </span>
          </p>
          <p className="mt-2 text-[12px] leading-5 text-[var(--text-secondary)]">
            {hoveredPersona.listenHabit}
          </p>
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {hoveredPersona.dropTriggers.map((t) => (
              <span
                key={t}
                className="rounded-[5px] bg-[var(--surface-1)] px-2 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <p className="absolute bottom-3 left-4 z-[2] text-[11px] text-[var(--text-muted)]">
          Hover a node to inspect a persona · isolates have no links
        </p>
      )}

      <style>{`
        @keyframes persona-wobble {
          0%, 100% { transform: translate(0px, 0px); }
          25% { transform: translate(0.7px, -1.1px); }
          50% { transform: translate(-0.8px, 0.6px); }
          75% { transform: translate(0.9px, 0.5px); }
        }
        @keyframes persona-edge-pulse {
          0%, 100% { stroke-opacity: 0.28; }
          50% { stroke-opacity: 0.7; }
        }
        .persona-node-wobble {
          animation: persona-wobble 3.6s ease-in-out infinite;
        }
        .persona-edge-pulse {
          animation: persona-edge-pulse 2.8s ease-in-out infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .persona-node-wobble,
          .persona-edge-pulse {
            animation: none !important;
          }
        }
      `}</style>
    </div>
  )
}
