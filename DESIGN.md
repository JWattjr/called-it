---
name: Called It
description: An ink-and-paper receipts desk for accountable public takes.
colors:
  acid: "#ddf34a"
  acid-hover: "#cbe032"
  acid-active: "#bbd327"
  green: "#38673c"
  red: "#a73e32"
  paper: "#f7f5ed"
  white: "#fffef8"
  ink: "#22251d"
  muted: "#686c5d"
  line: "#d9dace"
  nav-hover: "#eeeee2"
  nav-active: "#e9eddb"
  secondary-hover: "#eceede"
  ink-hover: "#424733"
  card-hover: "#9da28d"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(42px, 4.5vw, 64px)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(25px, 2.2vw, 33px)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.008em"
  title:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.12
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "14px"
    lineHeight: 1.55
  label:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 600
rounded:
  square: "0"
  filter: "20px"
  circle: "50%"
spacing:
  field-gap: "8px"
  action-gap: "12px"
  feed-gap: "19px"
  column-gap: "28px"
  field-padding: "13px 14px"
  card-padding: "22px 24px 0"
components:
  button-primary:
    backgroundColor: "{colors.acid}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "13px 17px"
  button-primary-hover:
    backgroundColor: "{colors.acid-hover}"
  button-primary-active:
    backgroundColor: "{colors.acid-active}"
  button-secondary:
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "12px 15px"
  button-secondary-hover:
    backgroundColor: "{colors.secondary-hover}"
  button-ink:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    padding: "12px"
  button-ink-hover:
    backgroundColor: "{colors.ink-hover}"
  button-wallet:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    padding: "9px 13px"
  field:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "{spacing.field-padding}"
  navigation:
    textColor: "{colors.muted}"
    padding: "12px 11px"
  navigation-active:
    backgroundColor: "{colors.nav-active}"
    textColor: "{colors.ink}"
  filter:
    textColor: "{colors.muted}"
    rounded: "{rounded.filter}"
    padding: "6px 10px"
  filter-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
  take-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "{spacing.card-padding}"
  verdict:
    padding: "5px 10px"
  transaction-disclosure:
    textColor: "{colors.ink}"
---

# Design System: Called It

## Overview

**Creative North Star: "The Receipts Desk"**

Called It feels like a public claim committed to paper: bold, direct, social and inspectable. Warm paper, dark ink and acid-yellow actions give the interface confidence; condensed lettering makes the claim the focal point while clear body type carries its conditions.

The reusable signature is the receipt: a square surface, ruled groups, explicit provenance and a stamped result. Clipped ticket teeth belong to the acid callout; the ordinary feed card stays rectangular. Material character comes from typography, color and geometry. Raster imagery is not required by this system.

**Key Characteristics:**

- Large condensed claims beside quiet, compact metadata.
- Flat paper surfaces and thin rules.
- Acid action emphasis with restrained outcome colors.
- Evidence, state and provenance readable beside their content.

## Colors

The palette combines warm paper neutrals with one sharp action accent and distinct outcome inks. Frontmatter is normative. Core color names map directly to the matching CSS custom properties in `app/globals.css`; state colors are extracted from implemented selectors.

### Primary

- **Acid Yellow** (`acid`): primary actions, count badges, the receipt callout and text selection. Darker hover and pressed variants give direct feedback.
- **Verdict Green** (`green`): affirmative verdicts, brand marks, evidence icons and keyboard focus.
- **Verdict Red** (`red`): missed verdicts and rejected-claim emphasis. Meaning always includes text.

### Neutral

- **Warm Paper** (`paper`): application canvas and sidebar.
- **Receipt White** (`white`): feed receipts, fields, wallet control and mobile navigation.
- **Dark Ink** (`ink`): main text, selected filters and dark actions.
- **Quiet Olive** (`muted`): secondary metadata and void verdicts.
- **Paper Rule** (`line`): borders, separators and resting field edges.
- **Navigation Wash** (`nav-active`): active navigation and receipt banners; the lighter navigation-hover color is separate.
- Other frontmatter colors record implemented secondary-action, dark-action and card hover treatments.

**The Outcome Rule.** Color never substitutes for CALLED IT, MISSED, VOID, rejection copy or provenance text.

## Typography

**Display Font:** Barlow Condensed, sans-serif; self-hosted weights (600, 700).
**Body Font:** DM Sans, sans-serif; self-hosted weights (400, 500, 600, 700).

The condensed face carries confident spoken claims and stamped results. DM Sans keeps rules, evidence, actions and transaction details readable. There is no separate monospace family: identifiers use smaller text, wrapping and tabular numerals where implemented.

- **Display:** frontmatter display role; mobile page headings use (48px).
- **Headline:** frontmatter headline role; take titles become (32px) at the intermediate single-column layout, (30px / 1.06) on mobile and (36px) on wide screens.
- **Title:** frontmatter title role; tertiary headings use (600, 23px / 1.15).
- **Detail claim:** (600, clamp(31px, 3vw, 44px) / 1.05); mobile (34px).
- **Body:** base frontmatter role; paragraphs use line height (1.65). Supporting copy commonly uses (12–13px).
- **Label:** frontmatter label role; compact metadata ranges from (8–11px). The mobile review raises take metadata, categories, author secondary text and card footer copy to (10px), with receipt identifiers at (9px).
- **Verdict:** (700, 28px / 0.95), letter spacing (0.02em); mobile (26px), ruling-panel stamps (25px).

**The Claim Rule.** Keep the whole claim readable. Condensed type establishes hierarchy without truncating the proposition.

## Layout

