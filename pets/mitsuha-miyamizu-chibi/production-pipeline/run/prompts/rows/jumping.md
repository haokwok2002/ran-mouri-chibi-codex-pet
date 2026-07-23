Create one horizontal animation strip for Codex pet `mitsuha-miyamizu-chibi`, state `jumping`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly 5 full-body frames in one left-to-right row on flat pure user-selected #00FF00. Treat the row as 5 invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: Mitsuha Miyamizu compact Q-version. Use the supplied green-screen reference as identity authority. Make every animation readable at 192x208 pixels. No scenery, text, floor, cast shadow, glow, detached effects, or green anywhere in the character.. Preserve silhouette, face, proportions, markings, palette, material, style, and props.
Style: Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, clear silhouette, simple face, stable palette/materials, and crisp edges for chroma-key extraction. Style `flat-vector`: Flat vector-style mascot with simple geometric forms, crisp color areas, clean outline, and minimal shading. User style notes: Compact 3-head-tall anime chibi. Large warm brown eyes, dark brown side ponytail tied with a red braided cord and tassels, white short-sleeve school blouse, large red bow, navy pleated skirt, navy knee socks, brown loafers. Keep the broad, low compact silhouette from the reference; clean dark linework, flat color blocks, no shadow or glow..
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: a grounded, gentle five-beat jump loop. The client plays these five frames at a fixed speed, so make the motion feel slower and believable through clear preparation and landing absorption rather than through exaggerated height or pose changes.

State requirements:
- Frame 1 — anticipation: feet planted on the normal baseline; a small, natural crouch with bent knees and lowered center of gravity. Arms and red braided cord relax downward. This is a held preparation pose, not a bounce.
- Frame 2 — lift-off: feet have only just left the baseline; the body is still slightly compressed, knees beginning to extend. Keep the rise modest and smooth.
- Frame 3 — apex: the highest point, but only a gentle hop. Body lengthens naturally without changing character scale; skirt and braided cord/tassel lag upward or outward only slightly.
- Frame 4 — descent: lower than the apex and approaching the baseline; knees start to bend in readiness for impact, with hair cord and skirt returning naturally.
- Frame 5 — landing and recovery: both feet return exactly to the normal baseline; knees are softly bent to absorb the landing and the body is close to the Frame 1 height, ready to loop back without a visible pop.
- Do not make any frame look like a floating hover. Keep the vertical travel modest, the head/body scale constant, and the five poses closely registered so the loop has no size flicker or sideways wobble.
- Do not draw ground shadows, contact shadows, drop shadows, oval shadows, landing marks, dust, smears, bounce pads, or motion marks under the pet.
- Keep the background outside the pet perfectly flat chroma key with no darker key-colored patches.

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet.
