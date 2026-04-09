# Design System Specification: The Ethereal FinTech Identity

## 1. Overview & Creative North Star

### The Creative North Star: "The Digital Luminary"
This design system rejects the "flat and boxy" SaaS standard in favor of a luminous, editorial experience. It is built on the concept of **The Digital Luminary**—an interface that feels less like a software tool and more like a high-end financial concierge. We achieve this through a "Physicality of Light," where depth is defined by how light passes through surfaces rather than how shadows drop from them.

To break the "template" look, designers must embrace **Intentional Asymmetry**. Dashboards should not be perfectly mirrored; use varying card widths and "Editorial White Space" to guide the eye. Overlap glass elements across background tonal shifts to create a sense of three-dimensional space, ensuring the data feels "rich" but never "cluttered."

---

## 2. Colors & Surface Philosophy

Our palette is anchored in Deep Purples and Dark Slates, designed to provide a high-contrast foundation for vibrant, glowing data visualizations.

### The "No-Line" Rule
**Explicit Instruction:** Prohibit the use of 1px solid borders for sectioning. Structural boundaries must be defined solely through background shifts. For example, a `surface-container-low` section sitting on a `surface` background provides all the separation required. 

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of frosted glass. 
*   **Base:** `surface` (#060e20)
*   **Sectioning:** `surface-container-low` (#091328)
*   **Feature Cards:** `surface-container` (#0f1930)
*   **Floating Elements/Modals:** `surface-container-highest` (#192540)

### The "Glass & Gradient" Rule
For primary actions and high-level summaries, use Glassmorphism.
*   **Glass Specs:** Apply a backdrop-blur of `12px` to `24px` on `surface-variant` containers with an opacity of 40-60%.
*   **Signature Textures:** Use a subtle linear gradient (Top-Left to Bottom-Right) transitioning from `primary` (#a3a6ff) to `primary-dim` (#6063ee) for CTAs. This creates a "pulse" of color that flat hex codes cannot replicate.

---

## 3. Typography

The typography strategy pairs the structural precision of **Inter** with the editorial elegance of **Manrope**.

| Level | Font | Token | Role |
| :--- | :--- | :--- | :--- |
| **Display** | Manrope | `display-lg` (3.5rem) | Hero data points (e.g., Net Worth). |
| **Headline** | Manrope | `headline-md` (1.75rem) | Page titles and major section headers. |
| **Title** | Inter | `title-lg` (1.375rem) | Card titles and modal headers. |
| **Body** | Inter | `body-md` (0.875rem) | General data, descriptions, and lists. |
| **Label** | Inter | `label-sm` (0.6875rem) | Micro-data, timestamps, and captions. |

**Editorial Note:** Use `on-surface-variant` (#a3aac4) for secondary body text to maintain a sophisticated, low-contrast hierarchy that highlights the `on-surface` (#dee5ff) primary data.

---

## 4. Elevation & Depth

We eschew traditional material shadows in favor of **Tonal Layering** and **Ambient Glows**.

*   **The Layering Principle:** Depth is achieved by "stacking" tiers. Place a `surface-container-lowest` card on a `surface-container-low` section to create a soft, natural lift.
*   **Ambient Shadows:** For floating elements (modals, dropdowns), use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);`. The shadow color should be a tinted version of the background, never pure black.
*   **The "Ghost Border" Fallback:** If containment is required for accessibility, use a "Ghost Border": the `outline-variant` token at 15% opacity. **Never use 100% opaque borders.**
*   **Backdrop Integration:** Glass elements must use `backdrop-filter: blur(16px)` to allow background "blobs" of `secondary` (#a88cfb) color to bleed through, softening the layout.

---

## 5. Components

### Buttons
*   **Primary:** Gradient of `primary` to `primary-dim`. `roundness-full`. 
*   **Secondary:** Glass effect using `surface-variant` with a `Ghost Border`.
*   **Tertiary:** Pure text using `primary` color, with a subtle underline on hover.

### Input Fields
*   **Surface:** `surface-container-highest` with a 10% `outline`.
*   **Focus State:** Transition the "Ghost Border" to 100% `primary` opacity with a subtle `primary` outer glow (4px blur).
*   **Error:** Use `error` (#ff6e84) for the label text and a `error_container` (#a70138) subtle background glow.

### Cards & Lists
*   **No Dividers:** Lists within cards must use vertical white space (16px - 24px) or a alternating background shift (`surface-container` to `surface-container-high`) instead of lines.
*   **FinTech Specific: The "Metric Cluster":** Group data points using varying typography scales (e.g., a `display-sm` value paired with a `label-md` percentage change) to create "scannable" data density.

---

## 6. Do's and Don'ts

### Do
*   **Do** use `roundness-xl` (1.5rem) for main dashboard cards to evoke a premium, friendly feel.
*   **Do** leverage "Lavender Accents" (`secondary`) for secondary data visualizations (e.g., expense categories).
*   **Do** ensure all text on glass surfaces meets WCAG AA contrast using the `on-surface` token.
*   **Do** use asymmetrical padding—more breathing room at the top of a section than the bottom—to create an editorial flow.

### Don't
*   **Don't** use 1px solid lines to separate table rows; use subtle tonal shifts on hover.
*   **Don't** use pure white (#FFFFFF) for text; use `on-surface` (#dee5ff) to reduce eye strain on dark backgrounds.
*   **Don't** apply glassmorphism to every element. If everything is glass, nothing is special. Reserve it for "floating" or "hero" containers.
*   **Don't** use standard "drop shadows" on cards that are sitting on the base surface. Let the color difference do the work.