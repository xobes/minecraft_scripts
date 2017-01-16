from mcpi.block import *
import copy

def rect_xz(size_x, size_z, fill):
   return [[fill for z in xrange(size_z)] for x in xrange(size_x)]
def square_xz(size, fill):
   return rect_xz(size, size, fill)
def max_size_x(layer):
   return len(layer)
def max_size_z(layer):
   return max([len(row) for row in layer])
def print_layer(layer):
   for row in layer:
      s = ""
      for col in row:
         if col == None: 
            c = "??"
         else:
            try:
               c = col.id
            except:
               c = col
            c = ("%02d"%(c))[-2:]
         s += "%2s"%(c)
      print s
def replace_blocks(layer, find, repl):
   if not isinstance(find, Block): find = Block(find)
   if not isinstance(repl, Block): repl = Block(repl)
   for x in xrange(len(layer)):
      for z in xrange(len(layer[x])):
         if not isinstance(layer[x][z], Block): layer[x][z] = Block(layer[x][z])
         if layer[x][z] == find:
            layer[x][z] = repl
   return
# end def
def set_block(layer, x, z, fill):
   layer[x][z] = fill

def copy_layer(layer):
   return copy.deepcopy(layer)
def merge_layers(layer1, 
                 layer2, 
                 offset_x=0, 
                 offset_z=0,
                 transparent = True, # set to false to erase layer1
                ):
   ''' E.g. with transparent = True vs. False
                           222                
1111   222              111222          <same>    
1111 + 222 @ (-1, +3) = 1111                            
1111                    1111               
                                                                          
1111   222222            1111         1111                                
1111 + 2    2 @ (1, 1) = 1222222      1222222                             
1111   2    2            1211  2      12    2                             
       222222             2    2       2    2                             
                          222222       222222                             
                                                                          
   '''
   new = []
   neg_x = min(0, offset_x)
   neg_z = min(0, offset_z)
   pos_x = max(0, offset_x)
   pos_z = max(0, offset_z)
   max_x_1 = max_size_x(layer1)
   max_x_2 = max_size_x(layer2)
   max_z_1 = max_size_z(layer1)
   max_z_2 = max_size_z(layer2)
   new_x = max(max_x_1-neg_x,(max_x_2+pos_x))
   new_z = max(max_z_1-neg_z,(max_z_2+pos_z))
   new = rect_xz(new_x, new_z, None)
   for i in xrange(max_x_1):
      for j in xrange(max_z_1):
         block = layer1[i][j]
         new[i-neg_x][j-neg_z] = block
   for i in xrange(max_x_2):
      for j in xrange(max_z_2):
         block = layer2[i][j]
         if transparent and block is None:
            pass
         else: # not transparent, layer 2 wins
            new[i+pos_x][j+pos_z] = block
   return new
   

def define_building(
      num_floors = 5,
      floor_height = 5, # includes the floor which is 1, = 4 blocks inside
      shaft_size = 5,
      window_width = 4,
      num_windows = 4,
      spacer_width = 1,
      flooring_material = STONE,         # flooring material
      building_material = IRON_BLOCK,    # building material
   ):
   size = (window_width+spacer_width) * num_windows + (spacer_width) # windows plus spacers + corner
   
   floor = square_xz(size, flooring_material)
   walls = square_xz(size, building_material)
   inside = square_xz(size-2, AIR) # None is faster if the area is cleared!

   shaft = merge_layers(square_xz(shaft_size, building_material), 
                        square_xz(shaft_size-2, AIR), # so the water flows
                        1, 1, transparent=0)
   door1,door2 = int(round(shaft_size/2.0-0.5)), int(round(shaft_size/2.0+0.5))
   # make a window
   for w in xrange(1,shaft_size-1):
      shaft[0][w] = GLASS
   elev_floor = copy_layer(shaft) # before we cut the door, copy it
   # and a door
   shaft[shaft_size-1][door1] = AIR
   shaft[shaft_size-1][door2] = AIR

   elev_loc = (0, int(size/2-shaft_size/2)) # half-way along the wall

   # make a stepping area near the door
   replace_blocks(elev_floor, building_material, flooring_material)
   elev_floor[shaft_size-2][door1] = flooring_material
   elev_floor[shaft_size-2][door2] = flooring_material

   roof = copy_layer(floor)
   floor = merge_layers(floor, elev_floor, 
                        elev_loc[0],elev_loc[1], 
                        transparent=0)

   walls_with_windows = copy_layer(walls)
   walls = merge_layers(walls, inside, 1, 1, transparent=0)
   walls = merge_layers(walls, shaft, elev_loc[0],elev_loc[1], transparent=0)

   #window_width = 4
   #num_windows = 4
   #spacer_width = 1
   windows_z = rect_xz(window_width, size, GLASS)
   windows_x = rect_xz(size, window_width, GLASS)
   for i in xrange(num_windows):
      offset = spacer_width + ((window_width+spacer_width)*i)
      walls_with_windows = merge_layers(walls_with_windows,
         windows_z, offset, 0)
      walls_with_windows = merge_layers(walls_with_windows,
         windows_x, 0, offset)
   walls_with_windows = merge_layers(walls_with_windows, inside, 1, 1, 
                                     transparent=0)
   walls_with_windows = merge_layers(walls_with_windows, shaft, 
                                     elev_loc[0],elev_loc[1], transparent=0)



   one_floor = [floor] + [walls_with_windows for x in xrange(floor_height-1)]
   top_floor = copy.deepcopy(one_floor)
   top_floor[0] = copy.deepcopy(roof)
   # add the elevator
   # make a window
   for w in xrange(1,shaft_size-1):
      top_floor[0][elev_loc[0]][elev_loc[1]+w]=GLASS
   top_floor[0][elev_loc[0]+shaft_size-3][elev_loc[1]+door1]=WATER_FLOWING
   top_floor[0][elev_loc[0]+shaft_size-3][elev_loc[1]+door2]=WATER_FLOWING
   top_floor[0][elev_loc[0]+shaft_size-4][elev_loc[1]+door1]=WATER_FLOWING
   top_floor[0][elev_loc[0]+shaft_size-4][elev_loc[1]+door2]=WATER_FLOWING
   top_floor.append(roof) # add a roof

   # make the front door
   bottom_floor = copy.deepcopy(one_floor)
   bottom_floor[2][size-1][elev_loc[1]+door1]=AIR
   bottom_floor[2][size-1][elev_loc[1]+door2]=AIR
   bottom_floor[1][size-1][elev_loc[1]+door1]=DOOR_WOOD
   bottom_floor[1][size-1][elev_loc[1]+door2]=DOOR_WOOD

   building = bottom_floor + \
              one_floor * (num_floors-2) + \
              top_floor

   '''
   print_layer(floor)
   print_layer(walls)
   print_layer(walls_with_windows)
   print_layer(top_floor)
   '''
   return building
