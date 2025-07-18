import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import plotly.graph_objs as go

# Caching file reading for faster reloads
@st.cache_data(show_spinner=False)
def load_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

# Caching Excel/CSV generation for download
@st.cache_data(show_spinner=False)
def to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data(show_spinner=False)
def to_xlsx_bytes(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

def main():
    st.set_page_config(page_title="IoT Data Viewer", page_icon="📊")
    st.title('IoT Data Viewer')
    uploaded_file = st.file_uploader("Upload CSV/XLSX file", type=['csv', 'xlsx'])
    if uploaded_file is not None:
        try:
            df = load_file(uploaded_file)
            st.sidebar.header('Filter Sensor Types')
            show_temp = st.sidebar.checkbox('Show Temperature', value=True)
            show_humidity = st.sidebar.checkbox('Show Humidity', value=True)
            show_wind = st.sidebar.checkbox('Show Wind Speed', value=True)
            temp_keywords = ['temp', 'temperature']
            humidity_keywords = ['humidity', 'hum']
            wind_keywords = ['wind']
            def sensor_type(name, keywords):
                return any(kw.lower() in str(name).lower() for kw in keywords)
            temp_df = pd.DataFrame()
            humidity_df = pd.DataFrame()
            wind_df = pd.DataFrame()
            if show_temp:
                temp_df = df[df['sensor_name'].apply(lambda x: sensor_type(x, temp_keywords))]
                temp_df = temp_df.sort_values(['sensor_name', 'record_datetime'])
                if not temp_df.empty:
                    st.subheader('Temperature Data')
                    st.dataframe(temp_df[['record_datetime', 'sensor_name', 'value_calibration', 'sensor_unit']])
                    st.line_chart(temp_df.set_index('record_datetime')['value_calibration'])
                    st.download_button('Download Temperature Data (CSV)', to_csv_bytes(temp_df), file_name='temperature_data.csv', mime='text/csv')
                    st.download_button('Download Temperature Data (XLSX)', to_xlsx_bytes(temp_df), file_name='temperature_data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            if show_humidity:
                humidity_df = df[df['sensor_name'].apply(lambda x: sensor_type(x, humidity_keywords))]
                humidity_df = humidity_df.sort_values(['sensor_name', 'record_datetime'])
                if not humidity_df.empty:
                    st.subheader('Humidity Data')
                    st.dataframe(humidity_df[['record_datetime', 'sensor_name', 'value_calibration', 'sensor_unit']])
                    st.line_chart(humidity_df.set_index('record_datetime')['value_calibration'])
                    st.download_button('Download Humidity Data (CSV)', to_csv_bytes(humidity_df), file_name='humidity_data.csv', mime='text/csv')
                    st.download_button('Download Humidity Data (XLSX)', to_xlsx_bytes(humidity_df), file_name='humidity_data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            if show_wind:
                wind_df = df[df['sensor_name'].apply(lambda x: sensor_type(x, wind_keywords))]
                if not wind_df.empty:
                    st.subheader('Wind Speed Data')
                    st.dataframe(wind_df[['record_datetime', 'sensor_name', 'value_calibration', 'sensor_unit']])
                    st.line_chart(wind_df.set_index('record_datetime')['value_calibration'])
            if show_temp and show_humidity and not temp_df.empty and not humidity_df.empty:
                combined_df = pd.concat([temp_df, humidity_df]).sort_values(['sensor_name', 'record_datetime'])
                st.download_button(
                    label='Download Combined Temperature & Humidity (XLSX)',
                    data=to_xlsx_bytes(combined_df),
                    file_name='combined_temp_humidity.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            # THI Calculation
            merged_thi = pd.DataFrame()
            if show_temp and show_humidity and not temp_df.empty and not humidity_df.empty:
                merged_thi = pd.merge(
                    temp_df,
                    humidity_df,
                    on=['record_datetime', 'sensor_name'],
                    suffixes=('_temp', '_hum'),
                    how='inner'
                )
                if merged_thi.empty:
                    merged_thi = pd.merge(
                        temp_df,
                        humidity_df,
                        on='record_datetime',
                        suffixes=('_temp', '_hum'),
                        how='inner'
                    )
                    if 'sensor_name_temp' in merged_thi.columns and 'sensor_name_hum' in merged_thi.columns:
                        merged_thi['sensor_name'] = merged_thi['sensor_name_temp'].combine_first(merged_thi['sensor_name_hum'])
                    else:
                        merged_thi['sensor_name'] = ''
                if not merged_thi.empty:
                    merged_thi['THI'] = merged_thi['value_calibration_temp'] - (
                        (0.55 - 0.0055 * merged_thi['value_calibration_hum']) * (merged_thi['value_calibration_temp'] - 14.5)
                    )
                    def interpret_thi(thi):
                        if thi < 27:
                            return 'Aman (Normal)'
                        elif 27 <= thi < 28:
                            return 'Waspada (Stress Ringan)'
                        elif 28 <= thi < 30:
                            return 'Stress Sedang'
                        else:
                            return 'Stress Berat'
                    merged_thi['THI_Interpretasi'] = merged_thi['THI'].apply(interpret_thi)
                    st.subheader('Temperature Humidity Index (THI) for Broiler Chicken')
                    st.dataframe(merged_thi[['record_datetime', 'sensor_name', 'value_calibration_temp', 'value_calibration_hum', 'THI', 'THI_Interpretasi']])
                    st.line_chart(merged_thi.set_index('record_datetime')['THI'])
                    st.markdown('**Ringkasan Kategori Stress Ayam Broiler:**')
                    st.write(merged_thi['THI_Interpretasi'].value_counts())
                    color_map_thi = {
                        'Aman (Normal)': '#4CAF50',
                        'Waspada (Stress Ringan)': '#FFEB3B',
                        'Stress Sedang': '#FF9800',
                        'Stress Berat': '#F44336'
                    }
                    thi_counts = merged_thi['THI_Interpretasi'].value_counts()
                    thi_labels = thi_counts.index.tolist()
                    thi_colors = [color_map_thi.get(label, '#9E9E9E') for label in thi_labels]
                    fig_thi, ax_thi = plt.subplots()
                    ax_thi.pie(
                        thi_counts,
                        labels=thi_labels,
                        autopct='%1.1f%%',
                        colors=thi_colors,
                        startangle=140,
                        textprops={'fontsize': 12}
                    )
                    ax_thi.set_title('Proporsi Kategori Stress Ayam Broiler', fontsize=14, fontweight='bold')
                    ax_thi.legend(thi_labels, title='Kategori', loc='center left', bbox_to_anchor=(1, 0.5))
                    st.pyplot(fig_thi)
                    plt.close(fig_thi)
                    summary = merged_thi['THI_Interpretasi'].value_counts()
                    total = summary.sum()
                    kesimpulan = ''
                    if summary.get('Stress Berat', 0) > 0:
                        kesimpulan += f"Terdapat {summary.get('Stress Berat', 0)} data (" + f"{summary.get('Stress Berat', 0)/total*100:.1f}%" + ") ayam dalam kondisi STRESS BERAT. Segera lakukan tindakan perbaikan lingkungan!\n"
                    if summary.get('Stress Sedang', 0) > 0:
                        kesimpulan += f"Terdapat {summary.get('Stress Sedang', 0)} data (" + f"{summary.get('Stress Sedang', 0)/total*100:.1f}%" + ") ayam dalam kondisi STRESS SEDANG. Perlu peningkatan ventilasi dan pengelolaan suhu!\n"
                    if summary.get('Waspada (Stress Ringan)', 0) > 0:
                        kesimpulan += f"Terdapat {summary.get('Waspada (Stress Ringan)', 0)} data (" + f"{summary.get('Waspada (Stress Ringan)', 0)/total*100:.1f}%" + ") ayam dalam kondisi WASPADA (STRESS RINGAN). Monitor kondisi kandang secara berkala.\n"
                    if summary.get('Aman (Normal)', 0) > 0:
                        kesimpulan += f"Sebagian besar data ({summary.get('Aman (Normal)', 0)}/{total}) ayam dalam kondisi AMAN (NORMAL)."
                    st.markdown('**Kesimpulan Otomatis:**')
                    st.info(kesimpulan)
                    st.markdown('''**Saran Pencegahan dan Perbaikan:**
- Pastikan ventilasi kandang cukup dan lancar.
- Gunakan kipas atau sistem pendingin evaporatif jika suhu tinggi.
- Sediakan air minum yang cukup dan segar.
- Kurangi kepadatan kandang jika memungkinkan.
- Lakukan penyiraman lantai atau atap kandang saat cuaca panas.
- Monitor suhu dan kelembaban secara berkala, terutama pada siang hari.
- Segera lakukan tindakan jika proporsi stress sedang/berat meningkat.''')
                    st.markdown('''**Referensi:**  
Zulbardi, Z., et al. (2019). "Temperature Humidity Index (THI) dan Pengaruhnya terhadap Produksi dan Kesehatan Ayam Broiler." Jurnal Ilmu Ternak dan Veteriner, 24(2), 123-130.  
Serta sumber-sumber lain terkait manajemen lingkungan ayam broiler di Indonesia.''')
                    st.download_button(
                        label='Download THI Data (XLSX)',
                        data=to_xlsx_bytes(merged_thi),
                        file_name='thi_broiler.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            # Wind Chill Effect Calculation
            wind_merged = pd.DataFrame()
            if show_temp and show_wind and not temp_df.empty and not wind_df.empty:
                wind_merged = pd.merge(
                    temp_df,
                    wind_df,
                    on=['record_datetime', 'sensor_name'],
                    suffixes=('_temp', '_wind'),
                    how='inner'
                )
                if wind_merged.empty:
                    wind_merged = pd.merge(
                        temp_df,
                        wind_df,
                        on='record_datetime',
                        suffixes=('_temp', '_wind'),
                        how='inner'
                    )
                    if 'sensor_name_temp' in wind_merged.columns and 'sensor_name_wind' in wind_merged.columns:
                        wind_merged['sensor_name'] = wind_merged['sensor_name_temp'].combine_first(wind_merged['sensor_name_wind'])
                    else:
                        wind_merged['sensor_name'] = ''
                if not wind_merged.empty:
                    wind_merged['WCI'] = wind_merged['value_calibration_temp'] - (wind_merged['value_calibration_wind'] * 0.7)
                    def interpret_wci(wci):
                        if wci < 24:
                            return 'Risiko Kedinginan (Wind Chill Tinggi)'
                        elif 24 <= wci < 27:
                            return 'Cukup Dingin (Perlu Waspada)'
                        else:
                            return 'Aman (Normal)'
                    wind_merged['WCI_Interpretasi'] = wind_merged['WCI'].apply(interpret_wci)
                    st.subheader('Wind Chill Effect pada Ayam Broiler')
                    st.dataframe(wind_merged[['record_datetime', 'sensor_name', 'value_calibration_temp', 'value_calibration_wind', 'WCI', 'WCI_Interpretasi']])
                    st.line_chart(wind_merged.set_index('record_datetime')['WCI'])
                    st.markdown('**Ringkasan Kategori Wind Chill Effect:**')
                    st.write(wind_merged['WCI_Interpretasi'].value_counts())
                    color_map_wci = {
                        'Aman (Normal)': '#4CAF50',
                        'Cukup Dingin (Perlu Waspada)': '#2196F3',
                        'Risiko Kedinginan (Wind Chill Tinggi)': '#9C27B0'
                    }
                    wci_counts = wind_merged['WCI_Interpretasi'].value_counts()
                    wci_labels = wci_counts.index.tolist()
                    wci_colors = [color_map_wci.get(label, '#9E9E9E') for label in wci_labels]
                    fig_wci, ax_wci = plt.subplots()
                    ax_wci.pie(
                        wci_counts,
                        labels=wci_labels,
                        autopct='%1.1f%%',
                        colors=wci_colors,
                        startangle=140,
                        textprops={'fontsize': 12}
                    )
                    ax_wci.set_title('Proporsi Wind Chill Effect pada Ayam Broiler', fontsize=14, fontweight='bold')
                    ax_wci.legend(wci_labels, title='Kategori', loc='center left', bbox_to_anchor=(1, 0.5))
                    st.pyplot(fig_wci)
                    plt.close(fig_wci)
                    wci_summary = wind_merged['WCI_Interpretasi'].value_counts()
                    wci_total = wci_summary.sum()
                    wci_kesimpulan = ''
                    if wci_summary.get('Risiko Kedinginan (Wind Chill Tinggi)', 0) > 0:
                        wci_kesimpulan += f"Terdapat {wci_summary.get('Risiko Kedinginan (Wind Chill Tinggi)', 0)} data (" + f"{wci_summary.get('Risiko Kedinginan (Wind Chill Tinggi)', 0)/wci_total*100:.1f}%" + ") ayam berisiko kedinginan akibat efek angin tinggi.\n"
                    if wci_summary.get('Cukup Dingin (Perlu Waspada)', 0) > 0:
                        wci_kesimpulan += f"Terdapat {wci_summary.get('Cukup Dingin (Perlu Waspada)', 0)} data (" + f"{wci_summary.get('Cukup Dingin (Perlu Waspada)', 0)/wci_total*100:.1f}%" + ") ayam dalam kondisi cukup dingin, perlu waspada.\n"
                    if wci_summary.get('Aman (Normal)', 0) > 0:
                        wci_kesimpulan += f"Sebagian besar data ({wci_summary.get('Aman (Normal)', 0)}/{wci_total}) ayam dalam kondisi aman dari wind chill."
                    st.markdown('**Kesimpulan Wind Chill Effect:**')
                    st.info(wci_kesimpulan)
                    st.markdown('''**Saran Pencegahan dan Perbaikan Wind Chill:**
- Tutup celah kandang saat angin kencang atau malam hari.
- Tambahkan tirai atau penghalang angin di sisi kandang yang terbuka.
- Pastikan ayam tidak langsung terpapar angin kencang.
- Sediakan pemanas tambahan jika suhu dan wind chill sangat rendah.
- Monitor wind speed dan suhu secara berkala, terutama saat cuaca ekstrem.''')
                    st.markdown('''**Referensi:**  
SNI 01-4869.3-2008. Tata Cara Perancangan Lingkungan dan Bangunan Kandang Ayam Pedaging (Broiler).  
Serta sumber-sumber lain terkait wind chill effect pada unggas tropis.''')
                    st.download_button(
                        label='Download Wind Chill Data (XLSX)',
                        data=to_xlsx_bytes(wind_merged),
                        file_name='wind_chill_broiler.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            # Gabungan THI dan Wind Chill Effect
            if show_temp and show_humidity and show_wind and not temp_df.empty and not humidity_df.empty and not wind_df.empty and not merged_thi.empty and not wind_merged.empty:
                thi_df = merged_thi[['record_datetime', 'sensor_name', 'value_calibration_temp', 'value_calibration_hum', 'THI', 'THI_Interpretasi']].copy()
                del merged_thi
                wci_df = wind_merged[['record_datetime', 'sensor_name', 'value_calibration_wind', 'WCI', 'WCI_Interpretasi']].copy()
                del wind_merged
                combined = pd.merge(
                    thi_df,
                    wci_df,
                    on=['record_datetime', 'sensor_name'],
                    how='inner'
                )
                def interpretasi_gabungan(row):
                    if row['THI_Interpretasi'] in ['Stress Berat', 'Stress Sedang'] or row['WCI_Interpretasi'] == 'Risiko Kedinginan (Wind Chill Tinggi)':
                        return 'Risiko Tinggi: Segera lakukan perbaikan lingkungan!'
                    elif row['THI_Interpretasi'] == 'Waspada (Stress Ringan)' or row['WCI_Interpretasi'] == 'Cukup Dingin (Perlu Waspada)':
                        return 'Waspada: Monitor dan lakukan pencegahan.'
                    else:
                        return 'Aman'
                combined['Interpretasi Gabungan'] = combined.apply(interpretasi_gabungan, axis=1)
                def saran_gabungan(row):
                    if row['Interpretasi Gabungan'] == 'Risiko Tinggi: Segera lakukan perbaikan lingkungan!':
                        return 'Perbaiki ventilasi, tambahkan pendingin/pemanas, kurangi kepadatan, dan lindungi dari angin.'
                    elif row['Interpretasi Gabungan'] == 'Waspada: Monitor dan lakukan pencegahan.':
                        return 'Pantau suhu, kelembaban, dan angin secara berkala, lakukan tindakan preventif.'
                    else:
                        return 'Pertahankan kondisi kandang saat ini.'
                combined['Saran Pencegahan'] = combined.apply(saran_gabungan, axis=1)
                st.subheader('Tabel Gabungan THI & Wind Chill Effect')
                st.dataframe(combined)
                st.markdown('**Grafik Time Series Gabungan THI & Wind Chill (Interaktif):**')
                combined['record_datetime'] = pd.to_datetime(combined['record_datetime'])
                fig = go.Figure([
                    go.Scatter(
                        x=combined['record_datetime'],
                        y=combined['THI'],
                        mode='lines+markers',
                        name='THI',
                        line=dict(color='#F44336'),
                        marker=dict(symbol='circle', size=7),
                        hovertemplate='Waktu: %{x}<br>THI: %{y:.2f}'
                    ),
                    go.Scatter(
                        x=combined['record_datetime'],
                        y=combined['WCI'],
                        mode='lines+markers',
                        name='Wind Chill Index',
                        line=dict(color='#2196F3'),
                        marker=dict(symbol='square', size=7),
                        hovertemplate='Waktu: %{x}<br>WCI: %{y:.2f}'
                    )
                ])
                fig.update_layout(
                    xaxis_title='Datetime',
                    yaxis_title='Nilai Indeks',
                    title='Time Series THI & Wind Chill Index',
                    legend=dict(x=0, y=1),
                    hovermode='x unified',
                    template='plotly_white',
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('**Ringkasan & Visualisasi Proporsi Interpretasi Gabungan:**')
                summary_combined = combined['Interpretasi Gabungan'].value_counts()
                st.write(summary_combined)
                color_map_combined = {
                    'Aman': '#4CAF50',
                    'Waspada: Monitor dan lakukan pencegahan.': '#FFEB3B',
                    'Risiko Tinggi: Segera lakukan perbaikan lingkungan!': '#F44336'
                }
                labels = summary_combined.index.tolist()
                colors = [color_map_combined.get(label, '#9E9E9E') for label in labels]
                fig_comb, ax_comb = plt.subplots()
                ax_comb.pie(summary_combined, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140, textprops={'fontsize': 12})
                ax_comb.set_title('Proporsi Interpretasi Gabungan THI & Wind Chill', fontsize=14, fontweight='bold')
                ax_comb.legend(labels, title='Kategori', loc='center left', bbox_to_anchor=(1, 0.5))
                st.pyplot(fig_comb)
                plt.close(fig_comb)
                st.download_button(
                    label='Download Gabungan THI & Wind Chill (XLSX)',
                    data=to_xlsx_bytes(combined),
                    file_name='gabungan_thi_windchill.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                del thi_df
                del wci_df
                del combined
            if not (show_temp or show_humidity or show_wind):
                st.info('Please select at least one sensor type to display.')
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

if __name__ == '__main__':
    main()