# -*- coding: utf-8 -*-

import os, glob
import pandas as pd
import numpy as np
import sys
import datetime
import dateutil.relativedelta
#global variables
BLANK_DIR = 0
today = datetime.datetime.today()

# DATA_MONTH = str(today.month)
DATA_MONTH = str(today.month - 1)
DATA_YEAR = str(today.year)

POSS_DIRECTIONS = ['All Northbound','All Eastbound','All Southbound','All Westbound'] # predefinition of all possible directions.    
# OUT_PATH = r"Q:\WebScraping\Traffic Data IE\Processed_Traffic_data_Latest.csv" # output location for the csv
OUT_PATH = r"D:\Scrappers\Abhiram\Nra_Traffic\Code\Processed_Traffic_data_Latest.csv" # output location for the csv
# DATA_FOLDER = os.path.join(r"Q:\WebScraping\Traffic Data IE", DATA_MONTH + "-" + DATA_YEAR) # folder containing all of the newly downloaded traffic data
DATA_FOLDER = os.path.join(r"D:\Scrappers\Abhiram\Nra_Traffic\Traffic Data IE", DATA_MONTH + "-" + DATA_YEAR) # folder containing all of the newly downloaded traffic data
LOCATION_DATA_PATH = os.path.join(DATA_FOLDER,  'Location_data.csv') # location data for each traffic camera. If the download process is not changed, this should be constant

directions = [] #predefine some lists to store data about the sites in
site_infos = [] 
traffic_data = []

#global functions

def print_error_seperator():
    """
    Prints a load of dashes to make it easier to discern between errors printed by proc_error_mode.
    """
    print('\n--------------------------------------------------------------\n')

def get_camera_location_data(site_id):
    """
    INS: site_name: str, A string of the NAME of the traffic camera site. For example: TMU N01 000.0 
    OUTS: [lat, long]: list of 2 floats, 2 floats representing ng fo the traffic camera site sccording to the file on the shared drive. will return empty list if site not found.
    """
    try:
        loc_df = pd.read_csv(LOCATION_DATA_PATH)# read in lat/long data
    except:
        loc_df = pd.read_excel(LOCATION_DATA_PATH, sheet_name='Omniscope data')

    cam_index = loc_df['cosit'].index[loc_df['cosit']==str(site_id).zfill(12)] # find the index of the site name to be tested 
    if len(cam_index) == 0:
        cam_index = loc_df['cosit'].index[loc_df['cosit']==str(site_id)]
    if len(cam_index) == 0:
        cam_index = loc_df['cosit'].index[loc_df['cosit']==int(site_id)]
 
    if len(cam_index) > 0: # if the site was found in the file
        lat = loc_df['lat'][cam_index].iloc[0] # get lat and long from encoding file
        long = loc_df['lng'][cam_index].iloc[0]
        return[lat,long]
    elif len(cam_index) == 0: # cam site wasn't found in file
        return [] # return empty list
    
def get_default_rules(): #The rules dictionary will work as follows. When a site ID is queried against it. if it is in this dict, then the directions that are to replace the old ones are returned.
    rules = dict()
    rules[20092] = ('All Southbound','All Northbound')
    rules[1281] = ('All Westbound','All Eastbound')
    rules[20071] = ('All Eastbound', 'All Westbound')
    rules[1623] = ('All Northbound', 'All Southbound')
    return rules
    
