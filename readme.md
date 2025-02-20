# Alphen's Isometric Subway Simulator
open-source pygame-based isometric train simulator, probably

## Features
- isometric graphics (duh)
- 3 types of rolling stock (there will be more!)
- the ability to create almost **any** user content, from maps to trains.

## Controls (player)
- Arrow keys -basic movement
- S - spawn menu
- Shift, Alt - speed modifiers
- Q - debug modes

## Controls (train)
- 9 - Reverser -
- 0 - Reverser +
- Up - traction +
- Down - traction -
- R - brake -
- F - brake +
- Use mouse to click buttons

## Train control handle explanations
Type "A" train:
- 5-1: Traction
- 0: Neutral
- -1-2: Reverse traction

Type "E" and "Ezh" trains:
- 3-1: Traction
- 0: Neutral
- -1: Handbrake (viable only on high speeds)
- -1a: Semi-auto brake (viable only on high speeds)
- -2: Full auto brake with additional pressure

Type 334 pneumatic driver's valve (requires motor-compressor to work):
- 1: Turbo discharge
- 2 (default): Discharge
- 3: Hold mode (pressure is constant)
- 4: Service brake
- 5: Emergency brake
