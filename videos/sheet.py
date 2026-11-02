import sys
from PIL import Image
d=sys.argv[1]; ts=sys.argv[2:]
ims=[Image.open(f'{d}/f_{t}.png').convert('RGB').resize((360,640)) for t in ts]
o=Image.new('RGB',(370*len(ims),640),'#777')
for i,im in enumerate(ims): o.paste(im,(i*370,0))
o.save(f'{d}/sheet.png')
