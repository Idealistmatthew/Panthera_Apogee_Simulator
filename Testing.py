import numpy as np
k_list = np.linspace(2, 1, 100, endpoint=False)[::-1]
k_list=np.insert(k_list,0,1)
print(k_list)