from utils import *
from struct import pack
from sys import argv

try:
  out_file = argv[1] # Check if the program has been given arguments
  if out_file[-4:-1] + out_file[-1] != '.bmp':
    out_file += '.bmp' # Append the file extension
except:
  out_file = 'out.bmp' # Default value


r = Render(1000, 1000)
r.glClear(0, 0, 0)
r.glLoad('sphere.obj', V3(500, 500, 0), V3(500, 500, 500))
if r.glWrite(out_file):
  print("Program finished successfully!")


