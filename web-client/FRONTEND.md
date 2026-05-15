# Stria — Frontend Design

This document is the reference for all UI work on Stria. Build from this. Do not invent layout or interaction patterns not described here.

---

## Design System

### Colours

| Token | Hex | Usage |
|---|---|---|
| `blue-900` | `#0F2E5A` | Hero gradient start, dark backgrounds |
| `blue-700` | `#1A56A0` | Primary brand, buttons, borders, links |
| `blue-50` | `#EFF6FF` | Protocol panel background |
| `red-600` | `#DC2626` | Positive result banner |
| `green-600` | `#16A34A` | Negative result banner |
| `amber-500` | `#F59E0B` | Invalid result banner, faint line indicator |
| `gray-900` | `#111827` | Primary text |
| `gray-500` | `#6B7280` | Secondary text, labels, sources |
| `gray-100` | `#F3F4F6` | Page background, cards |
| `white` | `#FFFFFF` | Card surfaces, input backgrounds |

### Typography

One font throughout: **Inter** (Google Fonts). Fall back to `system-ui`.

| Role | Size | Weight | Usage |
|---|---|---|---|
| Display | 56px / 40px mobile | 700 | Landing headline |
| Heading 1 | 28px | 700 | Section titles |
| Heading 2 | 20px | 600 | Card titles, result outcome |
| Body | 16px | 400 | Explanations, protocol steps |
| Small | 13px | 400 | Labels, source citations, tips |
| Mono | 14px Courier | 400 | Raw observation text |

### Spacing

Base unit: 4px. Use multiples of 4 for all spacing. Standard page padding: 16px horizontal on mobile, 24px on desktop.

### Border Radius

- Cards: `rounded-2xl` (16px)
- Buttons: `rounded-full` (pill)
- Drawers: `rounded-t-2xl` (top corners only)
- Small chips: `rounded-lg` (8px)

### Shadows

Use sparingly. Cards: `shadow-sm`. Drawer: `shadow-2xl`. Nothing else.

---

## Component Map

```
web-client/
├── app/
│   ├── page.tsx                ← Landing page
│   ├── layout.tsx              ← Root layout, Inter font, global metadata
│   └── scan/
│       └── page.tsx            ← Full scan flow, manages step state
│
├── components/
│   ├── landing/
│   │   ├── Hero.tsx            ← Headline, tagline, CTA, phone mockup
│   │   ├── StatsBar.tsx        ← Three statistics strip
│   │   ├── HowItWorks.tsx      ← Three-step explainer
│   │   └── TestTypeGrid.tsx    ← Four disease cards (landing version)
│   │
│   └── scan/
│       ├── TestTypeSelector.tsx   ← Step 1: select cassette type
│       ├── CameraCapture.tsx      ← Step 2: camera feed + guide overlay
│       ├── LightboxTip.tsx        ← Dismissed-once lightbox setup tip
│       ├── ProcessingScreen.tsx   ← Step 3: loading state
│       ├── ResultCard.tsx         ← Step 4: outcome banner + confidence
│       ├── LinesSummary.tsx       ← "What the AI saw" C/T indicators
│       ├── ProtocolPanel.tsx      ← Steps to follow, refer flag
│       └── AssistantDrawer.tsx    ← Step 5: bottom sheet chat
│
├── lib/
│   ├── api.ts                  ← Typed fetch wrappers for all endpoints
│   └── types.ts                ← TypeScript mirrors of stria/models.py
│
└── public/
    └── lightbox-guide.jpg      ← Photo of the imaging stand setup
```

---

## Rules

- App Router only. Never pages router.
- TypeScript strict mode on. No `any`.
- No raw `fetch` in components — use `lib/api.ts`.
- No `<form>` tags — use `onClick` with `FormData`.
- Mobile-first. Every component designed at 390px, then scaled up with `md:` and `lg:` breakpoints.
- The scan flow is a single page (`scan/page.tsx`) with local step state — not separate routes per step. No page reload between steps.
- Camera access uses the browser `MediaDevices` API. Always request `{ video: { facingMode: "environment" } }` (rear camera).
- The lightbox tip dismissal is stored in `localStorage` under key `stria_lightbox_dismissed`.

---

## Landing Page

Single scrollable page. Three visual sections below the nav.

### Nav

```
┌──────────────────────────────────────────┐
│  STRIA                      [Start Scan] │
└──────────────────────────────────────────┘
```

- `STRIA` wordmark left, `font-bold text-blue-700 text-xl tracking-widest`
- `Start Scan` button right: blue pill, white text, links to `/scan`
- Sticky on scroll, white background, 1px bottom border `border-gray-100`
- No other nav items

