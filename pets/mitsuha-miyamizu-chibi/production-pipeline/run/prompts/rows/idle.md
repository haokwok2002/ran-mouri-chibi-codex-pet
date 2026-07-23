Create one horizontal animation strip for Codex pet `mitsuha-miyamizu-chibi`, state `idle`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly 6 full-body frames in one left-to-right row on flat pure user-selected #00FF00. Treat the row as 6 invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: Mitsuha Miyamizu compact Q-version. Use the supplied green-screen reference as identity authority. Make every animation readable at 192x208 pixels. No scenery, text, floor, cast shadow, glow, detached effects, or green anywhere in the character.. Preserve silhouette, face, proportions, markings, palette, material, style, and props.
Style: Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, clear silhouette, simple face, stable palette/materials, and crisp edges for chroma-key extraction. Style `flat-vector`: Flat vector-style mascot with simple geometric forms, crisp color areas, clean outline, and minimal shading. User style notes: Compact 3-head-tall anime chibi. Large warm brown eyes, dark brown side ponytail tied with a red braided cord and tassels, white short-sleeve school blouse, large red bow, navy pleated skirt, navy knee socks, brown loafers. Keep the broad, low compact silhouette from the reference; clean dark linework, flat color blocks, no shadow or glow..
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: a calm six-beat resting loop for Mitsuha: quiet breathing and one soft blink, with the red braided cord and skirt almost still.

State requirements:
- CRITICAL: idle is the low-distraction baseline state and the first frame is also used as the reduced-motion static pet.
- Use only subtle idle motion: gentle breathing, a tiny blink, a slight head or body bob, a very small material sway, or another quiet motion that fits the pet persona.
- Keep the pet essentially in the same pose, facing direction, silhouette, markings, palette, and prop state across all 6 frames.
- Idle variation must stay calm but still read as animation; do not repeat effectively identical copies across the loop.
- Do not show waving, walking, running, jumping, talking, working, reviewing, emotional reactions, large gestures, item interactions, or new props.
- Feet, base, body, or object anchor should remain planted or nearly planted.
- The first and last frames should be very close visually so the loop feels calm and does not pop.
- Frame 1: relaxed neutral stance, open warm-brown eyes, feet planted.
- Frame 2: a very small inhale lifts the upper body and shoulders without moving the feet.
- Frame 3: a single gentle blink; head stays almost level.
- Frame 4: eyes reopen with the same restrained expression; only a tiny natural sway in the side ponytail cord.
- Frame 5: small exhale and return of the shoulders.
- Frame 6: match Frame 1 closely for a seamless quiet loop.

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet.
