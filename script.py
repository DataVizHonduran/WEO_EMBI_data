import pandas as pd
import requests
from io import StringIO
import weo
from datetime import datetime
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Comprehensive Trading Economics country name → ISO3 mapping for all S&P-rated sovereigns
COUNTRY_NAME_TO_ISO = {
    # Africa
    'Angola': 'AGO', 'Benin': 'BEN', 'Botswana': 'BWA', 'Burkina Faso': 'BFA',
    'Cameroon': 'CMR', 'Cape Verde': 'CPV', "Cote D'Ivoire": 'CIV', 'Egypt': 'EGY',
    'Ethiopia': 'ETH', 'Gabon': 'GAB', 'Ghana': 'GHA', 'Kenya': 'KEN',
    'Lesotho': 'LSO', 'Malawi': 'MWI', 'Mali': 'MLI', 'Morocco': 'MAR',
    'Mozambique': 'MOZ', 'Namibia': 'NAM', 'Niger': 'NER', 'Nigeria': 'NGA',
    'Rwanda': 'RWA', 'Senegal': 'SEN', 'South Africa': 'ZAF', 'Tanzania': 'TZA',
    'Togo': 'TGO', 'Tunisia': 'TUN', 'Uganda': 'UGA', 'Zambia': 'ZMB',

    # Americas
    'Argentina': 'ARG', 'Belize': 'BLZ', 'Bolivia': 'BOL', 'Brazil': 'BRA',
    'Canada': 'CAN', 'Chile': 'CHL', 'Colombia': 'COL', 'Costa Rica': 'CRI',
    'Dominican Republic': 'DOM', 'Ecuador': 'ECU', 'El Salvador': 'SLV',
    'Guatemala': 'GTM', 'Honduras': 'HND', 'Jamaica': 'JAM', 'Mexico': 'MEX',
    'Nicaragua': 'NIC', 'Panama': 'PAN', 'Paraguay': 'PRY', 'Peru': 'PER',
    'Suriname': 'SUR', 'Trinidad and Tobago': 'TTO', 'United States': 'USA',
    'Uruguay': 'URY', 'Venezuela': 'VEN',

    # Asia-Pacific
    'Australia': 'AUS', 'Bangladesh': 'BGD', 'China': 'CHN', 'Cook Islands': 'COK',
    'Fiji': 'FJI', 'Hong Kong': 'HKG', 'India': 'IND', 'Indonesia': 'IDN',
    'Japan': 'JPN', 'Kazakhstan': 'KAZ', 'Malaysia': 'MYS', 'Mongolia': 'MNG',
    'New Zealand': 'NZL', 'Pakistan': 'PAK', 'Papua New Guinea': 'PNG',
    'Philippines': 'PHL', 'Singapore': 'SGP', 'South Korea': 'KOR',
    'Sri Lanka': 'LKA', 'Taiwan': 'TWN', 'Thailand': 'THA', 'Vietnam': 'VNM',

    # Europe
    'Albania': 'ALB', 'Armenia': 'ARM', 'Austria': 'AUT', 'Azerbaijan': 'AZE',
    'Belarus': 'BLR', 'Belgium': 'BEL', 'Bosnia and Herzegovina': 'BIH',
    'Bulgaria': 'BGR', 'Croatia': 'HRV', 'Cyprus': 'CYP', 'Czech Republic': 'CZE',
    'Denmark': 'DNK', 'Estonia': 'EST', 'Finland': 'FIN', 'France': 'FRA',
    'Georgia': 'GEO', 'Germany': 'DEU', 'Greece': 'GRC', 'Hungary': 'HUN',
    'Iceland': 'ISL', 'Ireland': 'IRL', 'Italy': 'ITA', 'Kosovo': 'XKX',
    'Latvia': 'LVA', 'Lithuania': 'LTU', 'Luxembourg': 'LUX', 'Malta': 'MLT',
    'Moldova': 'MDA', 'Montenegro': 'MNE', 'Netherlands': 'NLD', 'North Macedonia': 'MKD',
    'Norway': 'NOR', 'Poland': 'POL', 'Portugal': 'PRT', 'Romania': 'ROU',
    'Russia': 'RUS', 'Serbia': 'SRB', 'Slovakia': 'SVK', 'Slovenia': 'SVN',
    'Spain': 'ESP', 'Sweden': 'SWE', 'Switzerland': 'CHE', 'Turkey': 'TUR',
    'Ukraine': 'UKR', 'United Kingdom': 'GBR',

    # Middle East
    'Bahrain': 'BHR', 'Israel': 'ISR', 'Jordan': 'JOR', 'Kuwait': 'KWT',
    'Lebanon': 'LBN', 'Oman': 'OMN', 'Qatar': 'QAT', 'Saudi Arabia': 'SAU',
    'United Arab Emirates': 'ARE',
}