### Hero

```
┌──────────────────────────────────────────┐
│                                          │
│  Seeing what the          ┌──────────┐   │
│  human eye misses.        │  [phone  │   │
│                           │  mockup] │   │
│  AI-powered RDT reading   │          │   │
│  for community health     └──────────┘   │
│  workers in Ghana.                       │
│                                          │
│  [  Start Scan →  ]                      │
│                                          │
└──────────────────────────────────────────┘
```

- Full viewport height on desktop, auto height on mobile
- White background
- Headline: `text-5xl md:text-7xl font-bold text-gray-900 leading-tight`
  - "what the human eye misses" in `text-blue-700`
- Subheading: `text-lg text-gray-500 mt-4 max-w-sm`
- CTA: `bg-blue-700 text-white px-8 py-4 rounded-full text-lg font-semibold mt-8`
- Phone mockup: static `<img>` of the result screen at ~280px wide. On mobile, hidden (`hidden md:block`). A smaller version shows below the CTA on mobile.

### Stats Bar

```
┌──────────────────────────────────────────┐
│  600K+          up to 30%      200M+     │
│  malaria deaths  RDT misread   tests/yr  │
│  per year        rate (WHO)    in SSA    │
└──────────────────────────────────────────┘
```

- `bg-gray-100 py-10`
- Three columns, centred
- Stat: `text-4xl font-bold text-blue-700`
- Label: `text-sm text-gray-500 mt-1`

### How It Works

```
┌──────────────────────────────────────────┐
│  How it works                            │
│                                          │
│   ①                ②               ③    │
│  [icon]           [icon]           [icon]│
│  Place cassette   Capture photo.   Read  │
│  in the lightbox. Auto-detected.   in 4s.│
│                                          │
└──────────────────────────────────────────┘
```

- Three columns on desktop, stacked on mobile
- Step number: `text-blue-700 font-bold text-sm`
- Icon: simple SVG, 40px, `text-blue-700`
- Title: `font-semibold text-gray-900 mt-3`
- Body: `text-sm text-gray-500 mt-1`

### Test Types Strip

```
┌──────────────────────────────────────────┐
│  Works with                              │
│                                          │
│  [🦟 Malaria] [🦠 COVID] [🤰 Preg.] [🩸 HIV] │
└──────────────────────────────────────────┘
```

- Four pill chips in a row, horizontally scrollable on mobile
- Each: `border border-gray-200 rounded-full px-4 py-2 text-sm text-gray-700 flex items-center gap-2`

### Footer

```
┌──────────────────────────────────────────┐
│  Stria · KNUST · 2026     Not a medical  │
│                           device.        │
└──────────────────────────────────────────┘
```

- `text-xs text-gray-400`
- "Not a medical device." on the right — always visible, never hidden

---

## Scan Flow (`/scan`)

Single page. Step managed by local state: `"select" | "capture" | "processing" | "result" | "assistant"`.

---

### Step 1 — Select Test Type

```
┌─────────────────────┐
│ ←                   │  ← back to landing
│  What type of       │
│  test is this?      │
│                     │
│  ┌────────┐┌──────┐ │
│  │   🦟   ││  🦠  │ │
│  │ Malaria││COVID │ │
│  │        ││      │ │
│  └────────┘└──────┘ │
│  ┌────────┐┌──────┐ │
│  │   🤰   ││  🩸  │ │
│  │Pregnancy││ HIV │ │
│  │        ││      │ │
│  └────────┘└──────┘ │
└─────────────────────┘
```

- White background, 16px padding
- 2×2 grid, `gap-3`
- Each card: `rounded-2xl border-2 border-gray-200 p-5 flex flex-col items-center gap-2 cursor-pointer`
- Selected state: `border-blue-700 bg-blue-50`
- Icon: emoji or SVG, 36px
- Name: `font-semibold text-gray-900 text-sm`
- Description: `text-xs text-gray-500 text-center`
- Tapping a card immediately advances to Step 2 — no confirm button

---

### Step 2 — Camera Capture

```
┌─────────────────────┐
│ ← Malaria RDT    ⚡ │  ← disease name, lightbox tip trigger
│                     │
│  ┌─────────────────┐│
│  │                 ││  ← live camera feed, fills available height
│  │   ┌─────────┐   ││
│  │   │         │   ││  ← guide rectangle
│  │   │         │   ││    dashed white → solid green when detected
│  │   └─────────┘   ││
│  │                 ││
│  └─────────────────┘│
│                     │
│  Place cassette     │  ← instruction, updates based on state
│  in the frame       │
│                     │
│         ⊙           │  ← capture button, 64px circle, blue
└─────────────────────┘
```

