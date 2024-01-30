import pandas as pd

# Define the groups
groups = {
    'Housing type': ['Detatched', 'Semi-Detatched', 'Terraced', 'Flat (Purpose Built)', 'Flat (Converted)', 'Residence in Commercial Building'],
    'Ownership': ['Owned Outright', 'Owned with Mortgage', 'Shared Ownership', 'Rented: From Council', 'Rented: Other Social', 'Rented: Private Landlord', 'Rented: Other', 'Rent Free'],
    'Household Size': ['One Person', 'Two People', 'Three People', 'Four People', 'Five People', 'Six People', 'Seven People', '8+ People'],
    'Age and Gender': ['Male', 'Female', '0 to 4', '5 to 7', '8 to 9', '10 to 14', '15', '16 to 17', '18 to 19', '20 to 24', '25 to 29', '30 to 44', '45 to 59', '60 to 64', '65 to 74', '75 to 84', '85 to 89', '90+'],
    'Marital Status': ['Single', 'Married', 'Divorced', 'Separated', 'Widowed', 'Same Sex'],
    'Education Level': ['Degree or similar', 'Apprenticeship', 'HNC, HND or 2+ A Levels', '5+ GCSE, an A-Level or 1-2 AS Levels', '1-4 GCSEs or Equivalent', 'No GCSEs or Equivalent', 'Other'],
    'Ethnicity': ['White', 'Mixed Ethnicity', 'Indian', 'Bangladeshi', 'Chinese', 'Other Asian', 'Black African', 'Other'],
    'Birthplace': ['England', 'Wales', 'Scotland', 'Northern Ireland', 'Republic of Ireland', 'European Union', 'Other', 'United Kingdom', 'Republic of Ireland', 'Europe (including European Union)', 'African Countries', 'Middle East or Asia', 'North America or Caribbean', 'Central America', 'South America', 'Oceania', 'None'],
    'Religion': ['Christian', 'No Religion', 'Buddhist', 'Hindu', 'Jewish', 'Muslim', 'Sikh', 'Other Religion'],
    'Employment Status': ['Not Stated','Full-Time Employee', 'Part-Time Employee', 'Self Employed', 'Unemployed', 'Full-Time Student', 'Retired', 'Looking after Home or Family', 'Long Term Sick or Disabled', 'Other']

}

# Read the entire CSV into a DataFrame
df = pd.read_csv("pp.csv")

# Filter only the columns that are part of the groups
all_group_columns = [col for sublist in groups.values() for col in sublist]
df_filtered = df[all_group_columns].copy()

# Initialize a list to keep track of final columns to be included in Excel
final_columns = []

# Remove commas and cast columns to float if they are of object type
for column in all_group_columns:
    if df_filtered[column].dtype == 'object':
        df_filtered[column] = df_filtered[column].str.replace(',', '').astype(float)
    else:
        df_filtered[column] = df_filtered[column].astype(float)

# Calculate group totals and convert to percentages
for group, columns in groups.items():
    # Calculate total
    total_column = f"{group} Total"
    df_filtered[total_column] = df_filtered[columns].sum(axis=1)
    
    final_columns.extend(columns)
    final_columns.append(total_column)
    
    # Calculate percentages, avoiding division by zero
    for column in columns:
        df_filtered[column] = df_filtered.apply(lambda row: (row[column] / row[total_column]) * 100 if row[total_column] != 0 else 0, axis=1)

# Write the filtered DataFrame to an Excel file, including only the final columns
with pd.ExcelWriter("Postcode_List_Percent_Filtered.xlsx", engine='xlsxwriter') as writer:
    df_filtered[final_columns].to_excel(writer, index=False, sheet_name='Sheet1')