# ISO3 → region for the JS UI
ISO_TO_REGION = {
    # Africa
    'AGO': 'Africa', 'BEN': 'Africa', 'BWA': 'Africa', 'BFA': 'Africa',
    'CMR': 'Africa', 'CPV': 'Africa', 'CIV': 'Africa', 'EGY': 'Africa',
    'ETH': 'Africa', 'GAB': 'Africa', 'GHA': 'Africa', 'KEN': 'Africa',
    'LSO': 'Africa', 'MWI': 'Africa', 'MLI': 'Africa', 'MAR': 'Africa',
    'MOZ': 'Africa', 'NAM': 'Africa', 'NER': 'Africa', 'NGA': 'Africa',
    'RWA': 'Africa', 'SEN': 'Africa', 'ZAF': 'Africa', 'TZA': 'Africa',
    'TGO': 'Africa', 'TUN': 'Africa', 'UGA': 'Africa', 'ZMB': 'Africa',
    # Americas
    'ARG': 'Americas', 'BLZ': 'Americas', 'BOL': 'Americas', 'BRA': 'Americas',
    'CAN': 'Americas', 'CHL': 'Americas', 'COL': 'Americas', 'CRI': 'Americas',
    'DOM': 'Americas', 'ECU': 'Americas', 'SLV': 'Americas', 'GTM': 'Americas',
    'HND': 'Americas', 'JAM': 'Americas', 'MEX': 'Americas', 'NIC': 'Americas',
    'PAN': 'Americas', 'PRY': 'Americas', 'PER': 'Americas', 'SUR': 'Americas',
    'TTO': 'Americas', 'USA': 'Americas', 'URY': 'Americas', 'VEN': 'Americas',
    # Asia-Pacific
    'AUS': 'Asia-Pacific', 'BGD': 'Asia-Pacific', 'CHN': 'Asia-Pacific',
    'COK': 'Asia-Pacific', 'FJI': 'Asia-Pacific', 'HKG': 'Asia-Pacific',
    'IND': 'Asia-Pacific', 'IDN': 'Asia-Pacific', 'JPN': 'Asia-Pacific',
    'KAZ': 'Asia-Pacific', 'MYS': 'Asia-Pacific', 'MNG': 'Asia-Pacific',
    'NZL': 'Asia-Pacific', 'PAK': 'Asia-Pacific', 'PNG': 'Asia-Pacific',
    'PHL': 'Asia-Pacific', 'SGP': 'Asia-Pacific', 'KOR': 'Asia-Pacific',
    'LKA': 'Asia-Pacific', 'TWN': 'Asia-Pacific', 'THA': 'Asia-Pacific',
    'VNM': 'Asia-Pacific',
    # Europe
    'ALB': 'Europe', 'ARM': 'Europe', 'AUT': 'Europe', 'AZE': 'Europe',
    'BLR': 'Europe', 'BEL': 'Europe', 'BIH': 'Europe', 'BGR': 'Europe',
    'HRV': 'Europe', 'CYP': 'Europe', 'CZE': 'Europe', 'DNK': 'Europe',
    'EST': 'Europe', 'FIN': 'Europe', 'FRA': 'Europe', 'GEO': 'Europe',
    'DEU': 'Europe', 'GRC': 'Europe', 'HUN': 'Europe', 'ISL': 'Europe',
    'IRL': 'Europe', 'ITA': 'Europe', 'XKX': 'Europe', 'LVA': 'Europe',
    'LTU': 'Europe', 'LUX': 'Europe', 'MLT': 'Europe', 'MDA': 'Europe',
    'MNE': 'Europe', 'NLD': 'Europe', 'MKD': 'Europe', 'NOR': 'Europe',
    'POL': 'Europe', 'PRT': 'Europe', 'ROU': 'Europe', 'RUS': 'Europe',
    'SRB': 'Europe', 'SVK': 'Europe', 'SVN': 'Europe', 'ESP': 'Europe',
    'SWE': 'Europe', 'CHE': 'Europe', 'TUR': 'Europe', 'UKR': 'Europe',
    'GBR': 'Europe',
    # Middle East
    'BHR': 'Middle East', 'ISR': 'Middle East', 'JOR': 'Middle East',
    'KWT': 'Middle East', 'LBN': 'Middle East', 'OMN': 'Middle East',
    'QAT': 'Middle East', 'SAU': 'Middle East', 'ARE': 'Middle East',
}

# ISO3 → display name
ISO_TO_NAME = {v: k for k, v in COUNTRY_NAME_TO_ISO.items()}
# Overrides for better display names
ISO_TO_NAME.update({
    'CIV': 'Côte d\'Ivoire', 'KOR': 'South Korea', 'GBR': 'United Kingdom',
    'USA': 'United States', 'ARE': 'UAE', 'TTO': 'Trinidad & Tobago',
    'BIH': 'Bosnia & Herzegovina',
})