**States:**

| Detection state | Guide rectangle | Instruction text |
|---|---|---|
| No cassette found | Dashed white | "Place cassette in the frame" |
| Cassette detected | Solid blue | "Hold steady..." |
| Stable (1.5s held) | Solid green, pulsing | Auto-captures |
| Error (quality fail) | Red border | Specific message e.g. "Too dark — move to better light" |

- Camera feed: `<video>` element, `object-cover w-full`
- Guide rectangle: absolutely positioned `<div>`, transitions via `className`
- Capture button always visible — tapping it captures immediately without waiting for detection
- On capture: freeze the frame as a `<canvas>` → convert to `Blob` → advance to processing

**Lightbox tip (⚡ icon):**

```
┌─────────────────────┐
│  ╔═════════════════╗ │
│  ║  Better results  ║ │
│  ║  [lightbox img]  ║ │  ← lightbox-guide.jpg
│  ║                  ║ │
│  ║  Place cassette  ║ │
│  ║  flat in a small ║ │
│  ║  white box with  ║ │
│  ║  LED lighting.   ║ │
│  ║  [  Got it  ]    ║ │
│  ╚═════════════════╝ │
└─────────────────────┘
```

- Bottom sheet, `rounded-t-2xl`, white background
- Shown automatically on first visit to capture step
- "Got it" sets `localStorage.stria_lightbox_dismissed = "true"` and closes
- ⚡ icon in header always reopens it manually

---

### Step 3 — Processing

```
┌─────────────────────┐
│                     │
│  [captured photo    │
│   blurred, dimmed   │  ← `filter: blur(4px) brightness(0.4)`
│   as background]    │
│                     │
│       STRIA         │  ← blue wordmark, pulsing opacity animation
│                     │
│   Reading test...   │  ← `text-white text-lg`
│                     │
│  ▓▓▓▓▓▓░░░░░░░░░   │  ← progress bar, animates over 4s
│  Analyzing lines    │  ← step label, cycles every ~1.3s:
│                     │    "Detecting cassette"
│                     │    "Analyzing lines"
│                     │    "Checking protocols"
└─────────────────────┘
```

- Captured photo fills the screen as a blurred background
- White overlay at 15% opacity
- All text is white
- Progress bar is fake — CSS animation over 4s. If API returns before 4s, skip to result immediately
- If API takes longer than 8s, show "Taking a moment..." below the bar

---

### Step 4 — Result

```
┌─────────────────────┐
│                     │
│ ┌───────────────────┐│
│ │  POSITIVE         ││  ← bg-red-600 (green/amber for other outcomes)
│ │  Malaria RDT      ││    text-white, padding 20px
│ │  94% confidence   ││    outcome: text-2xl font-bold
│ └───────────────────┘│    cassette type: text-sm opacity-80
│                     │    confidence: text-sm opacity-80
│  What the AI saw    │  ← text-xs font-semibold text-gray-500 uppercase tracking-wider
│                     │
│  C line   ✓ Present │  ← text-sm, checkmark green
│  T line   ⚠ Faint   │  ← text-sm, warning amber (not red — faint ≠ bad)
│                     │
│  "A faint T line    │  ← raw_observation in monospace
│   visible above     │    text-xs text-gray-400 italic
│   the C line"       │    collapsible, collapsed by default
│                     │
│  ─────────────────  │
│                     │
│  [explanation text] │  ← text-base text-gray-700, 3-4 sentences
│                     │
│  ─────────────────  │
│                     │
│  What to do next    │  ← bg-blue-50 rounded-2xl p-4
│                     │
│  · Do not treat     │
│    without clinic   │
│    confirmation     │
│  · Refer patient    │
│    to nearest post  │
│  · Record result    │
│                     │
│  ⚠ Referral needed  │  ← shown only if refer: true, amber chip
│                     │
│  ┌─────────────────┐│
│  │  Ask a question │││  ← bg-blue-700 text-white rounded-full
│  └─────────────────┘│
│                     │
│  [ Scan another ]   │  ← border border-gray-200, gray text, secondary
│                     │
└─────────────────────┘
```

**Outcome banner colours:**

| Outcome | Background | Usage |
|---|---|---|
| `positive` | `bg-red-600` | Malaria antigen detected |
| `negative` | `bg-green-600` | No antigen detected |
| `invalid` | `bg-amber-500` | Test failed — repeat |

**Line indicators:**

