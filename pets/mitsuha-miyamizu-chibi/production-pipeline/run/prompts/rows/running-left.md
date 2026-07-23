Create one horizontal animation strip for Codex pet `mitsuha-miyamizu-chibi`, state `running-left`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly 8 full-body frames in one left-to-right row on flat pure user-selected #00FF00. Treat the row as 8 invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: Mitsuha Miyamizu compact Q-version. Use the supplied green-screen reference as identity authority. Make every animation readable at 192x208 pixels. No scenery, text, floor, cast shadow, glow, detached effects, or green anywhere in the character.. Preserve silhouette, face, proportions, markings, palette, material, style, and props.
Style: Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, clear silhouette, simple face, stable palette/materials, and crisp edges for chroma-key extraction. Style `flat-vector`: Flat vector-style mascot with simple geometric forms, crisp color areas, clean outline, and minimal shading. User style notes: Compact 3-head-tall anime chibi. Large warm brown eyes, dark brown side ponytail tied with a red braided cord and tassels, white short-sleeve school blouse, large red bow, navy pleated skirt, navy knee socks, brown loafers. Keep the broad, low compact silhouette from the reference; clean dark linework, flat color blocks, no shadow or glow..
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: a light, determined eight-beat schoolgirl run toward screen-left. It is a complete alternating gait, not a whole-body slide.

State requirements:
- Show directional drag movement to the left through body, limb, and prop movement only.
- The row must unmistakably face and travel left.
- The movement cadence must alternate visibly across the 8 frames instead of repeating one nearly static stride.
- Frame sequence: left-facing leading-foot contact; gentle compression; rear foot passes under the body; lifted stride; opposite-foot contact; gentle compression; other foot passes; lifted stride returning smoothly to Frame 1.
- Keep the head and face stable in size. Let the torso lean only slightly toward screen-left; let the side ponytail, red cord/tassel, bow tails, and skirt trail a little toward screen-right as natural secondary motion.
- Both feet must remain fully visible and the run must read clearly at pet size without moving the whole character across the slot.
- Do not draw speed lines, dust clouds, floor shadows, motion trails, or detached motion effects.

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet.
