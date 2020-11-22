from struct import pack
# Data Modifier Functions
def char(c):
  return pack('=c', c.encode('ascii'))

def word(c):
  return pack('=h', c)

def dword(c):
  return pack('=l', c)

def bbox(*vertices):
  xs = [vertex.x for vertex in vertices]
  ys = [vertex.y for vertex in vertices]
  xs.sort()
  ys.sort()

  xMin, xMax = xs[0], xs[-1]
  yMin, yMax = ys[0], ys[-1]

  return xMin, xMax, yMin, yMax

def barycentric(A, B, C, P):
  c = V3(B.x - A.x, C.x - A.x, A.x - P.x).cross(V3(B.y - A.y, C.y - A.y, A.y - P.y))

  if abs(c.z) < 1: return -1, -1, -1

  u = c.x / c.z
  v = c.y / c.z
  w = 1 - (c.x + c.z) / c.z

  return w, v, u



class V2:
  def __init__(self, x, y):
    self.x = x
    self.y = y
  
  def __str__(self):
    return '(%s, %s)' % (self.x, self.y)

class V3:
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z
  
  def __str__(self):
    return '(%s, %s, %s)' % (self.x, self.y, self.z)

  def sum(self, v1):
    return V3(self.x + v1.x, self.y + v1.y, self.z + v1.z)
  
  def sub(self, v1):
    return V3(self.x - v1.x, self.y - v1.y, self.z - v1.z)
  
  def mul(self, k):
    return V3(self.x * k, self.y * k, self.z * k)
  
  def dot(self, v1):
    return self.x * v1.x + self.y * v1.y + self.z * v1.z
  
  def length(self):
    return ((self.x * self.x) + (self.y * self.y) + (self.z * self.z))

  def norm(self):
    current_length = self.length()

    if not current_length: return V3(0, 0, 0)

    return V3(
      self.x / current_length, 
      self.y / current_length, 
      self.z / current_length
      )

  def cross(self, w):
    return V3(
      self.y * w.z - self.z * w.y,
      self.z * w.x - self.x * w.z,
      self.x * w.y - self.y * w.x
    )

class Color:
  def __init__(self, r, g, b):
    self.r = self.interval(0, 255, r)
    self.g = self.interval(0, 255, g)
    self.b = self.interval(0, 255, b)

  def toBytes(self):
    return bytes([self.b, self.g, self.r])
  
  def interval(self, min, max, number):
    if min > number: return min
    if max < number: return max
    return number

  def __str__(self):
    return 'Color(%s, %s, %s)' % (self.r, self.g, self.b)


class Obj(object):
  def __init__(self, to_open):
    with open(to_open) as f:
      self.lines = f.read().splitlines()
    self.vertices, self.faces = [], []
    self.read()

  def read(self):
    for line in self.lines:
      if line:
        prefix, value = line.split(' ', 1)

        if prefix == 'v':
          self.vertices.append(list(map(float, value.split(' '))))
        
        elif prefix == 'f':
          self.faces.append([list(map(int, face.split('/'))) for face in value.split(' ')])

