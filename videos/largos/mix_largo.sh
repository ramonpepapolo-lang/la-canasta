# sh mixdoc.sh <out.mp4>   (in a folder with parts/A.mp4 [B.mp4], voice.wav, bed.wav, sfx.wav)
ls parts/*.mp4 | grep -v tmp | sort | sed "s#^#file '#;s#\$#'#" > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4 && ffmpeg -y -v error -i video.mp4 -i voice.wav -i bed.wav -i sfx.wav -filter_complex "
[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[v1][vsc];
[2:a]volume=0.2,afade=t=in:d=0.5[m];
[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];
[3:a]volume=0.75[s];
[v1][md][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$1.tmp.mp4" && mv "$1.tmp.mp4" "$1" && ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"
