# Slitherchunk
Slitherchunk - Proof of Concept chunking in Python.

Originally written in **Pygame**, the project was slowing down linearly to the amount of chunks rendered, this was caused by Pygame's inefficient drawing of large amounts of individual rectangles.
Now rewritten in **Arcade**, a subset of **Pyglet**, the complexity of the architecture increased but with that came the ability to render a large amount of rectangles as sprites in a combined sprite-list and the ability of multi-threading chunk generation.

**It should be noted that running the script by command-line ( or the .bat file ) has way more performance than debugging in an IDE like VSCode.**

Requirements:
- Python <=3.10.11 64-bit
