# IoT Data Viewer for Broiler Chicken Environment

A Streamlit web app for visualizing, analyzing, and downloading IoT sensor data (Temperature, Humidity, Wind Speed) for broiler chicken environments. The app provides:
- Interactive filtering by sensor type
- Data visualization (tables, line charts, pie charts)
- Calculation and interpretation of Temperature Humidity Index (THI) and Wind Chill Index (WCI)
- Combined analysis and recommendations for broiler chicken comfort
- Download options for filtered and processed data (CSV/XLSX)

## Features
- **Upload CSV/XLSX**: Upload your IoT sensor data file.
- **Sensor Filtering**: Select which sensor types to display (Temperature, Humidity, Wind Speed).
- **Data Visualization**: View tables and time series charts for each sensor type.
- **THI Calculation**: Calculate and interpret THI for broiler chickens, with pie chart and summary.
- **Wind Chill Calculation**: Calculate and interpret Wind Chill Index, with pie chart and summary.
- **Combined Analysis**: See combined THI & Wind Chill interpretation, recommendations, and download results.
- **Download**: Download filtered or processed data as CSV or XLSX.

## Installation

1. Clone this repository or copy the files to your project folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run dataIoT.py
```

Open the provided local URL in your browser. Upload your CSV or XLSX file with columns including at least:
- `record_datetime` (datetime)
- `sensor_name` (string)
- `value_calibration` (float)
- `sensor_unit` (string)

## Data Format Example

| record_datetime      | sensor_name   | value_calibration | sensor_unit |
|---------------------|--------------|------------------|-------------|
| 2025-06-09 08:00:00 | temp_sensor1 | 29.5             | °C          |
| 2025-06-09 08:00:00 | hum_sensor1  | 75.0             | %           |
| 2025-06-09 08:00:00 | wind_sensor1 | 2.5              | m/s         |

## Notes
- The app automatically detects sensor types by keywords in `sensor_name`.
- THI and Wind Chill calculations are based on standard formulas for broiler chickens in Indonesia.
- Recommendations and interpretations are shown based on calculated indices.

## References
- Zulbardi, Z., et al. (2019). "Temperature Humidity Index (THI) dan Pengaruhnya terhadap Produksi dan Kesehatan Ayam Broiler." Jurnal Ilmu Ternak dan Veteriner, 24(2), 123-130.
- SNI 01-4869.3-2008. Tata Cara Perancangan Lingkungan dan Bangunan Kandang Ayam Pedaging (Broiler).

## License
MIT License
