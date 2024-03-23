# The proof of concept project to create a fast world chunking script
Originally written in Pygame, the project was slowing down linearly to the amount of chunks rendered, this was caused by Pygame's inneficient drawing of a large amount of rectangles.
Now rewritten in Arcade, a subset of Pyglet, the complexity of the architecture increased but with that came the ability to render a large amount of rectangles as sprites in a combined spritelist (like an atlas) and multithreading chunk generation.

## It should be noted that running the script by commandline ( or the .bat file ) it has way more performance than debugging in an IDE like VSCode.

Requirements:
- Python <=3.10.11 64-bit

### Name explanations:
- Arcadev:
    Arcade (visualization framework, game framework like pygame) 
    dev (short name for development version of code)