Desktop has a fixed identity rail (232px), a top bar (76px) and a main region padded (39px 42px 0), capped at (1440px). A flexible feed pairs with a supporting rail (270px), separated by the column-gap token. Single-content views cap at (900px).

Up to (1190px), the identity rail narrows to (192px), main side padding becomes (26px), and the supporting rail becomes (235px), with a (20px) gap. Up to (1020px), the feed becomes one column and supporting content flows below in two columns. At (1600px) and above, the identity rail grows to (252px), main side padding to (55px), and the supporting rail to (300px), with a (40px) gap.

Up to (700px), the sidebar disappears, main padding becomes (29px 18px 0), and fixed bottom navigation (67px) replaces it. The mobile top bar is (67px). Supporting content stacks; the large acid callout is hidden. The footer reserves bottom space (93px). Filter rows scroll horizontally rather than compressing their labels.

Spacing is purpose-based: compact metadata sits within generous receipt groups. Reuse the observed frontmatter field, action, feed and column gaps. Two-column forms collapse on mobile; stake actions wrap. Long identifiers and large stake values wrap within their columns. Definition lists change from label/value columns to stacked pairs.

## Elevation & Depth

Surfaces are flat. There are no implemented shadows. Thin borders, paper/white contrast, tonal banners and the dark proof introduction create hierarchy. Card hover changes the border without lifting the surface.

Motion is restrained: primary-action background transitions (0.18s), card-border transitions (0.2s), a loading spinner (1s linear infinite), and an unseal clip animation (0.3s, cubic-bezier(0.16, 1, 0.3, 1)) for the existing open-details rule. Reduced-motion preferences disable animation, transition and smooth scrolling.

**The Paper Rule.** Preserve the flat ruled surface language when extending the application.

## Shapes

Receipt cards, fields and action surfaces have square edges. Rounded category filters use the filter token; circular avatars and status dots use the circle token. These are specific exceptions, rather than the container language.

Verdict stamps use an outlined rectangle (2px, currentColor), tilted (-7deg). The small callout stamp tilts (-6deg); the logo check tilts (-14deg). Only the acid callout uses the zigzag cut-paper footer (10px high). The signature is an outline and a paper cut, not an image asset.

## Components

### Buttons

Primary actions are square acid surfaces with bold body type (13px, 700), a minimum height (46px) and icon gap (10px). They darken on hover and press. Feed actions use denser sizing; mobile minimum height is (40px).

Secondary actions use an ink outline (1px), type (12px) and minimum height (46px); hover adds a pale wash. Dark callout actions use ink with receipt-white text and an olive hover. The wallet control uses receipt white, a paper-rule outline and compact type (12px, 600); hover changes its outline to ink.

Disabled buttons use opacity (0.5) and a not-allowed cursor. Buttons, links and summaries focus with a green outline (3px), offset (4px). Loading actions show the spinner beside descriptive text.

### Chips and tabs

Category filters are rounded, thinly outlined and muted at rest. Selection reverses to white text on ink. Feed status tabs use a bottom ink rule (2px), stronger weight and optional acid count. Both sets expose selection with `aria-pressed`. Square category labels on receipts are metadata rather than filter controls.

### Cards and receipts

Feed cards use receipt white, a paper-rule border and the frontmatter padding. Hover shifts only the border. Author, claim, metadata, opposing stake action and receipt footer remain distinct groups. Claim links underline on hover.

Detail receipts use a square bordered sheet, side padding (30px; mobile 18px), a tonal provenance banner and ruled sections for the frozen rule, match and ruling. Long hashes wrap. Exact evidence quotes use a pale inset block, condensed text (26px; mobile 24px) and a linked source citation.

### Inputs and fields

Fields have square white surfaces, a paper-rule outline (1px), minimum height (46px) and body type (13px). Labels use the field-gap token; helper copy is muted (10px). Inputs, selects and textareas focus with a green outline (2px), offset (2px). The take textarea uses condensed type (31px / 1.15), paper fill and minimum height (155px); mobile type is (28px).

Validation uses explicit error copy and alert semantics. Errors have a warm tinted surface; notices use a muted paper wash. No distinct per-field error-border or disabled-field treatment is implemented.

### Navigation

Desktop links pair icons with quiet text. Hover adds a wash; active links use tonal fill, ink text and a green trailing dot. Mobile links stack icon and label, with the post action on acid. Preserve native links, meaningful labels and keyboard focus.

### Verdict stamps

CALLED IT uses green, MISSED uses red and VOID uses muted ink. Their tilted outline and condensed uppercase words distinguish a decided receipt. Historical replay and recorded-read labels retain explicit provenance; the stamp alone does not imply a verified live outcome.

### Transaction disclosures and state feedback

Transaction trails and refund-credit panels use native `details`/`summary`, a chevron and visible summary focus. Open trails reveal ruled rows and receipt links. Evidence previews use status semantics; errors use alert semantics. Empty panels explain the missing state and provide a relevant action instead of fabricated activity.

## Do's and Don'ts

### Do:

- **Do** reuse the paper, ink, acid and outcome colors and self-hosted font pair.
- **Do** retain the full claim, readable state labels and visible keyboard focus.
- **Do** use thin rules and flat square surfaces for rules, stakes, sources and transactions.
- **Do** identify recorded reads and historical replays beside the content.
- **Do** preserve wrapping for long identifiers and roomy mobile action rows.
- **Do** honor reduced-motion preferences.

### Don't:

- **Don't** invent wins, balances, verdicts or live provenance to fill a layout.
- **Don't** turn every surface into a rounded card or introduce shadow-based depth.
- **Don't** use verdict color without explicit text.
- **Don't** truncate claims or obscure rule conditions with decoration.
- **Don't** replace receipt geometry with a required raster illustration.
