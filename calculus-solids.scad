// Models 3D objects by taking a 2D base (defined by two functions and two x values), slicing it up perpendicular to the X-axis, and using the resulting line as a base for another 2D object.
// The slices are trapezoidal approximations with adjustable width.
// It can also rotate about the X- and Y-axis.


// starting x value
StartX = 0;
// ending x value
EndX = 8;
// size of slice
StepX = 0.05;


// f(x) and g(x) are functions.
// Math functions can be found here:
// https://openscad.org/cheatsheet
function f(x) = x^(2/3);
function g(x) = 0;


// "Slice" should be a list of points of [y,z].  These are the slices.
// It will later be scaled so that difference between f(x) and g(x) is 1, and translated so that [0,0] is on the line f(x).
// This means that any shape with a flat base will start off with "Slice = [[0,0], [1,0], ..."
// Also, please contain the y values to between 0 and 1.
// ...or you could just use one of these pre-made ones by uncommenting it and commenting out the rest.
// (Comments are denoted by the "//" at the beginning of the line.)

// semicircle
//Slice = [for(a = [0:1:180]) [(cos(a)/2)+0.5, (sin(a)/2)]];

// circle (not rotation)
//Slice = [for(a = [0:1:360]) [(cos(a)/2)+0.5, (sin(a)/2)]];

// isosceles right triangle with leg on base(right angle closest to x axis)
Slice = [[0,0], [1,0], [0,1]];

// isosceles right triangle with leg on base(right angle farthest from x axis)
//Slice = [[0,0], [1,0], [1,1]];

// isosceles right triangle with hypotenuse on base
//Slice = [[0,0], [1,0], [0.5,0.5]];

// equilateral triangle
//Slice = [[0,0], [1,0], [0.5,(3^(1/2))/2]];

// square
//Slice = [[0,0], [1,0], [1,1], [0,1]];


// This should be "true" or "false".  If it is "false", it does regular slices.  If it is "true", it rotates about an axis.
// Note: If you rotate, neither of the functions can be negative.
Rotation = false;

// This is for rotation, the number of sides the circle has.  If it is "false", sets it to OpenSCAD's default value.
NumberOfSteps = 100;

// If it is "true", it will rotate around the X-Axis. If it is "false", it will rotate around the Y-Axis
XAxisRotation = false;


// That's it! Everything else is code that doesn't need to change.
// If you are having problems you could try:
// https://openscad.org/cheatsheet
// https://en.wikibooks.org/wiki/OpenSCAD_User_Manual
// or me: rfboerwinkle@gmail.com


// P.S. If you want holes, you can use this "Paths" variable.  You can learn more in the user manual.
Paths = false;

if(Rotation){
	polygonpoints = [for (x = [StartX:StepX:EndX]) [x,f(x)], for (x = [EndX:-StepX:StartX]) [x,g(x)]];
	if(XAxisRotation){
		rotate(a = [0,-90,0])
		rotate_extrude($fn = NumberOfSteps)
		rotate(a = [0,0,-90])
		polygon(points = polygonpoints);
	}else{
		rotate(a = [-90,0,0])
		rotate_extrude($fn = NumberOfSteps)
		polygon(points = polygonpoints);
	}
}else{
	pointlist = [for (x = [StartX:StepX:EndX]) [x, (f(x)>g(x)?f(x):g(x)), (f(x)>g(x)?g(x):f(x))]];
	for(i = [1:len(pointlist)-1]){
		if((pointlist[i][1] - pointlist[i][2]) != 0){
			scalefactor = (pointlist[i-1][1] - pointlist[i-1][2]) / (pointlist[i][1] - pointlist[i][2]);
			distance = (scalefactor == 0) ? -pointlist[i-1][1] : (((pointlist[i][2] - pointlist[i-1][2]) / (1-scalefactor)) - pointlist[i][2]);
			rotate(a = [90,0,90])
			mirror(v = [0,0,1])
			translate(v = [-distance,0,-pointlist[i][0]])
			linear_extrude(height = StepX, scale = scalefactor, slices = 1)
			translate(v = [distance,0,0])
			translate(v = [pointlist[i][2],0,0])
			resize([(pointlist[i][1] - pointlist[i][2]),0,0], auto=true)
			polygon(points = Slice, paths = Paths);
			if(i+1 < len(pointlist) && (pointlist[i+1][1] - pointlist[i+1][2]) == 0){
				rotate(a = [90,0,90])
				mirror(v = [0,0,1])
				translate(v = [-distance,0,-pointlist[i][0]])
				mirror(v = [0,0,1])
				linear_extrude(height = StepX, scale = 0, slices = 1)
				translate(v = [distance,0,0])
				translate(v = [pointlist[i][2],0,0])
				resize([(pointlist[i][1] - pointlist[i][2]),0,0], auto=true)
				polygon(points = Slice, paths = Paths);
			}
		}
	}
}
