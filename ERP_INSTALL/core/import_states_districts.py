import pandas as pd
from core.models import State, District

file_path = r"C:\Users\me\OneDrive\Documents\district&state.xlsx"

df = pd.read_excel(file_path, skiprows=1)
df.columns = df.columns.str.strip()

for _, row in df.iterrows():
    state_name = str(row['STATE']).strip()
    district_name = str(row['DISTRICT']).strip()

    if not state_name or state_name.lower() == 'nan':
        continue
    if not district_name or district_name.lower() == 'nan':
        continue

    state, _ = State.objects.get_or_create(state_name=state_name)
    District.objects.get_or_create(
        district_name=district_name,
        state=state
    )

print("✅ Import completed")
