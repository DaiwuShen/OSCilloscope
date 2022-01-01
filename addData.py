from os import linesep
import numpy as np
with open('./data.txt','w',encoding='utf8') as f:
    x=np.linspace(0,820,10000)
    y=np.sin(2*x)*np.tan(3*x)
    for i in range(len(x)):
        f.write('{:.2f},{:.2f}\n'.format(x[i],y[i]))