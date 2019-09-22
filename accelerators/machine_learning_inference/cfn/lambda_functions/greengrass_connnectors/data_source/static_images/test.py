import os
import glob
from functools import reduce

module_path = os.path.abspath(os.path.dirname(__file__))
images = reduce(lambda all,image: all + glob.glob(module_path + "/test_img/" + image), ['*.png', '*.jpg'], list())
print(images)