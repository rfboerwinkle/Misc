def toSI(line):
	xDiff = line[2]-line[0]
	if xDiff == 0:
		xDiff = 0.000001

	slope = (line[3]-line[1])/xDiff
	yIntrcpt = slope*(line[0]*-1) + line[1]
	return slope, yIntrcpt

def intersect(line1, line2):
	x = (line2[1]-line1[1]) / (line1[0]-line2[0])
	y = line1[0]*x + line1[1]
	return x, y

def bisect(line):
	x = (line[0]+line[2])/2
	y = (line[1]+line[3])/2
	point = [x, y]

	slope = toSI(line)[0]

	if(slope == 0):
		slope -= 0.000001
	slope = (1/slope)*-1
	yIntercept = (slope*x*-1)+y
	return slope, yIntercept

def generate(width, height, S):
	# https://courses.cs.washington.edu/courses/cse326/00wi/projects/voronoi.html

	C = [
		((-width, -height), [
			[width/2, height/2, width/2, -10*height],
			[width/2, -10*height, -10*width, height/2],
			[-10*width, height/2, width/2, height/2]
		]),
		((2*width, -height), [
			[width/2, height/2, width/2, -10*height],
			[width/2, -10*height, 10*width, height/2],
			[10*width, height/2, width/2, height/2]
		]),
		((2*width, 2*height), [
			[width/2, height/2, 10*width, height/2],
			[10*width, height/2, width/2, 10*height],
			[width/2, 10*height, width/2, height/2]
		]),
		((-width, 2*height), [
			[width/2, height/2, width/2, 10*height],
			[width/2, 10*height, -10*width, height/2],
			[-10*width, height/2, width/2, height/2]
		]),
	]

	for site in S:
		cell = (site, [])
		for c in C:
			pb = bisect((site[0], site[1], c[0][0], c[0][1]))
			pbFunc = lambda x : pb[0]*x + pb[1]
			X = []
			sign = site[1] < pbFunc(site[0])
			toDelete = []
			for e in c[1]:
				first = e[1] < pbFunc(e[0])
				second = e[3] < pbFunc(e[2])
				if sign == first == second:
					toDelete.append(e)
				if first != second:
					inter = intersect(pb, toSI(e))
					if first == sign:
						e[0] = inter[0]
						e[1] = inter[1]
					else:
						e[2] = inter[0]
						e[3] = inter[1]
					X.append(inter)
			if X:
				newE = X[0] + X[1]
				c[1].append(list(newE))
				cell[1].append(list(newE))
			for e in toDelete:
				c[1].remove(e)
		C.append(cell)
	return C


### VIEWER CODE ###


import pygame
import random
pygame.init()
import time


MAP = True
DENSITY = 0.1 # doesn't do anything if MAP is False
ALL = False # works a little different based on MAP
COUNT = 500
SCREEN_SIZE = (800, 800)


screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("'Voronoi Cells' map generator")


sites = []
for i in range(COUNT):
	sites.append((random.randint(0,SCREEN_SIZE[0]), (random.randint(0,SCREEN_SIZE[1]))))

start = time.time()
cells = generate(SCREEN_SIZE[0], SCREEN_SIZE[1], sites)
end = time.time()
print(f"Generated {COUNT} cells in {end-start} seconds")

def dispCell(screen, cell):
	for edge in cell[1]:
		pygame.draw.line(screen, (0,255,0), (edge[0], edge[1]), (edge[2], edge[3]))
	pygame.draw.circle(screen, (0,0,255), cell[0], 8)


if ALL:
	for cell in cells:
		dispCell(screen, cell)
	pygame.display.flip()

if MAP:
	inBounds = lambda x,y : x > 0 and y > 0 and x < SCREEN_SIZE[0] and y < SCREEN_SIZE[1]
	edges = set()
	for cell in cells:
		wall = random.random() < DENSITY
		if not wall:
			for edge in cell[1]:
				if not (inBounds(edge[0], edge[1]) and inBounds(edge[2], edge[3])):
					wall = True
					break
		if wall:
			if ALL:
				pygame.draw.circle(screen, (255,0,0), cell[0], 8)
			for edge in cell[1]:
				edge = tuple(round(x, 4) for x in edge)
				if edge in edges:
					edges.remove(edge)
				else:
					edges.add(tuple(edge))
	for edge in edges:
		pygame.draw.line(screen, (255,0,0), (edge[0], edge[1]), (edge[2], edge[3]))
	pygame.display.flip()

i = 0
while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			exit()
		if ALL and not MAP:
			if event.type == pygame.KEYDOWN:
				print("hey")
				screen.fill((0,0,0))
				i += 1
				i %= len(cells)
				dispCell(screen, cells[i])
				pygame.display.flip()
	time.sleep(0.05)

