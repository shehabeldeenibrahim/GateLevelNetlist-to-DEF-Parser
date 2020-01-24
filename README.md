*********Yosys can be used to generate GLNetlist in JSON format
*********Check documentation http://www.clifford.at/yosys/documentation.html

-usage:
python parser.py <GL-Nlist.json> <LEF file> <output DEF file>  

-The following options MUST be specified:  
-a aspect_ratio Floorplan width to height ratio (default: 1)  
-u core_utilization Core Utilization (default: 0.7)  
-mh horizontal_magin Left and right margins if the row width does not occupy the whole die  
-mv vertical_magin Top and bottom margins if the row width does not occupy the whole die  
-gndl layers GND ring metal layer [1, 2, 3, ..]   
-vddl layers VDD ring metal layer [1, 2, 3, ..]   
-gndw widths of gnd ring metal layers [1, 2, 3, ..]  
-vddw widths of VDD ring metal layers [1, 2, 3, ..]    

-[optional input options]:  
-sw site_width Site width (default: extracted from the LEF file)  
-sh row_height Row Height (default: extracted from the LEF file)  

-usage example:  
python parser.py uart_w2.json osu035.lef out.def -a 1 -u 1 -mh -480 -mv -400 -gndl [1,2,3,4] -vddl [1,2,3,4] -gndw [80,80,120,120]   -vddw [80,80,120,120] -sw 1.6 -sh 4  

-Assumptions:  
*Python 3.6 is installed on the machine  
*All files provided to the software are free of syntax errors  
*All required options are provided  
*User provided the right file paths  

-Limitations  
*Components and pins are unplaced  