#MAIN#
if __name__ == "__main__":     

    # Import in the arguments given to the program ##############################
    # This bit of code runs through each argument 1 by 1 until it reaches the end
    # it does this by indexing the arguments until an error happens 
    # the error is caused by the program indexing past the end of the arguments given
    ###########################################################################
    try:
        filename = sys.argv[0]
        input_path = sys.argv[1]
        print('The path to the data folder (which should contain all of the xls files) is:', input_path,'\nplease make sure this is correct.\n')
        if input_path != 'default':
            DATA_FOLDER = input_path
    except IndexError:
        print('No Arguments given, using default values for everything. \nAssuming data path is:',DATA_FOLDER,'\nAnd the data will be placed at',OUT_PATH)

    filenames = glob.glob(os.path.join(DATA_FOLDER,"*.xls")) # gets filenames that end in xls in the given data folder
    try:
        output_path = sys.argv[2]
        print('The output path (where this program will put the processed data) is:',output_path,'\nplease make sure this is correct. it should be the full path to a ".csv" file.\n')
        if output_path != 'default':
            OUT_PATH = output_path
    except IndexError:
        print('no output path given... the data will be place at', OUT_PATH)
   
    try:
        location_data = sys.argv[3]
        print('\nyou said that the XLSX file containing the latitude-longitude data for each site ',location_data,'\nplease make sure this is correct. it should be the full path to a ".XLSX" file.')
        if location_data != 'default':
            LOCATION_DATA_PATH = location_data
    except IndexError:
        print('no location data path given... Assuming it is at', LOCATION_DATA_PATH)
    
    # Set the schema of the output and start the loop #########################
    # This is the main loop that processes the files 1 by 1 
    ###########################################################################
    
    print_error_seperator()
    #Run processing
    schema = ['Site ID', 'Time Of Day', 'All Northbound', 'All Eastbound', 'All Southbound', 'All Westbound', 'Name', 'Address', 'Lat', 'Long', 'Days without blanks'] # desired column headings in the output file.
    data_out = pd.DataFrame(columns = schema)  
  
    rules = get_default_rules()
  
    # picks out xls files. ASSUMES ALL XLS FILES ARE RELAVENT TO TRAFFIC DATA
    for i, file in enumerate(filenames): #iterate through all detected xls files
       
        with open(file) as xhtml_file: # we have to open the file and read in the text as the "xls" files are actually built from xhtml code
           
            # READ IN THE FILE ################################################
            # in this block of code, we read in the files as just text
            # doing that, we see it is in XHTML, luckily pandas can convert that to a dataframe
            # pandas splits these documents up into a few data frames, the first table always represents the site info 
            ###################################################################
            
            xhtml_text = xhtml_file.read()
            df = pd.read_html(xhtml_text) # luckily pandas is very clever and can parse xhtml
            site_infos.append(df[0].iloc[:,0:2])
          
            # CHECK NUMBER 1: BLANK HEADER ####################################
            # sometimes the files have blank headers, this usually means the rest of the file is blank.
            # even if it wasn't we wouldnt be able to attribute this data to a location so it's usless either way
            # files with blank headers get discarded
            ###################################################################
            
            if site_infos[-1].isnull().values.any(): # check latest site info for nans
              print('\nBlank header detected in file:', file, "\nSo we have no site info. Ignoring this file and it's data...\n")
              print_error_seperator()
              continue # skips this file if header contains dud values as nothing of value can be pulled
    
            # FINDING WHICH DATAFRAME CONTAINS THE TRAFFIC DATA ###############
            # It's hard to predict which dataframe will contain the traffic data
            # therefore we must check them all, it is known that the longest dataframe (most rows) will contain the data
            ################################################################### 
            
            df_sizes = []
            rawdf = df
            for j, subdf in enumerate(df): #loop through all data frames and find the one with the biggest size, this will be the data one
                df_sizes.append(len(subdf))
            index = df_sizes.index(max(df_sizes))
            df = df[index]
            
            # FORMATTING THE DATA, FINDING THE DIRECTIONS #####################
            # In this block we name the columns to just numbers
            # we also find the location of rows that contain the word 'all' 
            # these are the start of the tables that contain the directional traffic data
            # we also check if the site appears in the 'rules' dictionary, this changes any sites that have directions like NorthWestbound etc etc
            ###################################################################
            
            df.columns = range(0,len(df.columns))#rename columns to something easier. the imported names were junk anyway.
            table_starts = np.asarray(df.index[df[0].astype(str).str.contains('All')]) #find index of rows containing direction names so we can extract those tables
            
            site_id = int(site_infos[-1].iloc[1,1])
            if site_id in rules:
                directions.append(rules[site_id])
            else:
                directions.append((df[0][table_starts[0]], df[0][table_starts[1]])) # variable for debugging. 
            
            direction1 = df.iloc[table_starts[0]:table_starts[1],:] # uses the searched indexes to pull the directions from the table. Assumes both tables have same number of rows.
            direction2 = df.iloc[table_starts[1]:table_starts[1]+len(direction1),:]
            
            NUM_NON_DAY_COLUMNS = 4
            NUM_DAYS = len(direction1.columns)-NUM_NON_DAY_COLUMNS
            # PULLING THE TOTALS ##############################################
            # In this block we find the last column which is the totals
            # we also crop the data by finding where the first row of all NaNs is
            ###################################################################
           
            last_col_name = direction1.columns[-1] # gets name of last column so we can use .loc instead of .iloc, makes code more readable
            
            data_end1 = direction1[last_col_name].index[direction1[last_col_name].isna()][0]-1 # gives us row IDs (NOT THE INDEXES AS IF IT WAS AN ARRAY) of rows where there are any NaNs, we take the first so we can delete anything after it
            data_end2 = direction2[last_col_name].index[direction2[last_col_name].isna()][0]-1# Same again but for the second direction
            direction1 =  direction1.loc[:data_end1,:] # we have the row IDs not indexes so we crop using .loc
            direction2 =  direction2.loc[:data_end2,:]
            
            # CHECK 2 NaNs in data ############################################
            # NaNs in the data can represent various things, if there are few, then the camera was off for that time
            # It can also represent a blank file, even if the file has a header
            # First we check if there are any Nans at all in the data
            # the we check to see if every read is NaN
            # we also check to see if any of the directions are all NaNs as these are 1 directional cameras
            # If neither of these are true then the camera was just off for a period
            ###################################################################
            #QUICKLY CHECK FOR NANS IN DATA WHICH REPRESENT THE CAMERA BEING OFFLINE FOR A TIME
            NUM_BLANKS_DIR1 = sum(direction1.iloc[:,1:].isna().any())
            NUM_BLANKS_DIR2 = sum(direction2.iloc[:,1:].isna().any())
            NUM_DIR1 = len(direction1.iloc[:,1:].isna().any())
            NUM_DIR2 = len(direction2.iloc[:,1:].isna().any())
            if direction1.iloc[:,1:].isnull().values.any() or direction2.iloc[:,1:].isnull().values.any():
                
              
                if NUM_BLANKS_DIR1 == NUM_DIR1 and NUM_BLANKS_DIR2 == NUM_DIR2: #CHECKS IF THE PROGRAM EXTRACTED NOTHING FROM DATA AS ITS BLANK
                    print('\nNo data at all detected in file:', file, "\nThe following site identifiers are true for this file\n", site_infos[-1])
                    print('\nCheck wether this site was offline or wether there was an issue in the download.')
                    print_error_seperator()
                    continue
                  
                elif NUM_BLANKS_DIR1 == NUM_DIR1 and NUM_BLANKS_DIR2 != NUM_DIR2:
                    print('\nOne directional camera detected in file:', file, "\nThe following site identifiers are true for this file if you want to check\n", site_infos[-1])
                    print_error_seperator()
                    BLANK_DIR = 1
                
                elif NUM_BLANKS_DIR1 != NUM_DIR1 and NUM_BLANKS_DIR2 == NUM_DIR2:
                    print('\nOne directional camera detected in file:', file, "\nThe following site identifiers are true for this file if you want to check\n", site_infos[-1])
                    print_error_seperator()
                    BLANK_DIR = 2
                  
                elif NUM_BLANKS_DIR1 != NUM_DIR1 and NUM_BLANKS_DIR2 != NUM_DIR2:# check latest data for nans      
                    print('\n',NUM_BLANKS_DIR1, 'and', NUM_BLANKS_DIR2, 'columns(days) with blank reads seen in the first and second direction respectivley in file:', file, "\nThe following site identifiers are true for this file\n", site_infos[-1])
                    print('\nThis is normally representative of the camera beig shut down for a bit. THE TOTALS FOR THIS FILE WILL BE SMALLER THAN THEY SHOULD BE, EITHER MANUALLY REPLACE THE "TOTALS" DATA IN THE FILE WITH WEIGHTED UP VALUES OR DELETE THE FILE/ALL THE DATA IN IT SO THE PROGRAM IGNORES IT.')
                    print_error_seperator()
    
            #BACK TO TRANSFORMING THE DATA TO A VECTOR OF INTS
            direction1 = direction1[last_col_name]
            direction2 = direction2[last_col_name]
            
            direction1 = direction1.loc[direction1.iloc[:].index[direction1.iloc[:].str.isnumeric()]] # does a similar operation to the above lines but finds numeric values so we are not assuming the indexes or size of data
            direction2 = direction2.loc[direction2.iloc[:].index[direction2.iloc[:].str.isnumeric()]]
            direction1 = direction1.to_numpy(np.dtype(np.int)).flatten() # flattens out the numpy arrays into simple 1D arrays of numbers
            direction2 = direction2.to_numpy(np.dtype(np.int)).flatten()
            
            #SOMETIMES A FILE OR DIRECTION TABLE WITH NO DATA INSIDE CAN SLIP THROUGH THE ERROR CATCHER ABOVE SO THIS IS HERE AS A REDUNDANCY
            if len(direction1) == 0 and len(direction2) == 0:
                    print('\nNo data at all detected in file:', file, "\nThe following site identifiers are true for this file\n", site_infos[-1])
                    print('\nCheck wether this site was offline or wether there was an issue in the download.')
                    print_error_seperator()
                    continue
                
            elif len(direction1) == 0 and len(direction2) != 0:
                    print('\nOne directional camera detected in file:', file, "\nThe following site identifiers are true for this file if you want to check\n", site_infos[-1])
                    print_error_seperator()
                    direction1 = np.zeros_like(direction2)
                    BLANK_DIR = 1
                    
            elif len(direction1) != 0 and len(direction2) == 0:
                    print('\nOne directional camera detected in file:', file, "\nThe following site identifiers are true for this file if you want to check\n", site_infos[-1])
                    print_error_seperator()
                    direction2 = np.zeros_like(direction1)
                    BLANK_DIR = 2
                    
            #UNLESS SOMETHING CHANGES, DATA SHOULD HAVE 24 VALUES. ONE FOR EACH HOUR
            if len(direction1) != 24 or len(direction2) != 24:
                if BLANK_DIR == 0:
                    print('\nUnusual length data detected in file (should be 24 numbers long):', file, "\nThe following site identifiers are true for this file\n", site_infos[-1])
                    print('Heres a look at the data:',direction1,direction2,"\nwill continue to process however, this program was designed to work with data per hour over 24 hours.")
                    print_error_seperator()
    
            #CHECK DATA FOR NANs 
            elif np.isnan(direction1).any() or np.isnan(direction2).any(): # check latest data for nans
                if BLANK_DIR == 0:
                    print('\nBlank records detected in data:', file, "\nThe following site identifiers are true for this file\n", site_infos[-1])
                    print('Heres a look at the data:',direction1,direction2,"\nThis is a coded redundancy just in case, as of writing. no problems like this have been seen yet.")
                    print_error_seperator()  
            traffic_data.append([direction1, direction2]) # append data to list, helps with debugging
            
            #WRITING DATA TO FILE
            schema = ['Site ID', 'Time Of Day', 'All Northbound', 'All Eastbound', 'All Southbound', 'All Westbound', 'Name', 'Address', 'Lat', 'Long'] # desired column headings in the output file.
            times = ['00:00:00','01:00:00','02:00:00','03:00:00','04:00:00','05:00:00','06:00:00','07:00:00','08:00:00','09:00:00','10:00:00','11:00:00','12:00:00','13:00:00','14:00:00','15:00:00','16:00:00','17:00:00','18:00:00','19:00:00','20:00:00','21:00:00','22:00:00','23:00:00','00:00:00','01:00:00','02:00:00','03:00:00','04:00:00','05:00:00','06:00:00','07:00:00','08:00:00','09:00:00','10:00:00','11:00:00','12:00:00','13:00:00','14:00:00','15:00:00','16:00:00','17:00:00','18:00:00','19:00:00','20:00:00','21:00:00','22:00:00','23:00:00']        
            loc = get_camera_location_data(int(site_infos[-1].iloc[1,1])) # run the function that checks the location data file and gets lat/long so we can put it in the output
            if len(loc) > 0: # if the location data was found correctly, put it in the data. if it wasn't then print the below error
                lat, long = loc
            else:
                print('Site name was not found in the following location data file:',LOCATION_DATA_PATH,'\nThe Lat-Long fields for the following site will be blank:\n',site_infos[-1])
                print_error_seperator() 
                continue
 
            try:
                direction1_name = directions[-1][0]
                direction2_name = directions[-1][1]
                direction1_index = schema.index(direction1_name) # try and find which columns correspond to the directions we have data for
                direction2_index = schema.index(direction2_name)
            except: # sometimes, a camera will have NorthEast as it's direction (just an example) and this is handled by the 'rules' variable, if the site has these daft directions and it isn't in the rules dictionary. we fix it here
                print('The following dodgy directions:', directions[-1], ' Have been found at the following site: ', site_infos[-1], "\n\nAnd this site wasn't in the 'rules' dictionary. The program will now assume that the closest compatible directions are North/South or South/North based on the order they are seen" )
                print_error_seperator()
                if 'North' in directions[-1][0]: # if the word 'North' is seen in the first dodgy direction, then assume data is Northbound then Southbound. and vice versa if it isn't
                    directions[-1] = ('All Northbound', 'All Southbound')
                else:
                    directions[-1] = ('All Southbound', 'All Northbound')
                    
                direction1_index = schema.index(directions[-1][0]) # find the column for the new direction data
                direction2_index = schema.index(directions[-1][1])
                    
            site_data = pd.DataFrame(index=range(len(times)),columns=schema) # create a blank dataframe ready fpr this site's data
          
            for j, hour in enumerate(times): # iterate through the hours.
                site_data.iloc[j,0] = int(site_infos[-1].iloc[1,1]) # for every hour, assign the site ID to the data frame
                site_data.iloc[j,1] = hour # assign the hour to the data frame
                site_data.iloc[j,-4] = site_infos[-1].iloc[0,1] # assign the site name and address to the data frame
                site_data.iloc[j,-3] = site_infos[-1].iloc[3,1]  
                site_data.iloc[j,-2] = lat; site_data.iloc[j,-1] = long
                try:
                    if j <= 23: #for the first 24 hours...
                        site_data.iloc[j,direction1_index] = direction1[j] #print the first directions data
                    elif j >= 24: # then for the second lot of 24 hours....
                        site_data.iloc[j,direction2_index] = direction2[j-24] # print the second directions hours
                except:
                    print(site_data)
                    break
         
            site_data['Days without blanks'] = NUM_DAYS - max(NUM_BLANKS_DIR1, NUM_BLANKS_DIR2) 
            if BLANK_DIR != 0:
                site_data.dropna(subset=[direction1_name, direction2_name], how='all', inplace=True)      
            BLANK_DIR = 0
          
            data_out = data_out.append(site_data, ignore_index = True) # add this site's data to the full data frame
    data_out.to_csv(OUT_PATH, index=False)  # print the data frame to a csv.
#%%