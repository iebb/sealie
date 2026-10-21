#!/usr/bin/env python3
"""Export Unicode18 Small Seal as square16x16 glyph sheets; reuse unchanged pages."""
from pathlib import Path
import argparse,hashlib,json,math,time
from PIL import Image,ImageDraw,ImageFont
FIRST,LAST=0x3D000,0x3FC3F
CELL=128;SIDE=16;SIZE=CELL*SIDE+1

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--label-font',type=Path);a=ap.parse_args()
 m=json.loads(a.manifest.read_text());source={int(s['codepoint'][2:],16):s for s in m['sources']};assert all(FIRST<=cp<=LAST for cp in source)
 a.output.mkdir(parents=True,exist_ok=True);index=a.output/'manifest.json';old=json.loads(index.read_text()) if index.exists() else {};prior={s['file']:s for s in old.get('sheets',[])}
 font=ImageFont.truetype(str(a.font),104);labels=ImageFont.truetype(str(a.label_font),11) if a.label_font else ImageFont.load_default(size=11)
 sheets=[];changed=0
 for first in range(FIRST,LAST+1,SIDE*SIDE):
  last=min(first+255,LAST);name=f'U{first:X}-U{last:X}.png';rows=[source[cp] for cp in range(first,last+1) if cp in source];key=hashlib.sha256(json.dumps({'style':1,'first':first,'last':last,'sources':rows,'cell':CELL,'font_size':104},sort_keys=True,separators=(',',':')).encode()).hexdigest();dest=a.output/name
  if name in prior and prior[name]['input_sha256']==key and dest.exists():sheets.append(prior[name]);continue
  im=Image.new('RGB',(SIZE,SIZE),'white');d=ImageDraw.Draw(im)
  for i in range(256):
   cp=first+i;x=i%16*CELL;y=i//16*CELL
   if cp>LAST:d.rectangle((x+1,y+1,x+CELL-1,y+CELL-1),fill='#ededed');continue
   if cp in source:d.text((x+12,y+88.5),chr(cp),font=font,fill='#111111',anchor='ls')
   else:
    d.rectangle((x+1,y+1,x+CELL-1,y+CELL-1),fill='#f7f7f7');d.text((x+64,y+57),'pending',font=labels,fill='#aaaaaa',anchor='mm')
   d.text((x+64,y+115),f'U+{cp:X}',font=labels,fill='#666666' if cp in source else '#a0a0a0',anchor='mm')
  for i in range(17):
   v=i*CELL;d.line((v,0,v,SIZE-1),fill='#cecece',width=1);d.line((0,v,SIZE-1,v),fill='#cecece',width=1)
  im.save(dest,optimize=True);changed+=1;sheets.append({'file':name,'first':f'U+{first:X}','last':f'U+{last:X}','codepoint_cells':last-first+1,'rendered_glyphs':len(rows),'input_sha256':key,'sha256':sha(dest)})
 out={'schema_version':1,'unicode_version':'18.0','block':'Small Seal','first':f'U+{FIRST:X}','last':f'U+{LAST:X}','repertoire_count':LAST-FIRST+1,'rendered_glyphs':len(source),'pending_glyphs':LAST-FIRST+1-len(source),'grid':{'columns':16,'rows':16,'cell_pixels':CELL,'image_pixels':[SIZE,SIZE]},'style':'Regular400, shared rounded monoline; gray cells are explicitly pending, darkgray cells outside block','font_sha256':sha(a.font),'sheets':sheets};index.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'sheets':len(sheets),'changed':changed,'rendered_glyphs':len(source),'pending':out['pending_glyphs']}),flush=True)
if __name__=='__main__':main()
