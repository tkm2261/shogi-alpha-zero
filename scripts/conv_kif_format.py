import glob
import re
from tqdm import tqdm
for path in tqdm(glob.glob('kif/*kif')):
    with open(path, 'rb') as f:
        txt = f.read().decode('cp932')
    if '　　' in txt:
        print("AAAA")
        txt = re.sub('　+', '　', txt)
        with open(path, 'wb') as f:
            f.write(txt.encode('cp932'))