RATINGS_NUMERIC = {
    'AAA': 1, 'AA+': 2, 'AA': 3, 'AA-': 4,
    'A+': 5, 'A': 6, 'A-': 7,
    'BBB+': 8, 'BBB': 9, 'BBB-': 10,
    'BB+': 11, 'BB': 12, 'BB-': 13,
    'B+': 14, 'B': 15, 'B-': 16,
    'CCC+': 17, 'CCC': 18, 'CCC-': 19,
    'SD': 20, 'WD': 21, 'RD': 22, 'D': 23,
}


def rating_to_bucket(rating_str):
    n = RATINGS_NUMERIC.get(rating_str, 99)
    if n <= 7:  return 'A & Above'
    if n <= 10: return 'BBB'
    if n <= 13: return 'BB'
    if n <= 16: return 'B'
    return 'CCC & Below'


def fetch_ratings():
    """Scrape S&P sovereign ratings from Trading Economics; returns {iso: rating_str}."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(
            'https://tradingeconomics.com/country-list/rating',
            headers=headers, timeout=20
        )
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))
        df_r = tables[0]
        country_col = df_r.columns[0]
        rating_col = next(
            (c for c in df_r.columns if 'S&P' in str(c) or 'Rating' in str(c)),
            df_r.columns[1]
        )
        result = {}
        for _, row in df_r.iterrows():
            iso = COUNTRY_NAME_TO_ISO.get(str(row[country_col]).strip())
            if iso:
                result[iso] = str(row[rating_col]).strip()
        print(f"✓ Ratings fetched for {len(result)} countries")
        return result
    except Exception as e:
        print(f"⚠ Could not fetch ratings: {e}")
        return {}

current_year = datetime.now().year
current_month = datetime.now().month


def generate_download_attempts(year, month):
    """Build ordered list of WEO (year, release) to try, newest first."""
    if month >= 10:
        start_year, start_release = year, 2
    elif month >= 4:
        start_year, start_release = year, 1
    else:
        start_year, start_release = year - 1, 2

    attempts = []
    y, r = start_year, start_release
    for _ in range(6):
        attempts.append((y, r))
        if r == 2:
            r = 1
        else:
            r = 2
            y -= 1
    return attempts


download_attempts = generate_download_attempts(current_year, current_month)

weo_downloaded = False
weo_release_label = None
weo_filepath = os.path.join(SCRIPT_DIR, 'weo.csv')

for weo_year, weo_release in download_attempts:
    try:
        print(f"Attempting to download WEO data: {weo_year} Release {weo_release}")
        weo.download(year=weo_year, release=weo_release, filename=weo_filepath)

        with open(weo_filepath, 'rb') as f:
            header = f.read(512).decode('utf-8', errors='replace')
            if any(tag in header.lower() for tag in ['<html>', '<head>', 'blobnotfound', '<error>']):
                print(f"  ✗ Downloaded file is an error page, not CSV")
                continue

        print(f"  ✓ Successfully downloaded {weo_year} Release {weo_release}")
        weo_release_label = f"{'April' if weo_release == 1 else 'October'} {weo_year}"
        weo_downloaded = True
        break
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        continue

if not weo_downloaded:
    raise RuntimeError("Could not download WEO data from any available release.")

print("\nAttempting to load WEO data...")
try:
    w = weo.WEO(weo_filepath)
    print("✓ WEO data loaded successfully using weo library")
except KeyError as e:
    print(f"⚠ WEO library encountered column issue: {e}")
    df_weo = pd.read_csv(weo_filepath, sep='\t')

    class CustomWEO:
        def __init__(self, df):
            self.df = df
            self.country_col = next(
                (col for col in ['ISO', 'WEO Country Code', 'Country Code', 'ISO3'] if col in df.columns),
                None
            )
            if not self.country_col:
                raise ValueError(f"Could not identify country code column. Available: {df.columns.tolist()}")
            print(f"Using '{self.country_col}' as country identifier")

        def getc(self, variable_code):
            var_data = self.df[self.df['WEO Subject Code'] == variable_code].copy()
            if var_data.empty:
                raise ValueError(f"Variable {variable_code} not found")
            year_cols = [col for col in var_data.columns if str(col).isdigit()]
            var_data = var_data.set_index(self.country_col)
            result = var_data[year_cols].apply(pd.to_numeric, errors='coerce')
            result.columns = result.columns.astype(int)
            return result.T

    w = CustomWEO(df_weo)
    print("✓ Created custom WEO wrapper")

# Fetch ratings first to determine country universe
country_ratings = fetch_ratings()
rated_isos = set(country_ratings.keys())

# Get all WEO country codes from a core variable, then intersect with rated countries
print("\nDetermining WEO country universe...")
try:
    gdp_series = w.getc('NGDPD')
    weo_isos = set(gdp_series.columns.tolist())
    target_countries = sorted(weo_isos & rated_isos)
    print(f"✓ WEO countries: {len(weo_isos)}, Rated: {len(rated_isos)}, Intersection: {len(target_countries)}")
except Exception as e:
    print(f"⚠ Could not determine WEO universe ({e}), falling back to rated ISOs only")
    target_countries = sorted(rated_isos)

var_dict = {
    'NGDPD': 'GDP (US Dollars)',
    'LP': 'Population',
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

current_year_data = {}
median_10yr_data = {}
data_2019 = {}
current_year_str = str(current_year)


def extract_year_from_index(idx):
    try:
        return idx.year if hasattr(idx, 'year') else int(idx)
    except:
        return str(idx)


def get_year_data(series_data, target_year):
    index_years = [extract_year_from_index(idx) for idx in series_data.index]
    if target_year in index_years:
        return series_data.iloc[index_years.index(target_year)].sort_values(), target_year
    numeric_years = [y for y in index_years if isinstance(y, int)]
    if numeric_years:
        closest = min(numeric_years, key=lambda x: abs(x - target_year))
        return series_data.iloc[index_years.index(closest)].sort_values(), closest
    return series_data.iloc[-1].sort_values(), "last_available"


print("\nCollecting data for variables...")
for var in var_dict.keys():
    try:
        # Only keep columns that are in our target list
        all_series = w.getc(var)
        available = [c for c in target_countries if c in all_series.columns]
        series_data = all_series[available]

        current_values, used_year = get_year_data(series_data, current_year)
        current_year_data[var] = current_values

        median_10yr = series_data.loc[pd.Period(current_year - 9, freq='A'):pd.Period(current_year, freq='A')].median().sort_values()
        median_10yr_data[var] = median_10yr

        try:
            values_2019, _ = get_year_data(series_data, 2019)
            data_2019[var] = values_2019
        except Exception as e:
            data_2019[var] = pd.Series([float('nan')] * len(available), index=available).sort_values()

        print(f"✓ {var} ({len(available)} countries)")
    except Exception as e:
        print(f"✗ {var}: {e}")
        current_year_data[var] = None
        median_10yr_data[var] = None
        data_2019[var] = None

clean_current = {k: v for k, v in current_year_data.items() if v is not None}
clean_median = {k: v for k, v in median_10yr_data.items() if v is not None}
clean_2019 = {k: v for k, v in data_2019.items() if v is not None}

df_current_year = pd.DataFrame(clean_current).rename(columns=var_dict)
df_10yr_median = pd.DataFrame(clean_median).rename(columns=var_dict)
df_2019 = pd.DataFrame(clean_2019).rename(columns=var_dict)

df_current_renamed = df_current_year.add_suffix(f'_{current_year_str}')
df_median_renamed = df_10yr_median.add_suffix('_10yr_Median')
df_2019_renamed = df_2019.add_suffix('_2019')

dff = pd.concat([df_current_renamed, df_median_renamed, df_2019_renamed], axis=1)

columns_tuples = []
for col in dff.columns:
    if col.endswith(f'_{current_year_str}'):
        columns_tuples.append((col.replace(f'_{current_year_str}', ''), current_year_str))
    elif col.endswith('_10yr_Median'):
        columns_tuples.append((col.replace('_10yr_Median', ''), '10yr_Median'))
    elif col.endswith('_2019'):
        columns_tuples.append((col.replace('_2019', ''), '2019'))

dff.columns = pd.MultiIndex.from_tuples(columns_tuples, names=['Indicator', 'Time_Period'])
dff = dff.sort_index(axis=1)

logical_order = [
    'GDP (US Dollars)', 'Population', 'Real GDP growth (%)',
    'Inflation, consumer prices (%)', 'National savings (% of GDP)',
    'Total investment (% of GDP)', 'Current account balance (% of GDP)',
    'General government revenue (% of GDP)', 'General government total expenditure (% of GDP)',
    'General government net lending/borrowing (% of GDP)',
    'General government net borrowing (% of GDP)', 'General government gross debt (% of GDP)'
]


def get_country_df(country_code, round_digits=1, sort_order=None):
    dfz = dff.loc[country_code].unstack().round(round_digits)[[current_year_str, '2019', '10yr_Median']]
    if sort_order:
        available = dfz.index.tolist()
        ordered = [i for i in sort_order if i in available]
        remaining = [i for i in available if i not in sort_order]
        dfz = dfz.reindex(ordered + remaining)
    return dfz


country_dfs = {}
for code in dff.index.tolist():
    try:
        country_dfs[code] = get_country_df(code, sort_order=logical_order)
    except Exception as e:
        print(f"✗ {code}: {e}")

country_metrics_json = {}
for country_code, df in country_dfs.items():
    country_metrics_json[country_code] = {}
    for indicator in df.index:
        country_metrics_json[country_code][indicator] = {
            current_year_str: float(df.loc[indicator, current_year_str]) if pd.notna(df.loc[indicator, current_year_str]) else None,
            '2019': float(df.loc[indicator, '2019']) if pd.notna(df.loc[indicator, '2019']) else None,
            '10yr_Median': float(df.loc[indicator, '10yr_Median']) if pd.notna(df.loc[indicator, '10yr_Median']) else None
        }

print(f"\n✓ {len(country_metrics_json)} countries converted to JSON")

# Build region-grouped country data for JS (only countries with WEO data)
region_order = ['Africa', 'Americas', 'Asia-Pacific', 'Europe', 'Middle East']
country_data_by_region = {r: {} for r in region_order}
for iso in sorted(country_metrics_json.keys()):
    region = ISO_TO_REGION.get(iso, 'Other')
    name = ISO_TO_NAME.get(iso, iso)
    if region not in country_data_by_region:
        country_data_by_region[region] = {}
    country_data_by_region[region][iso] = name

# Remove empty regions
country_data_by_region = {r: v for r, v in country_data_by_region.items() if v}

# Build rating groups
rating_groups_ordered = ['A & Above', 'BBB', 'BB', 'B', 'CCC & Below']
rating_groups = {k: [] for k in rating_groups_ordered}
for iso, rating in country_ratings.items():
    if iso in country_metrics_json:
        rating_groups[rating_to_bucket(rating)].append(iso)
rating_groups = {k: v for k, v in rating_groups.items() if v}

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign Dashboard</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useMemo } = React;

        const countryMetrics  = COUNTRY_DATA_PLACEHOLDER;
        const currentYear     = "CURRENT_YEAR_PLACEHOLDER";
        const weoReleaseLabel = "WEO_RELEASE_PLACEHOLDER";
        const ratingGroups    = RATING_GROUPS_PLACEHOLDER;
        const countryRatings  = COUNTRY_RATINGS_PLACEHOLDER;
        const countryData     = COUNTRY_DATA_BY_REGION_PLACEHOLDER;

        const allCountriesFlat = Object.entries(countryData).flatMap(([continent, countries]) =>
          Object.entries(countries).map(([code, name]) => ({ code, name, continent }))
        );

        const indicators = [
          'Real GDP growth (%)',
          'Inflation, consumer prices (%)',
          'General government gross debt (% of GDP)',
          'General government net lending/borrowing (% of GDP)',
          'Current account balance (% of GDP)',
          'GDP (US Dollars)',
          'Population',
          'Total investment (% of GDP)',
          'National savings (% of GDP)',
          'General government revenue (% of GDP)',
          'General government total expenditure (% of GDP)',
          'General government net borrowing (% of GDP)',
        ];

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

        // ── Country detail card ─────────────────────────────────────────────
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

          const peerBucket = Object.entries(ratingGroups).find(([, codes]) => codes.includes(countryCode))?.[0] ?? null;
          const peerCodes  = peerBucket ? ratingGroups[peerBucket] : [];

          const peerAverages = useMemo(() => {
            const avgs = {};
            for (const indicator of Object.keys(metrics)) {
              const vals = peerCodes
                .map(c => countryMetrics[c]?.[indicator]?.[currentYear] ?? null)
                .filter(v => v !== null);
              avgs[indicator] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
            }
            return avgs;
          }, [peerCodes]);

          const getChangeIndicator = (current, previous) => {
            if (current == null || previous == null) return null;
            const change = current - previous;
            if (Math.abs(change) < 0.1) return null;
            return change > 0 ? <TrendingUp /> : <TrendingDown />;
          };

          const MetricRow = ({ label, data, peerAvg }) => (
            <div className="grid grid-cols-5 gap-4 py-3 border-b border-gray-100 hover:bg-gray-50">
              <div className="col-span-1 font-medium text-gray-700 text-sm">{label}</div>
              <div className="text-right font-semibold text-blue-900">
                {data[currentYear]?.toFixed(1) ?? 'N/A'}
                {getChangeIndicator(data[currentYear], data['2019'])}
              </div>
              <div className="text-right text-gray-600">{data['10yr_Median']?.toFixed(1) ?? 'N/A'}</div>
              <div className="text-right text-gray-600">{data['2019']?.toFixed(1) ?? 'N/A'}</div>
              <div className="text-right text-purple-600 font-medium">{peerAvg != null ? peerAvg.toFixed(1) : 'N/A'}</div>
            </div>
          );

          return (
            <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
              <div className="mb-6 pb-4 border-b-2 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-800">{countryName}</h2>
                    <p className="text-gray-600 text-lg">
                      {countryCode}
                      {countryRatings[countryCode] && (
                        <span className="ml-3 px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-sm font-semibold">
                          S&P {countryRatings[countryCode]}
                        </span>
                      )}
                      {peerBucket && (
                        <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-sm">
                          {peerBucket} peer avg · n={peerCodes.length}
                        </span>
                      )}
                    </p>
                  </div>
                  <Globe className="w-16 h-16 text-blue-600" />
                </div>
              </div>
              <div className="grid grid-cols-5 gap-4 mb-2 pb-2 border-b-2 border-gray-300">
                <div className="col-span-1 font-bold text-gray-700">Indicator</div>
                <div className="text-right font-bold text-blue-900">{currentYear}</div>
                <div className="text-right font-bold text-gray-700">10yr Median</div>
                <div className="text-right font-bold text-gray-700">2019</div>
                <div className="text-right font-bold text-purple-700">Peer Avg</div>
              </div>
              <div className="space-y-0">
                {Object.entries(metrics).map(([key, value]) => (
                  <MetricRow key={key} label={key} data={value} peerAvg={peerAverages[key] ?? null} />
                ))}
              </div>
              <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
                Source: IMF World Economic Outlook Database · {weoReleaseLabel} WEO
              </div>
            </div>
          );
        };

        // ── Compare tab ─────────────────────────────────────────────────────
        const CompareView = () => {
          const [indicator,       setIndicator]       = useState(indicators[0]);
          const [period,          setPeriod]          = useState(currentYear);
          const [filterMode,      setFilterMode]      = useState('region');
          const [continentFilter, setContinentFilter] = useState('All');
          const [ratingFilter,    setRatingFilter]    = useState('All');
          const [showRatingAvg,   setShowRatingAvg]   = useState(false);

          const periods   = [
            { key: currentYear,   label: currentYear },
            { key: '10yr_Median', label: '10yr Median' },
            { key: '2019',        label: '2019' },
          ];
          const continents    = ['All', ...Object.keys(countryData)];
          const ratingBuckets = ['All', ...Object.keys(ratingGroups)];

          const rows = useMemo(() => {
            let source = allCountriesFlat;
            if (filterMode === 'region' && continentFilter !== 'All')
              source = source.filter(c => c.continent === continentFilter);
            if (filterMode === 'rating' && ratingFilter !== 'All')
              source = source.filter(c => (ratingGroups[ratingFilter] || []).includes(c.code));

            return source
              .map(c => ({
                ...c,
                value:  countryMetrics[c.code]?.[indicator]?.[period]          ?? null,
                median: countryMetrics[c.code]?.[indicator]?.['10yr_Median']   ?? null,
                rating: countryRatings[c.code] ?? '',
              }))
              .filter(c => c.value !== null)
              .sort((a, b) => b.value - a.value);
          }, [indicator, period, filterMode, continentFilter, ratingFilter]);

          const ratingAverages = useMemo(() => {
            if (!showRatingAvg) return [];
            return Object.entries(ratingGroups).map(([bucket, codes]) => {
              const vals = codes
                .map(c => countryMetrics[c]?.[indicator]?.[period] ?? null)
                .filter(v => v !== null);
              if (vals.length === 0) return null;
              const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
              return { bucket, avg, count: vals.length };
            }).filter(Boolean);
          }, [showRatingAvg, indicator, period]);

          const maxAbs = useMemo(() => {
            const allVals = [
              ...rows.map(r => Math.abs(r.value)),
              ...(showRatingAvg ? ratingAverages.map(a => Math.abs(a.avg)) : []),
              1,
            ];
            return Math.max(...allVals);
          }, [rows, ratingAverages, showRatingAvg]);

          const hasNegative = rows.some(r => r.value < 0) ||
            (showRatingAvg && ratingAverages.some(a => a.avg < 0));
          const showMedian  = period === currentYear;

          const valToPct = (v) => Math.min(Math.abs(v) / maxAbs * 100, 100);

          return (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-xl shadow p-5 mb-6 flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Indicator</label>
                  <select
                    value={indicator}
                    onChange={e => setIndicator(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {indicators.map(ind => (
                      <option key={ind} value={ind}>{ind}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-wrap gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Period</label>
                    <div className="flex gap-2">
                      {periods.map(p => (
                        <button key={p.key} onClick={() => setPeriod(p.key)}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                            period === p.key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
                          }`}>
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Group by</label>
                    <div className="flex gap-2">
                      {[['region','Region'],['rating','Credit Rating']].map(([m, label]) => (
                        <button key={m} onClick={() => setFilterMode(m)}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                            filterMode === m ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-indigo-50'
                          }`}>
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 items-end">
                  <div className="flex-1 min-w-0">
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                      {filterMode === 'region' ? 'Region' : 'Rating Tier'}
                    </label>
                    <div className="flex gap-2 flex-wrap">
                      {(filterMode === 'region' ? continents : ratingBuckets).map(opt => (
                        <button key={opt}
                          onClick={() => filterMode === 'region' ? setContinentFilter(opt) : setRatingFilter(opt)}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                            (filterMode === 'region' ? continentFilter : ratingFilter) === opt
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
                          }`}>
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Rating Averages</label>
                    <button
                      onClick={() => setShowRatingAvg(v => !v)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition border ${
                        showRatingAvg
                          ? 'bg-teal-600 text-white border-teal-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:bg-teal-50'
                      }`}>
                      {showRatingAvg ? '✓ Shown' : 'Show'}
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-xs text-gray-400">
                    {rows.length} countries · sorted by value · {period === currentYear ? currentYear : period}
                  </p>
                  {showMedian && (
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                      <span className="inline-block w-4 border-t-2 border-dashed border-orange-400" />
                      10yr median
                    </p>
                  )}
                </div>

                {rows.length === 0 && (
                  <p className="text-center text-gray-400 py-8">No data available for this selection.</p>
                )}

                <div className="space-y-1.5">
                  {rows.map(({ code, name, value, median, rating }) => {
                    const absPct   = valToPct(value);
                    const positive = value >= 0;
                    const medPct   = (showMedian && median != null) ? valToPct(median) : null;
                    const medPositive = median >= 0;

                    if (hasNegative) {
                      return (
                        <div key={code} className="flex items-center gap-2 group">
                          <div className="w-36 text-right text-xs text-gray-700 truncate group-hover:text-blue-700 font-medium" title={name}>
                            {name}
                            {rating && <span className="ml-1 text-gray-400 font-normal">({rating})</span>}
                          </div>
                          <div className="flex-1 flex items-center h-6 relative">
                            <div className="w-1/2 flex justify-end relative h-full">
                              {!positive && (
                                <div style={{ width: `${absPct}%` }} className="h-5 bg-red-400 rounded-l relative">
                                  {medPct != null && !medPositive && (
                                    <div style={{ right: `${medPct / absPct * 100}%` }}
                                      className="absolute top-0 bottom-0 w-0.5 border-r-2 border-dashed border-orange-400" />
                                  )}
                                </div>
                              )}
                            </div>
                            <div className="w-px h-5 bg-gray-400 mx-0.5 flex-shrink-0" />
                            <div className="w-1/2 flex justify-start relative h-full">
                              {positive && (
                                <div style={{ width: `${absPct}%` }} className="h-5 bg-blue-500 rounded-r relative">
                                  {medPct != null && medPositive && (
                                    <div style={{ left: `${medPct / absPct * 100}%` }}
                                      className="absolute top-0 bottom-0 w-0.5 border-l-2 border-dashed border-orange-400" />
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className={`w-14 text-xs font-semibold text-right ${positive ? 'text-blue-700' : 'text-red-600'}`}>
                            {value.toFixed(1)}
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div key={code} className="flex items-center gap-2 group">
                        <div className="w-36 text-right text-xs text-gray-700 truncate group-hover:text-blue-700 font-medium" title={name}>
                          {name}
                          {rating && <span className="ml-1 text-gray-400 font-normal">({rating})</span>}
                        </div>
                        <div className="flex-1 relative h-5">
                          <div style={{ width: `${absPct}%` }} className="h-5 bg-blue-500 rounded-r" />
                          {medPct != null && (
                            <div style={{ left: `${medPct}%` }}
                              className="absolute top-0 bottom-0 w-0.5 border-l-2 border-dashed border-orange-400" />
                          )}
                        </div>
                        <div className="w-14 text-xs font-semibold text-right text-blue-700">
                          {value.toFixed(1)}
                        </div>
                      </div>
                    );
                  })}

                  {showRatingAvg && ratingAverages.length > 0 && (
                    <>
                      <div className="border-t-2 border-gray-200 mt-3 mb-2" />
                      {ratingAverages.map(({ bucket, avg, count }) => {
                        const absPct  = valToPct(avg);
                        const positive = avg >= 0;
                        const bucketColor = {
                          'A & Above':   'bg-emerald-600',
                          'BBB':         'bg-emerald-400',
                          'BB':          'bg-amber-400',
                          'B':           'bg-orange-500',
                          'CCC & Below': 'bg-red-600',
                        }[bucket] || 'bg-gray-400';
                        const textColor = {
                          'A & Above':   'text-emerald-800',
                          'BBB':         'text-emerald-600',
                          'BB':          'text-amber-700',
                          'B':           'text-orange-700',
                          'CCC & Below': 'text-red-700',
                        }[bucket] || 'text-gray-700';

                        if (hasNegative) {
                          return (
                            <div key={bucket} className="flex items-center gap-2">
                              <div className={`w-36 text-right text-xs font-bold ${textColor}`}>
                                {bucket} avg
                                <span className="ml-1 font-normal text-gray-400">n={count}</span>
                              </div>
                              <div className="flex-1 flex items-center h-6">
                                <div className="w-1/2 flex justify-end">
                                  {!positive && (
                                    <div style={{ width: `${absPct}%` }} className={`h-5 ${bucketColor} opacity-80 rounded-l`} />
                                  )}
                                </div>
                                <div className="w-px h-5 bg-gray-400 mx-0.5 flex-shrink-0" />
                                <div className="w-1/2 flex justify-start">
                                  {positive && (
                                    <div style={{ width: `${absPct}%` }} className={`h-5 ${bucketColor} opacity-80 rounded-r`} />
                                  )}
                                </div>
                              </div>
                              <div className={`w-14 text-xs font-bold text-right ${textColor}`}>
                                {avg.toFixed(1)}
                              </div>
                            </div>
                          );
                        }

                        return (
                          <div key={bucket} className="flex items-center gap-2">
                            <div className={`w-36 text-right text-xs font-bold ${textColor}`}>
                              {bucket} avg
                              <span className="ml-1 font-normal text-gray-400">n={count}</span>
                            </div>
                            <div className="flex-1 relative h-5">
                              <div style={{ width: `${absPct}%` }} className={`h-5 ${bucketColor} opacity-80 rounded-r`} />
                            </div>
                            <div className={`w-14 text-xs font-bold text-right ${textColor}`}>
                              {avg.toFixed(1)}
                            </div>
                          </div>
                        );
                      })}
                    </>
                  )}
                </div>
                <div className="mt-6 pt-4 border-t border-gray-100 text-center text-xs text-gray-400">
                  Source: IMF World Economic Outlook Database · {weoReleaseLabel} WEO
                </div>
              </div>
            </div>
          );
        };

        // ── Root app ────────────────────────────────────────────────────────
        const App = () => {
          const [tab, setTab] = useState('countries');
          const [selectedCountry, setSelectedCountry] = useState(null);
          const [selectedContinent, setSelectedContinent] = useState('All');
          const [search, setSearch] = useState('');

          const handleCountryClick = (code, name) => setSelectedCountry({ code, name });
          const handleBack = () => setSelectedCountry(null);
          const continents = ['All', ...Object.keys(countryData)];

          const getFilteredCountries = () => {
            let list;
            if (selectedContinent === 'All') {
              list = Object.entries(countryData).flatMap(([continent, countries]) =>
                Object.entries(countries).map(([code, name]) => ({ code, name, continent }))
              );
            } else {
              list = Object.entries(countryData[selectedContinent] || {}).map(([code, name]) => ({
                code, name, continent: selectedContinent
              }));
            }
            if (search.trim()) {
              const q = search.trim().toLowerCase();
              list = list.filter(c => c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q));
            }
            return list;
          };

          if (selectedCountry) {
            return (
              <div className="min-h-screen bg-gradient-to-br from-gray-100 to-blue-50 p-8">
                <button onClick={handleBack} className="mb-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
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
                <div className="text-center mb-5">
                  <h1 className="text-4xl font-bold text-gray-800 mb-2">Sovereign Dashboard</h1>
                  <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
                    Data: IMF {weoReleaseLabel} WEO · S&P Ratings
                  </span>
                </div>

                <div className="flex justify-center gap-2 mb-6">
                  {[['countries', 'Countries'], ['compare', 'Compare']].map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => setTab(key)}
                      className={`px-6 py-2 rounded-full font-semibold text-sm transition ${
                        tab === key ? 'bg-blue-600 text-white shadow' : 'bg-white text-gray-600 hover:bg-blue-50'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {tab === 'compare' ? (
                  <CompareView />
                ) : (
                  <>
                    <div className="flex justify-center gap-2 mb-4 flex-wrap">
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
                    <div className="flex justify-center mb-6">
                      <input
                        type="text"
                        placeholder="Search country…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-64 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                      />
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
                              <h3 className="font-bold text-lg text-gray-800 group-hover:text-blue-600 transition">{name}</h3>
                              <p className="text-sm text-gray-500">{code}</p>
                            </div>
                            {countryRatings[code] && (
                              <span className="text-xs font-semibold px-2 py-1 rounded bg-blue-50 text-blue-700">
                                {countryRatings[code]}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-2">{continent}</p>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          );
        };

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>"""

html_content = (html_template
    .replace('COUNTRY_DATA_PLACEHOLDER',            json.dumps(country_metrics_json, indent=2))
    .replace('CURRENT_YEAR_PLACEHOLDER',            current_year_str)
    .replace('WEO_RELEASE_PLACEHOLDER',             weo_release_label)
    .replace('RATING_GROUPS_PLACEHOLDER',           json.dumps(rating_groups))
    .replace('COUNTRY_RATINGS_PLACEHOLDER',         json.dumps(country_ratings))
    .replace('COUNTRY_DATA_BY_REGION_PLACEHOLDER',  json.dumps(country_data_by_region)))

output_filename = os.path.join(SCRIPT_DIR, 'index.html')
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ HTML dashboard created: {output_filename}")
print(f"✓ WEO release: {weo_release_label}")
print(f"✓ Countries: {len(country_metrics_json)}")
print("\n=== DONE ===")
