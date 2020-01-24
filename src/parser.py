import json
import math
import sys, getopt

#functions
def open_json(netlist_path):
    with open(netlist_path, 'r') as infile:  
        netlist_json = json.load(infile)
    return netlist_json
def components(netlist_json):
    modules_list = netlist_json["modules"]
    components_list = {}
    #search in each module for each cell used and push in the comp dict
    for module in modules_list:
        for cell in modules_list[module]["cells"]:
            components_list[cell] = modules_list[module]["cells"][cell]
    return components_list
def nets(netlist_json):
    #search for each net in netlist "ports", find its mapped names in 
    #"netnames", list all connected cells and pins

    modules_list = netlist_json["modules"]
    #ports
    ports = {}
    for module in modules_list: 
        for cell in modules_list[module]["ports"]:
            for port in modules_list[module]["ports"]:
                ports[port] = modules_list[module]["ports"][port]

    ports_keys = ports.keys()
    #get nets
    netnames_bits = {}
    netnames_bits_reverse = {}
    for module in modules_list:
        for net in modules_list[module]["netnames"]:
            is_port = 0
            arr = modules_list[module]["netnames"][net]["bits"]
            if net in ports_keys:
                is_port = 1
            #if bus
            if(len(arr) > 1):
                for i in range(0, len(arr)):
                    net_temp = net + "<" + str(i) + ">"
                    netnames_bits[net_temp] = arr[i]
            else: #if single bit
                netnames_bits[net] = arr[0]
            is_port = 0

    #generate reverse lookup from netnames: bits
    for a in netnames_bits:
        netnames_bits_reverse[str(netnames_bits[a])] = a

    #get nets dict;
    netnames_cells = {}
    for module in modules_list:
        for cell in modules_list[module]["cells"]:
            for conn in modules_list[module]["cells"][cell]["connections"]:
                b = modules_list[module]["cells"][cell]["connections"][conn]
                type_b = isinstance(b[0], int)
                if type_b:
                    c = netnames_bits_reverse[str(b[0])]
                else:
                    if b[0] != "0" and b[0] != "1":
                        c = netnames_bits_reverse[b[0]]
                r = []
                try:
                    r = netnames_cells[c]
                except:
                    pass
                stri = cell + " " + conn
                r.append(stri)
                netnames_cells[c] = r

    #add connected ports
    for net_ in netnames_cells:
        n = net_.find('<', 0, len(net_))
        if n > -1:
            net_2 = net_[0:n]
            if net_2 in ports_keys:
                netnames_cells[net_].append('PIN ' + net_)
        else:
            if net_ in ports_keys:
                netnames_cells[net_].append('PIN ' + net_)
    return netnames_cells  
def pins(netlist_json):
    #search for connected pin in the netlist and push them in a dict
    #seperate pins if they are buses
    modules_list = netlist_json["modules"]
    ports = {}
    for module in modules_list: 
        for cell in modules_list[module]["ports"]:
            for port in modules_list[module]["ports"]:
                arr = modules_list[module]["ports"][port]["bits"]
                #if bus
                if(len(arr) > 1):
                    for i in range(0, len(arr)):
                        net_temp = port + "<" + str(i) + ">"
                        
                        ports[net_temp] = modules_list[module]["ports"][port]["direction"]
                else: #if single bit
                     
                    ports[port] = modules_list[module]["ports"][port]["direction"]
    return ports
def getLenWid(area, aspect_ratio):
    #solve for length and width of die area
    w = math.sqrt(area/aspect_ratio)
    if(w!=0):
        l = area/w
    return l, w
def dieArea(util_factor, components_list, macros_sizes, aspect_ratio):
    #die area = total area / coreutil
    #get total area by summing all sites areas used in the gatelevel
    components_types = {}
    area_sum = 0
    for component in components_list:
        components_types[components_list[component]["type"]] = 0
    for component in components_list:
        components_types[components_list[component]["type"]] += 1
    for component in components_types:
        area_sum += float(macros_sizes[component][1]) * float(macros_sizes[component][3]) * components_types[component]
    die_area = area_sum/util_factor
    length, width = getLenWid(die_area, aspect_ratio)
    length = length * 100
    width = width * 100
    return length, width
def macros(macro_index, lines, name):
    #return the required macro size with the given name
    index = macro_index
    lines_length = len(lines)
    while(index != lines_length):
        if((lines[macro_index][0] == "End" and lines[macro_index][1] == name)):
            break
        if(lines[index][0] == "SIZE"):
            return lines[index]
        index += 1
    return -1
