import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import streamlit as st
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# --- Arps hyperbolic decline ---
def arps_hyperbolic(t, qi, di, b):
    return qi / np.power(1 + b * di * t, 1 / b)

# --- Estimate b-factor using curve_fit (LM algorithm) ---
def estimate_b_lm(qi, qe, di, t_months):
    def arps_with_b(t, b):
        return qi / np.power(1 + b * di * t, 1 / b)

    try:
        t_data = np.array([0, t_months])
        q_data = np.array([qi, qe])
        popt, _ = curve_fit(arps_with_b, t_data, q_data, bounds=(0.000000000001, 5.0))
        return float(popt[0])
    except:
        return np.nan

# --- Generate forecast table with calendar dates ---
def forecast_well_with_dates(qi, di, b, months, start_date):
    t = np.arange(0, months + 1)
    q = arps_hyperbolic(t, qi, di, b)
    dates = pd.date_range(start=start_date, periods=months + 1, freq='MS')
    return pd.DataFrame({'Date': dates, 'Rate (bbl/d)': q})

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("🛢️ Decline Curve Analysis with B-Factor Estimation (LM Method)")

uploaded_file = st.file_uploader("📤 Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    required_cols = ['Well Name', 'Qi', 'Qe', 't, months', 'Di Mon Eff', 'Start date']

    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ Your file must include: {required_cols}")
    else:
        b_factors = []
        q_diff = []
        forecast_dict = {}

        for _, row in df.iterrows():
            well = row['Well Name']
            qi = row['Qi']
            qe_input = row['Qe']
            t_months = row['t, months']
            di = row['Di Mon Eff']
            start_date = pd.to_datetime(row['Start date'])

            b = estimate_b_lm(qi, qe_input, di, t_months)
            forecast_df = forecast_well_with_dates(qi, di, b, int(t_months), start_date)

            qe_forecasted = forecast_df.iloc[-1]['Rate (bbl/d)']
            mismatch = qe_forecasted - qe_input

            b_factors.append(round(b, 8))
            q_diff.append(round(mismatch, 2))

            forecast_dict[well] = {
                'b': b,
                'forecast': forecast_df
            }

        # Add new columns to input table
        df['Estimated b-factor'] = b_factors
        df['Qe mismatch (STB/month)'] = q_diff

        # --- Section 1: Show full input table and download ---
        st.subheader("📋 Processed Input Table")
        st.dataframe(df.style.format({
            'Qi': '{:.2f}', 'Qe': '{:.2f}', 'Di Mon Eff': '{:.4f}',
            'Estimated b-factor': '{:.12f}', 'Qe mismatch (bbl/d)': '{:.2f}'
        }), use_container_width=True)

        input_output = BytesIO()
        with pd.ExcelWriter(input_output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Input Data')
        input_output.seek(0)

        st.download_button(
            label="📥 Download Processed Input Table",
            data=input_output,
            file_name="processed_input_table.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        st.markdown("---")

        # --- Section 2: Well forecast visualization ---
        st.subheader("📊 Forecast Visualization by Well")
        selected_well = st.selectbox("🔽 Select a well to view forecast:", df['Well Name'].tolist())

        if selected_well:
            result = forecast_dict[selected_well]
            forecast_df = result['forecast']
            b_val = result['b']

            forecast_df_display = forecast_df.copy()
            forecast_df_display['Date'] = forecast_df_display['Date'].dt.strftime('%Y-%m-%d')

            col1, col2 = st.columns([1, 1.5])

            with col1:
                st.markdown(f"### 📈 Forecast Table for {selected_well}")
                st.write(f"**Estimated b-factor**: `{b_val:.3f}`")
                st.dataframe(
                    forecast_df_display.style.format({'Rate (STB/month)': '{:.2f}'}),
                    use_container_width=True
                )

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    forecast_df_display.to_excel(writer, index=False, sheet_name='Forecast')
                output.seek(0)

                st.download_button(
                    label=f"📥 Download Forecast for {selected_well}",
                    data=output,
                    file_name=f"{selected_well}_forecast.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            with col2:
                st.markdown(f"### 📉 Decline Curve for {selected_well}")
                # st.line_chart(forecast_df.set_index('Date'))
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(forecast_df['Date'], forecast_df['Rate (bbl/d)'], color='red')
                ax.set_title(f"Decline Curve for {selected_well}")
                ax.set_ylabel("Rate (bbl/d)")
                ax.set_xlabel("Year")

                # Format x-axis to show only years
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                ax.grid(True)

                st.pyplot(fig)
