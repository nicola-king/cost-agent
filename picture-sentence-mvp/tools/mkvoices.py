import numpy as np, glob, os
d={}
for f in glob.glob('dl/kokoro-js-1.2.1/package/voices/*.bin'):
    a=np.fromfile(f,dtype=np.float32); d[os.path.basename(f)[:-4]]=a.reshape(-1,1,256)
np.savez('voices.npz',**d); print(len(d), d['af_heart'].shape)