def siteCore(site_index, lines, name):
    #return the required site size with the given name
    index = site_index
    lines_length = len(lines)
    while(index != lines_length):
        if((lines[site_index][0] == "End" and lines[site_index][1] == name)):
            break
        if(lines[index][0] == "SIZE"):
            return lines[index][1], lines[index][3]
        index += 1
    return -1
def getMacrosSizes(lines):
    #search for macro sections to get thir sizes and put in a dict
    macros_sizes = {}
    line_index = 0
    for line in lines:
        if line[0] == "MACRO":
            macro_size = macros(line_index, lines, line[1])
            macros_sizes[line[1]] = macro_size
        line_index+=1
    return macros_sizes
def parseLef(lef_path):
    #get required info from lef file such as:
    #macros_sizes, site_wid, site_len, metal_spacing

    f = open(lef_path, "r")
    lines = []
    for line in f:
        line_data = line.split()

        #array of lines
        if(len(line_data)>0):
            lines.append(line_data)
    #get dict of macros sizes
    macros_sizes = getMacrosSizes(lines)  
    site_wid, site_len = getSiteInfo(lines)
    metal_spacing = getMetalSpacing(lines)
    return macros_sizes, site_wid, site_len, metal_spacing
def spacing(site_index, lines, name):
    #get required spacing of the metal with the given name
    index = site_index
    lines_length = len(lines)
    while(index != lines_length):
        if((lines[site_index][0] == "End" and lines[site_index][1] == name)):
            break
        if(lines[index][0] == "SPACING"):
            return lines[index][1]
        index += 1
    return -1
def getMetalSpacing(lines):
    #get all metal layers spaces and push in dict
    spacings={}
    line_index = 0
    for line in lines:
        if line[0] == "LAYER":
            if line[1][0:5] == "metal" :
                spacings[line[1][5]] = spacing(line_index, lines, line[1])
                if len(spacings) == 4:
                    break
        line_index+=1
    return spacings   
def roundLW(x, base):
    return base * round(x/base)
def getBestLW(Len, wid, aspect_ratio, site_len, site_wid):
    #get floor
    Len_floor = math.floor(Len)
    wid_floor = math.floor(wid)
    AR_floor = Len_floor/wid_floor

    #get ceil
    Len_ceil = math.ceil(Len)
    wid_ceil = math.ceil(wid)
    AR_ceil = Len_ceil / wid_ceil

    #check which one is nearest to original Aspect ratio
    diff_ceil = abs(AR_ceil - aspect_ratio)

    diff_floor = abs(AR_floor - aspect_ratio)

    if(diff_floor < diff_ceil):
        Len = Len_floor
        wid = wid_floor
    else:
        Len = Len_ceil
        wid = wid_ceil


    Len = roundLW(Len, site_len)
    wid = roundLW(wid, site_wid)
    Len = round(Len)
    wid = round(wid)
    return Len, wid
def rows(Len, site_len):
    #get # of rows
    rows_number = Len/site_len
    return rows_number
def getSiteInfo(lines):
    #get required info abou core site such as:
    #site width and height
    line_index = 0
    for line in lines:
        if line[0] == "SITE":
            if line[1] == "core" :
                wid, height = siteCore(line_index, lines, "core")
                wid = float(wid)
                height = float(height)
                break
        line_index+=1
    return wid, height
def round_to_nearest_multiple(n, m):
    #return n to the  nearest multiple of m (upper multiple)
    n = int(n)
    m = int(m)
    if(n%m == 0):
        return n
    else:
        while n%m != 0:
            n += 1
        return n
