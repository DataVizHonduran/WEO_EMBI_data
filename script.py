import pandas as pd
import requests
from io import StringIO
import weo
from datetime import datetime
import json
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

current_year = datetime.now().year
current_month = datetime.now().month

# Try multiple WEO releases in order of preference
download_attempts = [
    (2025, 2),  # October 2025
    (2025, 1),  # April 2025
    (2024, 2),  # October 2024
    (2024, 1),  # April 2024
    (2023, 2),  # October 2023
]

weo_downloaded = False
weo_filepath = os.path.join(SCRIPT_DIR, 'weo.csv')

for weo_year, weo_release in download_attempts:
    try:
        print(f"Attempting to download WEO data: {weo_year} Release {weo_release}")
        weo.download(year=weo_year, release=weo_release, filename=weo_filepath)
        
        # Verify it's actually a CSV by checking first line
        with open(weo_filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if '<html>' in first_line.lower() or '<head>' in first_line.lower():
                print(f"  ✗ Downloaded file is HTML, not CSV (redirect or error page)")
                continue
        
        print(f"  ✓ Successfully downloaded {weo_year} Release {weo_release}")
        weo_downloaded = True
        break
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        continue

if not weo_downloaded:
    raise RuntimeError("Could not download WEO data from any available release. Please download manually from https://www.imf.org/en/Publications/WEO/weo-database")

# Get current year
current_year = datetime.now().year

# Get EMB holdings data
url = 'https://www.ishares.com/us/products/239572/ishares-jp-morgan-usd-emerging-markets-bond-etf/1467271812596.ajax?fileType=csv&fileName=EMB_holdings&dataType=fund'
response = requests.get(url)
csv_data = StringIO(response.text)
df = pd.read_csv(csv_data, skiprows=9)

# Extract countries
countries = df['Location'].dropna().unique()

# Country mapping to ISO codes
country_mapping = {
    'Angola': 'AGO', 'Argentina': 'ARG', 'Bahrain': 'BHR', 'Brazil': 'BRA', 
    'Bulgaria': 'BGR', 'Chile': 'CHL', 'China': 'CHN', 'Colombia': 'COL',
    'Costa Rica': 'CRI', 'Cote D\'Ivoire (Ivory Coast)': 'CIV', 'Dominican Republic': 'DOM', 
    'Ecuador': 'ECU', 'Egypt': 'EGY', 'Ghana': 'GHA', 'Guatemala': 'GTM',
    'Hungary': 'HUN', 'Jamaica': 'JAM', 'Jordan': 'JOR', 'Kazakhstan': 'KAZ',
    'Kenya': 'KEN', 'Latvia': 'LVA', 'Malaysia': 'MYS', 'Mexico': 'MEX',
    'Morocco': 'MAR', 'Nigeria': 'NGA', 'Oman': 'OMN', 'Pakistan': 'PAK',
    'Panama': 'PAN', 'Peru': 'PER', 'Philippines': 'PHL', 'Poland': 'POL',
    'Romania': 'ROU', 'Saudi Arabia': 'SAU', 'Serbia': 'SRB', 'South Africa': 'ZAF',
    'Sri Lanka': 'LKA', 'Turkey': 'TUR', 'Ukraine': 'UKR', 'United Arab Emirates': 'ARE',
    'Uruguay': 'URY'
}

# Filter countries that exist in mapping
embi_countries = [country_mapping.get(country, country) for country in countries if country in country_mapping]

# Try to initialize WEO data - with error handling for column issues
print("\nAttempting to load WEO data...")
try:
    w = weo.WEO(weo_filepath)
    print("✓ WEO data loaded successfully using weo library")
except KeyError as e:
    print(f"⚠ WEO library encountered column issue: {e}")
    print("Inspecting CSV structure...")
    
    # Read the CSV directly to inspect
    df_inspect = pd.read_csv(weo_filepath, nrows=5, sep='\t')
    print(f"Available columns: {df_inspect.columns.tolist()}")
    
    # Try alternative approach - read the full CSV
    print("\nAttempting to read WEO CSV directly...")
    df_weo = pd.read_csv(weo_filepath, sep='\t')
    
    # Look for country-related columns
    country_cols = [col for col in df_weo.columns if 'country' in col.lower() or 'iso' in col.lower()]
    print(f"Found potential country columns: {country_cols}")
    
    # Create a custom WEO-like wrapper
    class CustomWEO:
        def __init__(self, df):
            self.df = df
            # Try to identify the country code column
            self.country_col = None
            for col in ['ISO', 'WEO Country Code', 'Country Code', 'ISO3']:
                if col in df.columns:
                    self.country_col = col
                    break
            
            if not self.country_col:
                raise ValueError(f"Could not identify country code column. Available columns: {df.columns.tolist()}")
            
            print(f"Using '{self.country_col}' as country identifier")
        
        def getc(self, variable_code):
            """Get variable data by country"""
            # Filter for the variable
            var_data = self.df[self.df['WEO Subject Code'] == variable_code].copy()
            
            if var_data.empty:
                raise ValueError(f"Variable {variable_code} not found")
            
            # Get year columns (they're typically numeric column names)
            year_cols = [col for col in var_data.columns if str(col).isdigit()]
            
            # Set country as index
            var_data = var_data.set_index(self.country_col)
            
            # Return only year columns, convert to numeric
            result = var_data[year_cols].apply(pd.to_numeric, errors='coerce')
            result.columns = result.columns.astype(int)
            
            return result.T  # Transpose so years are rows
    
    w = CustomWEO(df_weo)
    print("✓ Created custom WEO wrapper")

# Variable definitions
var_dict = {
    'NGDPD':'GDP (US Dollars)',
    'LP':'Population',
    'NGDP_RPCH': 'Real GDP growth (%)',
    'NID_NGDP': 'Total investment (% of GDP)',
    'NGSD_NGDP': 'National savings (% of GDP)',
    'PCPIPCH': 'Inflation, consumer prices (%)',
    'GGR_NGDP': 'General government revenue (% of GDP)',
    'GGX_NGDP': 'General government total expenditure (% of GDP)',
    'GGXCNL_NGDP': 'General government net lending/borrowing (% of GDP)',
    'GGXONLB_NGDP': 'General government net borrowing (% of GDP)',
    'GGXWDG_NGDP': 'General government gross debt (% of GDP)',
    'BCA_NGDPD': 'Current account balance (% of GDP)',
}

# Initialize data dictionaries
current_year_data = {}
median_10yr_data = {}
data_2019 = {}

# Helper function to get year from index
def extract_year_from_index(idx):
    """Extract year from various index formats"""
    try:
        # Handle Period objects
        if hasattr(idx, 'year'):
            return idx.year
        else:
            return int(idx)
    except:
        return str(idx)

# Helper function to find specific year in series
def get_year_data(series_data, target_year):
    """Get data for a specific year, or closest available year"""
    # Convert index to years
    index_years = [extract_year_from_index(idx) for idx in series_data.index]
    
    # Try to find exact year
    if target_year in index_years:
        year_pos = index_years.index(target_year)
        return series_data.iloc[year_pos].sort_values(), target_year
    
    # Find closest year
    numeric_years = [y for y in index_years if isinstance(y, int)]
    if numeric_years:
        closest_year = min(numeric_years, key=lambda x: abs(x - target_year))
        year_pos = index_years.index(closest_year)
        return series_data.iloc[year_pos].sort_values(), closest_year
    
    # Fallback to last available year
    return series_data.iloc[-1].sort_values(), "last_available"

# Collect data for all three datasets
print("\nCollecting data for variables...")
for var in var_dict.keys():
    try:
        # Get full time series for all countries
        series_data = w.getc(var)[embi_countries]
        
        # Current year (2025) or closest available year
        current_values, used_year = get_year_data(series_data, current_year)
        current_year_data[var] = current_values
        if used_year != current_year:
            print(f"Current year {current_year} not found for {var}, using {used_year} instead")
        
        # 10-year median (last 10 years)
        median_10yr = series_data.loc[pd.Period(current_year-9, freq='A'):pd.Period(current_year, freq='A')].median().sort_values()
        median_10yr_data[var] = median_10yr
        
        # 2019 values
        try:
            values_2019, used_year_2019 = get_year_data(series_data, 2019)
            data_2019[var] = values_2019
            if used_year_2019 != 2019:
                print(f"2019 not found for {var}, using {used_year_2019} instead")
            
        except Exception as e:
            print(f"Error getting 2019 data for {var}: {e}")
            # Create a series with NaN values for all countries to maintain structure
            data_2019[var] = pd.Series([float('nan')] * len(embi_countries), index=embi_countries).sort_values()
        
        print(f"✓ Successfully collected data for {var}")
        
    except Exception as e:
        print(f"✗ Error collecting data for {var}: {e}")
        current_year_data[var] = None
        median_10yr_data[var] = None
        data_2019[var] = None

# Create the three dataframes
# Filter out None values to avoid DataFrame creation issues
clean_current_data = {k: v for k, v in current_year_data.items() if v is not None}
clean_median_data = {k: v for k, v in median_10yr_data.items() if v is not None}
clean_2019_data = {k: v for k, v in data_2019.items() if v is not None}

df_current_year = pd.DataFrame(clean_current_data).rename(columns=var_dict)
df_10yr_median = pd.DataFrame(clean_median_data).rename(columns=var_dict)
df_2019 = pd.DataFrame(clean_2019_data).rename(columns=var_dict)

# Display summary information
print("\n=== SUMMARY ===")
print(f"Current Year ({current_year}) DataFrame shape: {df_current_year.shape}")
print(f"10-Year Median DataFrame shape: {df_10yr_median.shape}")
print(f"2019 DataFrame shape: {df_2019.shape}")

# Create standard pandas DataFrame with MultiIndex columns
# Add suffixes to distinguish between time periods
df_current_renamed = df_current_year.add_suffix(f'_{current_year}')
df_median_renamed = df_10yr_median.add_suffix('_10yr_Median')
df_2019_renamed = df_2019.add_suffix('_2019')

# Combine all dataframes horizontally
dff = pd.concat([df_current_renamed, df_median_renamed, df_2019_renamed], axis=1)

# Create MultiIndex columns: (Indicator, Time_Period)
# Extract the base indicator names and time periods
columns_tuples = []
for col in dff.columns:
    if col.endswith(f'_{current_year}'):
        indicator = col.replace(f'_{current_year}', '')
        columns_tuples.append((indicator, str(current_year)))
    elif col.endswith('_10yr_Median'):
        indicator = col.replace('_10yr_Median', '')
        columns_tuples.append((indicator, '10yr_Median'))
    elif col.endswith('_2019'):
        indicator = col.replace('_2019', '')
        columns_tuples.append((indicator, '2019'))

# Create MultiIndex
multi_index = pd.MultiIndex.from_tuples(columns_tuples, names=['Indicator', 'Time_Period'])
dff.columns = multi_index

# Sort columns to group indicators together
dff = dff.sort_index(axis=1)

print(f"\nMerged DataFrame created with shape: {dff.shape}")

# Define get_country_df function
def get_country_df(country_code, round_digits=1, sort_order=None):
    dfz = dff.loc[country_code].unstack().round(round_digits)[['2025', '2019','10yr_Median',]]
    
    if sort_order is not None:
        available_indicators = dfz.index.tolist()
        ordered_indicators = [ind for ind in sort_order if ind in available_indicators]
        remaining_indicators = [ind for ind in available_indicators if ind not in sort_order]
        final_order = ordered_indicators + remaining_indicators
        dfz = dfz.reindex(final_order)
    return(dfz)

logical_order = [
    'GDP (US Dollars)',
    'Population',
    'Real GDP growth (%)',
    'Inflation, consumer prices (%)',
    'National savings (% of GDP)',
    'Total investment (% of GDP)',
    'Current account balance (% of GDP)',
    'General government revenue (% of GDP)',
    'General government total expenditure (% of GDP)',
    'General government net lending/borrowing (% of GDP)',
    'General government net borrowing (% of GDP)',
    'General government gross debt (% of GDP)'
]

# Create country_dfs dictionary
all_countries = dff.index.tolist()
print(f"\nProcessing {len(all_countries)} countries...")

country_dfs = {}
for country_code in all_countries:
    try:
        country_dfs[country_code] = get_country_df(country_code, sort_order=logical_order)
        print(f"✓ {country_code}")
    except Exception as e:
        print(f"✗ Error with {country_code}: {e}")

print(f"\nSuccessfully created {len(country_dfs)} country dataframes")

# Convert country_dfs to JSON format
country_metrics_json = {}

for country_code, df in country_dfs.items():
    country_metrics_json[country_code] = {}
    
    for indicator in df.index:
        country_metrics_json[country_code][indicator] = {
            '2025': float(df.loc[indicator, '2025']) if pd.notna(df.loc[indicator, '2025']) else None,
            '2019': float(df.loc[indicator, '2019']) if pd.notna(df.loc[indicator, '2019']) else None,
            '10yr_Median': float(df.loc[indicator, '10yr_Median']) if pd.notna(df.loc[indicator, '10yr_Median']) else None
        }

print(f"\n✓ Converted {len(country_metrics_json)} countries to JSON format")

# Generate the HTML file with embedded data
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emerging Markets Dashboard</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState } = React;
        
        // Embedded country data
        const countryMetrics = COUNTRY_DATA_PLACEHOLDER;
        
        // Country organization by continent
        const countryData = {
          'Africa': {
            'AGO': 'Angola',
            'CIV': 'Côte d\\'Ivoire',
            'EGY': 'Egypt',
            'GHA': 'Ghana',
            'KEN': 'Kenya',
            'MAR': 'Morocco',
            'NGA': 'Nigeria',
            'ZAF': 'South Africa'
          },
          'Americas': {
            'ARG': 'Argentina',
            'BRA': 'Brazil',
            'CHL': 'Chile',
            'COL': 'Colombia',
            'CRI': 'Costa Rica',
            'DOM': 'Dominican Republic',
            'ECU': 'Ecuador',
            'GTM': 'Guatemala',
            'JAM': 'Jamaica',
            'MEX': 'Mexico',
            'PAN': 'Panama',
            'PER': 'Peru',
            'URY': 'Uruguay'
          },
          'Asia': {
            'BHR': 'Bahrain',
            'CHN': 'China',
            'JOR': 'Jordan',
            'KAZ': 'Kazakhstan',
            'MYS': 'Malaysia',
            'OMN': 'Oman',
            'PAK': 'Pakistan',
            'PHL': 'Philippines',
            'SAU': 'Saudi Arabia',
            'LKA': 'Sri Lanka',
            'ARE': 'United Arab Emirates'
          },
          'Europe': {
            'BGR': 'Bulgaria',
            'HUN': 'Hungary',
            'LVA': 'Latvia',
            'POL': 'Poland',
            'ROU': 'Romania',
            'SRB': 'Serbia',
            'TUR': 'Turkey',
            'UKR': 'Ukraine'
          }
        };

        const TrendingUp = () => (
            <svg className="inline w-4 h-4 text-green-600 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
        );

        const TrendingDown = () => (
            <svg className="inline w-4 h-4 text-red-600 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
        );

        const Globe = ({ className }) => (
            <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        );

        const CountryCard = ({ countryCode, countryName, metrics }) => {
          if (!metrics) {
            return (
              <div className="bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
                <div className="text-center text-gray-500">
                  <p>Data not available for {countryName} ({countryCode})</p>
                </div>
              </div>
            );
          }

          const getChangeIndicator = (current, previous) => {
            if (!current || !previous) return null;
            const change = current - previous;
            if (Math.abs(change) < 0.1) return null;
            return change > 0 ? <TrendingUp /> : <TrendingDown />;
          };

          const MetricRow = ({ label, data }) => (
            <div className="grid grid-cols-4 gap-4 py-3 border-b border-gray-100 hover:bg-gray-50">
              <div className="col-span-1 font-medium text-gray-700 text-sm">{label}</div>
              <div className="text-right font-semibold text-blue-900">
                {data['2025']?.toFixed(1) ?? 'N/A'}
                {getChangeIndicator(data['2025'], data['2019'])}
              </div>
              <div className="text-right text-gray-600">{data['10yr_Median']?.toFixed(1) ?? 'N/A'}</div>
              <div className="text-right text-gray-600">{data['2019']?.toFixed(1) ?? 'N/A'}</div>
            </div>
          );

          return (
            <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
              <div className="mb-6 pb-4 border-b-2 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-800">{countryName}</h2>
                    <p className="text-gray-600 text-lg">{countryCode}</p>
                  </div>
                  <Globe className="w-16 h-16 text-blue-600" />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4 mb-2 pb-2 border-b-2 border-gray-300">
                <div className="col-span-1 font-bold text-gray-700">Indicator</div>
                <div className="text-right font-bold text-blue-900">2025</div>
                <div className="text-right font-bold text-gray-700">10yr Median</div>
                <div className="text-right font-bold text-gray-700">2019</div>
              </div>

              <div className="space-y-0">
                {Object.entries(metrics).map(([key, value]) => (
                  <MetricRow key={key} label={key} data={value} />
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
                Source: IMF World Economic Outlook Database
              </div>
            </div>
          );
        };

        const App = () => {
          const [selectedCountry, setSelectedCountry] = useState(null);
          const [selectedContinent, setSelectedContinent] = useState('All');

          const handleCountryClick = (code, name) => {
            setSelectedCountry({ code, name });
          };

          const handleBack = () => {
            setSelectedCountry(null);
          };

          const continents = ['All', ...Object.keys(countryData)];

          const getFilteredCountries = () => {
            if (selectedContinent === 'All') {
              return Object.entries(countryData).flatMap(([continent, countries]) =>
                Object.entries(countries).map(([code, name]) => ({ code, name, continent }))
              );
            }
            return Object.entries(countryData[selectedContinent] || {}).map(([code, name]) => ({
              code,
              name,
              continent: selectedContinent
            }));
          };

          if (selectedCountry) {
            return (
              <div className="min-h-screen bg-gradient-to-br from-gray-100 to-blue-50 p-8">
                <button
                  onClick={handleBack}
                  className="mb-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  ← Back to Countries
                </button>
                <CountryCard
                  countryCode={selectedCountry.code}
                  countryName={selectedCountry.name}
                  metrics={countryMetrics[selectedCountry.code]}
                />
              </div>
            );
          }

          return (
            <div className="min-h-screen bg-gradient-to-br from-gray-100 to-blue-50 p-8">
              <div className="max-w-7xl mx-auto">
                <div className="text-center mb-8">
                  <h1 className="text-4xl font-bold text-gray-800 mb-2">Emerging Markets Dashboard</h1>
                  <p className="text-gray-600">Select a country to view economic indicators</p>
                </div>

                <div className="flex justify-center gap-2 mb-8 flex-wrap">
                  {continents.map(continent => (
                    <button
                      key={continent}
                      onClick={() => setSelectedContinent(continent)}
                      className={`px-4 py-2 rounded-lg font-medium transition ${
                        selectedContinent === continent
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-blue-100'
                      }`}
                    >
                      {continent}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {getFilteredCountries().map(({ code, name, continent }) => (
                    <button
                      key={code}
                      onClick={() => handleCountryClick(code, name)}
                      className="bg-white rounded-lg shadow hover:shadow-xl transition p-6 text-left group"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-bold text-lg text-gray-800 group-hover:text-blue-600 transition">
                            {name}
                          </h3>
                          <p className="text-sm text-gray-500">{code}</p>
                        </div>
                        <Globe className="w-6 h-6 text-blue-400" />
                      </div>
                      <p className="text-xs text-gray-400 mt-2">{continent}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        };

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>"""

# Replace placeholder with actual data
html_content = html_template.replace('COUNTRY_DATA_PLACEHOLDER', json.dumps(country_metrics_json, indent=2))

# Save HTML file to script directory
output_filename = os.path.join(SCRIPT_DIR, 'index.html')
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ HTML dashboard created: {output_filename}")
print(f"✓ Full path: {os.path.abspath(output_filename)}")
print(f"✓ Total countries included: {len(country_metrics_json)}")
print("\nYou can now open 'index.html' in your web browser!")
print("\n=== DONE ===")
