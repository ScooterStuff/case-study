# 04_frontend.md — Chat Interface (Next.js or adapted template)

## Objective
A PartSelect-branded chat experience with rich in-chat components, streaming,
and the "fix-it journey" flow. If Phase 0 found a CRA template in the fork,
implement the SAME component spec inside it (plain React + CSS modules or
Tailwind via CRACO) and skip Next-specific items; record in DEVIATIONS.md.

## Branding tokens (from CONTEXT.md §6 — set as Tailwind theme / CSS vars)
`--ps-teal:#337778; --ps-yellow:#f3c04c; --ps-red:#f4364c; --ps-amber:#FFC107;
--ps-bg:#f6f6f4; --ps-ink:#121212; --ps-muted:#555453; --ps-border:#d7d7d7`
Buttons: teal solid w/ white text (mirror the site's `btn--teal`); secondary:
white w/ teal border. Font: system stack or Inter; clean, utilitarian, rounded-md
cards with subtle borders — match PartSelect's trustworthy-DIY feel, not a
flashy gradient AI app.

## Layout
- Header: "PartSelect" wordmark-style logo text + "Part Assistant" badge; teal.
- Chat pane: message list + composer (textarea, Enter to send, Shift+Enter newline,
  disabled while streaming with a stop button).
- Cart drawer: slide-over from right, badge with item count in header.
- Mobile responsive (single column; cart drawer becomes full-screen sheet).

## Empty state (first impression — invest here)
Greeting from the agent + 4 suggested-prompt chips (clicking sends them):
- "How can I install part number PS11752778?"
- "Is part PS11752778 compatible with my WDT780SAEM1?"
- "My Whirlpool fridge ice maker isn't working"
- "Find a replacement wheel for my dishwasher's bottom rack"
(Yes — seed the exact spec queries. The evaluator will smile.)
Plus a small "Where do I find my model number?" link → modal with a short
explainer (model number is on a sticker/plate: fridge — inside wall near
crisper; dishwasher — door edge/frame) and a simple illustration (inline SVG).

## Message rendering
- Markdown rendering for agent prose (react-markdown), links open new tab.
- Streaming: render `token` events as they arrive with a subtle caret.
- `tool_start` events → status pill above the incoming message: spinner +
  friendly label ("Searching parts…", "Checking compatibility…",
  "Looking up repair guides…"). Replace/stack as tools run; fade on `tool_end`.
- `ui_block` events render as components BETWEEN prose, in arrival order.

## Rich components (one file each in `components/blocks/`)
1. **ProductCard / ProductList** — image, title, PS# + MPN, price, stock badge
   (green "In Stock"), star rating, difficulty chip ("Very Easy install"),
   buttons: "Add to cart", "Check fits my model", "Install guide" (the last two
   send templated chat messages — chat-native navigation, a nice demo beat).
2. **CompatResult** — big ✓ (teal) / ⚠ (amber) / ✗ (red), verdict sentence,
   evidence line ("Verified against PartSelect's cross-reference — this part
   fits NN models including yours"), honesty note for no_match_found, and
   "Show some compatible models" expander.
3. **Diagnosis** — ranked cause list (1, 2, 3 with likelihood framing), each
   cause expandable to its explanation, suggested parts as mini product cards
   under the relevant cause, and chips for the ONE clarifying question when
   the agent asks (e.g. brand chips: Whirlpool / GE / Samsung / LG / Other).
4. **InstallGuide** — difficulty + time + tools header row, embedded YouTube
   thumbnail (click → opens video; don't autoplay), top 2 customer repair
   stories in quote styling with "helpful" counts.
5. **OrderStatus** — order id, status timeline (placed → shipped → delivered),
   mock-data disclaimer in subtle small text.
6. **CartDrawer** — line items, quantities, subtotal, fake checkout button →
   toast "Demo checkout — this is where the real PartSelect flow takes over."
   Cart state in React context, persisted to localStorage*.
   *If artifacts-style restrictions apply in your environment, fall back to
   in-memory state — but in a normal Next.js/CRA app localStorage is fine.

## Plumbing
- `lib/api.ts` — SSE client (fetch + ReadableStream parsing; handle reconnect,
  surface errors as a red system message with retry button).
- `session_id` — uuid in localStorage; cleared by a "New chat" button.
- Keep ALL ui_block prop types in `lib/blocks.ts` mirroring backend payloads;
  one source-of-truth comment pointing to `backend/app/tools.py`.
- Accessibility: focus management to composer, aria-live="polite" on the
  message list, alt text on product images, visible focus rings.

## Acceptance checks
- [ ] All four suggested prompts produce correct rich-component answers
- [ ] Fix-it journey works as one conversation: diagnosis → click part card →
      "Check fits my model" → give model → ✓ verdict → install guide → add to
      cart → cart shows item (RECORD THIS as the demo GIF for README)
- [ ] Streaming text visible < 1.5s after send; tool pills appear/disappear
- [ ] Off-topic question renders the deflection nicely (no broken blocks)
- [ ] `npm run build` clean; no TS errors; mobile viewport (390px) usable
- [ ] `git commit -m "feat(ui): branded chat with rich blocks and fix-it journey"`
