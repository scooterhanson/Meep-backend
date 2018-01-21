# Meep Audio Files
All audio alert files follow the format of **alert-(sensor_name).wav**.  When the alarmNotifier class plays a sound based on a specific sensor, it will construct the expected filename and pass it to the audio subprocess.  

**siren.wav** is the exception to this rule.

By default, Meep uses *aplay* for playing the files and *amixer* to set the volume.

The files included were generated at [From Text to Speech](http://www.fromtexttospeech.com/).  This service has a pretty nice speech generation, but it outputs in  *.mp3* format.  I recommend either using [Audacity](https://www.audacityteam.org/) to convert to *.wav* format or using an online converter like [Zamzar](http://www.zamzar.com/convert/mp3-to-wav/) or [Online Convert](https://audio.online-convert.com/convert-to-wav).