def main(argv):
    #get user inputs
    #options can be given as follows:
    #-a aspect_ratio

    try:
        args, opts = getopt.getopt(argv,"a:u:mh:mv:gnd:vdd")
    except getopt.error: 
        print("input error") 
        sys.exit(2)

    netlist_path = argv[0]
    lef_path = argv[1]
    def_path = argv[2]
    site_w_in = "None"
    site_l_in = "None"
    i = 0
    for opt in argv:
        if(i >= len(argv)-1):
            break
        if opt == '-a':
            aspect_ratio = argv[i+1]
        elif opt == ("-u"):
            util_factor = argv[i+1]
        elif opt == ("-sw"):
            site_w_in = argv[i+1]
        elif opt == ("-sh"):
            site_l_in = argv[i+1]
        elif opt == ("-mh"):
            horizontal_margin = argv[i+1]  
        elif opt == ("-mv"):
            vertical_margin = argv[i+1]
        elif opt == ("-gndl"):
            gnd_layer = argv[i+1]
        elif opt == ("-vddl"):
            vdd_layer = argv[i+1]
        elif opt == ("-gndw"):
            gnd_width = argv[i+1]
        elif opt == ("-vddw"):
            vdd_width = argv[i+1]
        i+=1
    return aspect_ratio , util_factor, horizontal_margin, vertical_margin, gnd_layer, vdd_layer, gnd_width, vdd_width, netlist_path,lef_path, def_path, site_l_in, site_w_in

#microns define unit
units_micron = 100

######################user input############################
aspect_ratio , util_factor, horizontal_margin, vertical_margin, gnd_metal_layer, vdd_metal_layer, gnd_metal_width, vdd_metal_width, netlist_path,lef_path, def_path, site_l_in,site_w_in = main(sys.argv[1:])

#convert the inputs to arrays and floats to fit the algorithm
aspect_ratio = float(aspect_ratio)
util_factor = float(util_factor)
horizontal_margin = float(horizontal_margin)
vertical_margin = float(vertical_margin)

gnd_metal_layer = gnd_metal_layer[1:len(gnd_metal_layer)-1]
gnd_metal_layer = gnd_metal_layer.split(",")
gnd_metal_layer = list(map(int, gnd_metal_layer))

vdd_metal_layer = vdd_metal_layer[1:len(vdd_metal_layer)-1]
vdd_metal_layer = vdd_metal_layer.split(",")
vdd_metal_layer = list(map(int, vdd_metal_layer))


gnd_metal_width = gnd_metal_width[1:len(gnd_metal_width)-1]
gnd_metal_width = gnd_metal_width.split(",")
gnd_metal_width = list(map(int, gnd_metal_width))

vdd_metal_width = vdd_metal_width[1:len(vdd_metal_width)-1]
vdd_metal_width = vdd_metal_width.split(",")
vdd_metal_width = list(map(int, vdd_metal_width))

print(aspect_ratio , util_factor, horizontal_margin, vertical_margin, gnd_metal_layer, vdd_metal_layer, gnd_metal_width, vdd_metal_width)


#################################open file#####################################
netlist_json = open_json(netlist_path)


###########################get components list and their number############################
components_list = components(netlist_json)
number_of_components = len(components_list)

################################get nets#######################################
nets = nets(netlist_json)
number_of_nets = len(nets)

#################################pins################################
pins = pins(netlist_json)
number_of_pins = len(pins)

##################################parse lef##########################
macros_sizes, site_wid, site_len, metal_spacings = parseLef(lef_path)

#if site height or width was not specified, extract from lef
if site_l_in == "None":
    print("")
else:
    print("hey")
    site_len = float(site_l_in)

if site_w_in == "None":
    print("")
else:
    site_wid = float(site_w_in)

site_len *= units_micron
site_wid *= units_micron

###########################Die area###################################
Len, wid = dieArea(util_factor, components_list, macros_sizes, aspect_ratio)


##################round to multiple of site width and height###########
#Len, wid = getBestLW(Len, wid, aspect_ratio, site_len, site_wid)
Len = round_to_nearest_multiple(Len, site_len)
wid = round_to_nearest_multiple(wid, site_wid)

##########################rows#################################
number_rows = rows(Len, site_len)
number_sites = wid/(site_wid)
site_spacing = 160


#get module name
for a in netlist_json['modules']:
    top = a
    break

