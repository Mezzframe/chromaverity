---
name: chromaverity got a file wrong
about: A real file where the verdict didn't match reality
labels: zoo, accuracy
---

**What chromaverity said** (paste `chromaverity inspect FILE --json`, or attach the report):

**What's actually true about the file, and how you know:**

**ffprobe output** (`ffprobe -v error -show_streams -select_streams v:0 -of json FILE`):

**FFmpeg version** (`ffmpeg -version | head -1`):

Please don't attach footage you don't have the rights to share. The report and ffprobe output are usually enough for us to rebuild the case synthetically.
