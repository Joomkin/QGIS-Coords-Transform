Transform Coords 
Thanks to Plugin Builder for providing the skeleton to build this. 


Transform Coords is a plugin to help convert coordinates from decimal or grades-minutes-seconds (DMS) to UTM. The user can also make a point in those coordinates. In addition, the user can also simply use it to make a point by introducing UTM coordinates.
Mostly designed for students to have an easier time saving points on QGIS while reading documents with points in different reference systems. 

Requirements: 
QGIS 3.0+
Python 3.x.

How to use: 
In QGIS; Vector > Transform Coords > Transform Coordinates. There, you can pick the coordinate system (decimal; DMS, or UTM) and in the text box you can add the coordinates. You also have the option (checkbox) to make those coordinates into a point, and to name that point. 
Then, write the UTM zone you wish to convert them to (In this exact format: XXS or XXN. Do not put a 0 to the left, just type like 5N). 
Once you are done with that, you simply need to click "Transform" and you will see the UTM coordinates (and obtain a point if you checked the required boxes).


Contact: vicente.rivas@uc.cl or https://github.com/Joomkin/QGIS-Coords-Transform/issues 

Special thanks to: Camilo Marey for helping test the original version, and to Felipe Contreras for telling me to stop procrastinating this. 