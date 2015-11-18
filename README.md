This project contains a script that uses [PocketSphinx](cmusphinx.sourceforge.net/) to produce captions
from a video file using speech recognition. The dependencies are a bit tricky,
a Dockerfile is provided to produce a working environment. Specifically,
the script currently relies on [an unlanded patch](https://github.com/luser/pocketsphinx/commit/18f6755caafd04726e76569aa7daa7c6211ea05e) to the PocketSphinx
Gstreamer plugin.

You can test this script with the pre-built docker image `luser/auto-caption:0.1`, for example:
```
docker run -t luser/auto-caption:0.1 ./run.sh https://people.mozilla.org/~tmielczarek/test-long.wav
```

Will produce captions on stdout.

Any copyright is dedicated to the Public Domain.
http://creativecommons.org/publicdomain/zero/1.0/
