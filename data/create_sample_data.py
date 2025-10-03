import pandas as pd

# Your sample data as a DataFrame
data = {
    'employee_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'first_name': ['Jessika', 'Donni', 'Pat', 'Raddie', 'Sidonnie', 'Burnard', 'Stanley', 'Bunnie', 'Izak', 'Barton'],
    'last_name': ['Hulcoop', 'Alps', 'Frick', 'Gostick', 'Oganesian', 'Roote', 'Jennens', 'Dorricott', 'Burwin', 'Leguey'],
    'salary': [127518.76, 100688.92, 96735.41, 149368.4, 90661.82, 104105.49, 116501.5, 123178.12, 31391.41, 70522.72],
    'hire_date': ['9/16/2010', '12/5/2020', '3/14/2001', '11/16/2017', '11/5/2010', '8/9/2020', '6/29/2007', '1/24/2021', '7/3/2011', '6/18/2017'],
    'department_id': [5, 3, 2, 1, 1, 2, 4, 5, 3, 1],
    'department': ['IT', 'Marketing', 'IT', 'IT', 'Finance', 'Marketing', 'IT', 'Sales', 'Marketing', 'IT'],
    'residence_city': ['Babushkin', 'Ukmerge', 'Kiruru', 'São Félix do Xingu', 'Bayt Liqyā', 'Weishanzhuang', 'Taznakht', 'Sharkawshchyna', 'Nkoteng', 'Yanzhao'],
    'age': [44, 26, 42, 46, 41, 40, 37, 42, 31, 33],
    'job_level': ['Mid Level', 'Executive', 'Entry Level', 'Entry Level', 'Entry Level', 'Executive', 'Executive', 'Entry Level', 'Mid Level', 'Executive']
}

# Create DataFrame with ALL 500 rows (I'll truncate for brevity, but you have the full data)
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('data/employees.csv', index=False)
print("Sample data created successfully!")