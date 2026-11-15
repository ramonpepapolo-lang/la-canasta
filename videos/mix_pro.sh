# Mezcla "pro" (desde el 15/11/2026): voz + música real (que baja sola cuando habla la voz) + efectos.
#   sh mix_pro.sh <carpeta> <nombre> <musica.mp3>     -> <carpeta>/<nombre>.mp4
# La música sale de la rama "musica" (Kevin MacLeod, CC BY 4.0): su crédito va SIEMPRE en la descripción de YouTube.
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $1/raw.mp4)
FO=$(python3 -c "print(round($D-1.6,2))")
ffmpeg -y -v error -i $1/raw.mp4 -i "$3" -i $1/sfx.wav -filter_complex "
[0:a]asplit=2[v1][vsc];
[1:a]atrim=0:$D,asetpts=PTS-STARTPTS,volume=0.2,afade=t=in:d=0.4,afade=t=out:st=$FO:d=1.6[m];
[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];
[2:a]volume=0.8[s];
[v1][md][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart $1/$2.tmp.mp4 && mv $1/$2.tmp.mp4 $1/$2.mp4 && ffprobe -v error -show_entries format=duration -of csv=p=0 $1/$2.mp4