class Render(object):
  def __init__(self, width: int, height: int) -> None:
    self.framebuffer = []
    self.zbuffer = []
    self.width = 800 if width < 0 else width
    self.height = 600 if height < 0 else height
    print('Set frame %sx%s' % (self.width, self.height))

  def glClear(self, r: float, g: float, b: float) -> None:
    r, g, b = round(r * 255), round(g * 255), round(b * 255)
    self.framebuffer = [
      [Color(r, g, b).toBytes() for x in range(self.width)]
      for y in range(self.height)
    ]

    self.zbuffer = [
      [-float('inf') for x in range(self.width)]
      for y in range(self.height)
    ]

  
  def glColor(self, r: float, g: float, b: float) -> Color:
    r = round(r * 255)
    g = round(g * 255)
    b = round(b * 255)
    return Color(r, g, b)

  def glWrite(self, to_write: str) -> bool:
    try:
      with open(to_write, 'bw') as f:
        f.write(char('B'))
        f.write(char('M'))
        f.write(dword(54 + self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(54))
        f.write(dword(40))
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))
        f.write(word(24))
        f.write(dword(0))
        f.write(dword(self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))

        for x in range(self.width):
          for y in range(self.height):
            f.write(self.framebuffer[y][x])
      return True
    except Exception as e:
      print(e)
      return False


  def point(self, x: int, y: int, color: bytes):
    try:
      self.framebuffer[x][y] = self.glColor(color[0], color[1], color[2]).toBytes()
    except:
      pass

  def triangle(self, A: V3, B: V3, C: V3, colored: bytes) -> None:
    xMin, xMax, yMin, yMax = bbox(A, B, C)
    for x in range(xMin, xMax + 1):
      for y in range(yMin, yMax + 1):
        P = V2(x, y)
        w, v, u = barycentric(A, B, C, P)

        if w < 0 or v < 0 or u < 0: continue

        z = A.z * w + B.z * u + C.z * v

        try:
          if z > self.zbuffer[x][y]:
            self.point(x, y, colored)
            self.zbuffer[x][y] = z
        except:
          pass

  def glLoad(self, to_open: str, translation: V3, size: V3) -> None:
    model = Obj(to_open)

    light = V3(0, 0, 1)

    for face in model.faces:
      vcount = len(face)
      
      if vcount == 2:
        continue
      elif vcount == 3:
        f1 = face[0][0] - 1
        f2 = face[1][0] - 1
        f3 = face[2][0] - 1

        v1 = V3(model.vertices[f1][0], model.vertices[f1][1], model.vertices[f1][2])
        v2 = V3(model.vertices[f2][0], model.vertices[f2][1], model.vertices[f2][2])
        v3 = V3(model.vertices[f3][0], model.vertices[f3][1], model.vertices[f3][2])

        x1 = round((v1.x * size.x) + translation.x)
        y1 = round((v1.y * size.y) + translation.y)
        z1 = round((v1.z * size.z) + translation.z)

        x2 = round((v2.x * size.x) + translation.x)
        y2 = round((v2.y * size.y) + translation.y)
        z2 = round((v2.z * size.z) + translation.z)

        x3 = round((v3.x * size.x) + translation.x)
        y3 = round((v3.y * size.y) + translation.y)
        z3 = round((v3.z * size.z) + translation.z)

        A = V3(x1, y1, z1)
        B = V3(x2, y2, z2)
        C = V3(x3, y3, z3)

        bSa = B.sub(A)
        cSa = C.sub(A)
        normal = bSa.cross(cSa)

        intensity = normal.dot(light)
        grey = round(intensity / 255)
        if grey < 0: continue

        intColor = Color(grey, grey, grey).toBytes()
        self.triangle(A, B, C, intColor)
      else:
        f1 = face[0][0] - 1
        f2 = face[1][0] - 1
        f3 = face[2][0] - 1
        f4 = face[3][0] - 1   

        v1 = V3(model.vertices[f1][0], model.vertices[f1][1], model.vertices[f1][2])
        v2 = V3(model.vertices[f2][0], model.vertices[f2][1], model.vertices[f2][2])
        v3 = V3(model.vertices[f3][0], model.vertices[f3][1], model.vertices[f3][2])
        v4 = V3(model.vertices[f4][0], model.vertices[f4][1], model.vertices[f4][2])

        x1 = round((v1.x * size.x) + translation.x)
        y1 = round((v1.y * size.y) + translation.y)
        z1 = round((v1.z * size.z) + translation.z)

        x2 = round((v2.x * size.x) + translation.x)
        y2 = round((v2.y * size.y) + translation.y)
        z2 = round((v2.z * size.z) + translation.z)

        x3 = round((v3.x * size.x) + translation.x)
        y3 = round((v3.y * size.y) + translation.y)
        z3 = round((v3.z * size.z) + translation.z)

        x4 = round((v4.x * size.x) + translation.x)
        y4 = round((v4.y * size.y) + translation.y)
        z4 = round((v4.z * size.z) + translation.z)

        A = V3(x1, y1, z1)
        B = V3(x2, y2, z2)
        C = V3(x3, y3, z3)
        D = V3(x4, y4, z4)

        bSa = B.sub(A)
        cSa = C.sub(A)
        normal = bSa.cross(cSa)

        intensity = normal.dot(light)

        grey = round(intensity * 255)

        if grey < 0: continue

        intColor = Color(grey, grey, grey).toBytes()
        self.triangle(A, D, C, intColor)


  