#######################write in file############################
with open(def_path, 'a') as file_:

    file_.write("VERSION 5.7 ;\nNAMESCASESENSITIVE ON ;\nDIVIDERCHAR "+'"/"'+" ;\nBUSBITCHARS "+ '"<>"' + " ;\nDESIGN "+ top + " ;\nUNITS DISTANCE MICRONS " + str(units_micron) +" ;\n")

    file_.write('DIEAREA ( ' + str(horizontal_margin) + " " + str(vertical_margin) + " ) "+ '( ' + str(wid + horizontal_margin) + ' ' + str(Len + vertical_margin) + ' ) ;\n\n')
    
    for i in range(0, int(number_rows)):
        if(i%2 == 0):
            orientation = "N"
        else:
            orientation = "FS"
        file_.write("ROW ROW_" + str(i) + " core " + str(vertical_margin) + " " + str((i+1)*site_len) + " " + orientation +
        " DO " + str(number_sites) + " BY " + "1" + " STEP " + str(site_spacing) +" 0  ;\n")
    file_.write("\n\n")

    file_.write('COMPONENTS '+ str(number_of_components) + ' ;\n')  
    for component in components_list:
        file_.write('   - ' + component + ' ' + components_list[component]["type"] +' + UNPLACED ( 0 0 ) N' + ' ;\n')
    file_.write("END COMPONENTS\n\n")   
    
    file_.write('PINS '+ str(number_of_pins) + ' ;\n')
    for pin in pins:
        file_.write('   - ' + pin + " + NET " + pin + ' ;\n')
    file_.write("END PINS\n\n")
        
    file_.write('NETS '+ str(number_of_nets) + ' ;\n')
    for net in nets:
        file_.write('   - ' + net +'\n')
        for cell in nets[net]:
            file_.write("       ( " + cell + " ) \n")
        file_.write("   + USE SIGNAL ; \n")
        
    file_.write("END NETS\n\n")

    file_.write('SPECIALNETS 2'+' ;\n')
    file_.write('   - vdd\n')

    
    #######################vdd#######################
    index = 0
    for metal_layer in vdd_metal_layer:
        #vertical vdd
        if metal_layer % 2 == 1:
            file_.write("       NEW metal" + str(metal_layer) + " " + str(vdd_metal_width[index]) 
            + " ( " + str(horizontal_margin) + " " + str(vertical_margin) + " ) " + "( * " + str(Len + vertical_margin) + " )\n")     

            file_.write("       NEW metal" + str(metal_layer) + " " + str(vdd_metal_width[index]) 
            + " ( " + str(horizontal_margin + wid) + " " + str(vertical_margin) + " ) " + "( * " + str(Len + vertical_margin) + " )\n")     
        else:
            #horizontal vdd
            file_.write("       NEW metal" + str(metal_layer) + " " + str(vdd_metal_width[index]) 
            + " ( " + str(horizontal_margin) + " " + str(vertical_margin) + " ) " + "( " + str(horizontal_margin + wid) + " * )\n")     

            file_.write("       NEW metal" + str(metal_layer) + " " + str(vdd_metal_width[index]) 
            + " ( " + str(horizontal_margin) + " " + str(Len + vertical_margin) + " ) " +  "( " + str(horizontal_margin + wid) + " * )\n")     
        index += 1
    file_.write("   ;\n")

    ##################gnd####################################
    file_.write('   - gnd\n')
    index = 0
    for metal_layer in gnd_metal_layer:
        vdd_gnd_spacing = float(metal_spacings[str(metal_layer)])
        #vertical gnd
        if metal_layer % 2 == 1:
            file_.write("       NEW metal" + str(metal_layer) + " " + str(gnd_metal_width[index]) 
            + " ( " + str(horizontal_margin + vdd_gnd_spacing) + " " + str(vertical_margin + vdd_gnd_spacing) + " ) " + "( * " + str(Len + vertical_margin - vdd_gnd_spacing) + " )\n")     

            file_.write("       NEW metal" + str(metal_layer) + " " + str(gnd_metal_width[index]) 
            + " ( " + str(horizontal_margin + wid - vdd_gnd_spacing) + " " + str(vertical_margin + vdd_gnd_spacing) + " ) " + "( * " + str(Len + vertical_margin - vdd_gnd_spacing) + " )\n")     
        else:
            #Horizontal gnd
            file_.write("       NEW metal" + str(metal_layer) + " " + str(gnd_metal_width[index]) 
            + " ( " + str(horizontal_margin + vdd_gnd_spacing) + " " + str(vertical_margin + vdd_gnd_spacing) + " ) " + "( " + str(horizontal_margin + wid + vdd_gnd_spacing) + " * )\n")     

            file_.write("       NEW metal" + str(metal_layer) + " " + str(gnd_metal_width[index]) 
            + " ( " + str(horizontal_margin + vdd_gnd_spacing) + " " + str(Len + vertical_margin - vdd_gnd_spacing) + " ) " +  "( " + str(horizontal_margin + wid - vdd_gnd_spacing) + " * )\n")     
        index += 1
    file_.write("   ;\n")
    file_.write("END SPECIALNETS\n")

    file_.write("END DESIGN\n")