| State | Icon | Colour |
|---|---|---|
| Present (strong) | ✓ | `text-green-600` |
| Present (faint) | ⚠ | `text-amber-500` |
| Absent | ✕ | `text-gray-400` |

---

### Step 5 — Assistant Drawer

Triggered by "Ask a question" button. Slides up as a bottom sheet.

```
┌─────────────────────┐
│         ▬           │  ← drag handle, dismisses drawer
│                     │
│  ┌─────────────────┐│
│  │ Malaria · +ve   ││  ← result context chip, sticky
│  │ Faint T line    ││    bg-red-50 border border-red-200 rounded-lg
│  └─────────────────┘│    text-xs text-red-700
│                     │
│  ┌───────────────┐  │
│  │ Stria         │  │  ← assistant message, left-aligned
│  │ A faint T line│  │    bg-gray-100 rounded-2xl rounded-tl-none
│  │ means malaria │  │    text-sm text-gray-900
│  │ antigens were │  │
│  │ detected...   │  │
│  │ ─────────     │  │
│  │ WHO RDT Guide │  │  ← source, text-xs text-gray-400
│  └───────────────┘  │
│                     │
│       ┌───────────┐ │
│       │ What do I │ │  ← user message, right-aligned
│       │ give a    │ │    bg-blue-700 rounded-2xl rounded-tr-none
│       │ 5-yr-old? │ │    text-sm text-white
│       └───────────┘ │
│                     │
│  ┌───────────────┐  │
│  │ Stria         │  │
│  │ For children, │  │
│  │ first-line is │  │
│  │ AL (artemether│  │
│  │ -lumefantrine)│  │
│  │ ─────────     │  │
│  │ GHS Protocol  │  │
│  └───────────────┘  │
│                     │
│ ┌─────────────────┐ │
│ │ Ask about this →│ │  ← input bar, sticky at bottom
│ └─────────────────┘ │
└─────────────────────┘
```

- Drawer height: 75vh, `overflow-y-auto` for messages
- Result context chip is sticky at the top of the drawer — always visible
- Messages scroll, input bar is always at the bottom
- Input: `rounded-full border border-gray-200 px-4 py-3 text-sm` with blue send arrow button
- Sources shown as `text-xs text-gray-400 mt-1 border-t border-gray-100 pt-1` — never hidden, never omitted
- While loading a response: show a pulsing `...` bubble in the assistant position
- Max message history displayed: 20 (scroll for older, but do not load from server during session)

---

## Interaction Notes

**Auto-capture logic in CameraCapture.tsx:**
1. Every 500ms, capture a frame from `<video>` to an offscreen `<canvas>`
2. Send frame to `POST /api/detect-cassette` (lightweight endpoint, no LLM — just OpenCV detection)
3. If cassette detected: show green overlay, start 1.5s stability timer
4. If cassette still detected after 1.5s: auto-capture full frame, advance to processing
5. If cassette lost during timer: reset timer, revert to dashed overlay

> Note: `/api/detect-cassette` is a lightweight polling endpoint. Rate limit: 60/min. It runs only the imaging service's `detect_cassette()` — no vision model call.

**Error handling on result:**
- If API returns a quality failure code: go back to Step 2 (camera), show the failure reason in the instruction text
- If API returns `result_ambiguous`: stay on capture, show "Retake — result was unclear" with a yellow banner
- If API 503 (both providers down): show result with a gray banner and a disclaimer note that explanation is unavailable

**Back navigation:**
- Back arrow from Step 2 → Step 1 (resets type selection)
- Back arrow from Step 4 → Step 2 (keeps type selection, allows rescan)
- No back from Step 3 (processing)
- Closing the assistant drawer does not change step state

---

## API calls from the frontend (`lib/api.ts`)

```typescript
// POST /api/read
readCassette(image: File, cassetteType: string): Promise<ReadResponse>

// POST /api/assistant/message
sendMessage(request: AssistantRequest): Promise<AssistantResponse>

// GET /api/results
getHistory(): Promise<ReadResponse[]>
```

All functions throw a typed `ApiError` on non-2xx responses. Components catch this and display inline error states — no unhandled rejections.

---

## What NOT to Do

- Do not use a separate route for each scan step — it is one page with step state
- Do not show loading spinners inside buttons — use the full ProcessingScreen instead
- Do not hide source citations in the assistant — they are the trust signal
- Do not use red for faint T lines — amber only (faint ≠ bad, it is a degree of positive)
- Do not navigate away from the result to show the assistant — it is a drawer overlay
- Do not request front camera — always `facingMode: "environment"` (rear camera)
- Do not auto-submit on page load — wait for explicit user action at every step
