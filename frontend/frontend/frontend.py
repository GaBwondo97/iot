from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="CityPulse AI — Urban Environmental Intelligence",
    page_icon="🌆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING CSS KUSTOM & KONTRAK VISUAL KEPARAHAN ---
st.markdown("""
<style>
    .severity-badge {
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        text-transform: uppercase;
    }
    .sev-low { background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
    .sev-moderate { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .sev-high { background-color: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid #f97316; }
    .sev-critical { background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .sev-insufficient { background-color: rgba(100, 116, 139, 0.25); color: #cbd5e1; border: 1px solid #64748b; }

    .source-tag-sim {
        background-color: rgba(168, 85, 247, 0.2);
        color: #d8b4fe;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .source-tag-api {
        background-color: rgba(14, 165, 233, 0.2);
        color: #7dd3fc;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

SEVERITY_CLASS_MAP = {
    "Low": "sev-low",
    "Moderate": "sev-moderate",
    "High": "sev-high",
    "Critical": "sev-critical",
    "Insufficient Data": "sev-insufficient"
}

# --- REFERENSI KOTA & MOCK DATABASE (SESUAI KONTRAK KANONIS) ---
SUPPORTED_CITIES = {
    "kuala-lumpur": {"name": "Kuala Lumpur", "country": "Malaysia"},
    "jakarta": {"name": "Jakarta", "country": "Indonesia"},
    "singapore": {"name": "Singapore", "country": "Singapore"},
}

MOCK_DATABASE = {
    "kuala-lumpur": {
        "assessment": {
            "assessment_id": "assess-kl-001",
            "city_id": "kuala-lumpur",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "status": "analyzed",
            "risk_score": 0.68,
            "severity": "High",
            "confidence": 0.85,
            "data_sufficiency": {"coverage": 0.92, "missing": []},
            "drivers": [
                "Heat index reached 39.2°C (Danger threshold)",
                "Simulated traffic congestion index at 0.82 (High)"
            ],
            "recommendations": [
                {
                    "id": "rec-01",
                    "priority": 1,
                    "category": "weather",
                    "text": "Issue public heat advisory for outdoor workers",
                    "rationale": "Sustained temperature of 34.5°C with 75% humidity elevates heat stress risk."
                },
                {
                    "id": "rec-02",
                    "priority": 2,
                    "category": "traffic",
                    "text": "Optimize traffic signal intervals along central corridors",
                    "rationale": "Simulated vehicle density (120 veh/km) correlates with rising local PM2.5."
                }
            ],
            "provenance": {"sources": ["open_meteo", "iot_simulator"], "includes_simulated": True}
        },
        "observations": {
            "weather": {
                "source_type": "public_api",
                "source_name": "Open-Meteo",
                "status": "active",
                "metrics": {
                    "Temperature": {"value": 34.5, "unit": "°C"},
                    "Humidity": {"value": 75, "unit": "%"},
                    "Rainfall": {"value": 0.0, "unit": "mm/h"},
                    "Wind Speed": {"value": 14.2, "unit": "km/h"}
                }
            },
            "air_quality": {
                "source_type": "public_api",
                "source_name": "Open-Meteo (Modelled)",
                "status": "active",
                "metrics": {
                    "PM2.5": {"value": 45.0, "unit": "µg/m³"},
                    "PM10": {"value": 70.0, "unit": "µg/m³"},
                    "AQI": {"value": 124, "unit": "US AQI"},
                    "CO2": {"value": 430, "unit": "ppm"}
                }
            },
            "traffic": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "active",
                "metrics": {
                    "Vehicle Count": {"value": 850, "unit": "veh"},
                    "Average Speed": {"value": 22.5, "unit": "km/h"},
                    "Traffic Density": {"value": 120, "unit": "veh/km"},
                    "Congestion Level": {"value": "High", "unit": ""}
                }
            },
            "population": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "active",
                "metrics": {
                    "Estimated Population": {"value": 15400, "unit": "people"},
                    "Population Density": {"value": 5100, "unit": "/km²"},
                    "Crowd Density": {"value": "High", "unit": ""},
                    "Population Change": {"value": "+250", "unit": "people"}
                }
            }
        },
        "trends": [
            {"time": "06:00", "risk_score": 0.32, "aqi": 68},
            {"time": "08:00", "risk_score": 0.48, "aqi": 85},
            {"time": "10:00", "risk_score": 0.55, "aqi": 98},
            {"time": "12:00", "risk_score": 0.64, "aqi": 112},
            {"time": "14:00", "risk_score": 0.68, "aqi": 124},
        ]
    },
    "jakarta": {
        "assessment": {
            "assessment_id": "assess-jkt-001",
            "city_id": "jakarta",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "status": "analyzed",
            "risk_score": 0.78,
            "severity": "Critical",
            "confidence": 0.90,
            "data_sufficiency": {"coverage": 1.0, "missing": []},
            "drivers": [
                "PM2.5 concentration reached 88.4 µg/m³ (Unhealthy)",
                "Severe arterial congestion detected"
            ],
            "recommendations": [
                {
                    "id": "rec-jkt-01",
                    "priority": 1,
                    "category": "air_quality",
                    "text": "Recommend N95 masks and limit prolonged outdoor exertion",
                    "rationale": "AQI exceeded 165 threshold across monitoring nodes."
                }
            ],
            "provenance": {"sources": ["open_meteo", "iot_simulator"], "includes_simulated": True}
        },
        "observations": {
            "weather": {
                "source_type": "public_api",
                "source_name": "Open-Meteo",
                "status": "active",
                "metrics": {
                    "Temperature": {"value": 33.1, "unit": "°C"},
                    "Humidity": {"value": 78, "unit": "%"},
                    "Rainfall": {"value": 2.5, "unit": "mm/h"},
                    "Wind Speed": {"value": 11.0, "unit": "km/h"}
                }
            },
            "air_quality": {
                "source_type": "public_api",
                "source_name": "Open-Meteo (Modelled)",
                "status": "active",
                "metrics": {
                    "PM2.5": {"value": 88.4, "unit": "µg/m³"},
                    "PM10": {"value": 125.0, "unit": "µg/m³"},
                    "AQI": {"value": 168, "unit": "US AQI"},
                    "CO2": {"value": 465, "unit": "ppm"}
                }
            },
            "traffic": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "active",
                "metrics": {
                    "Vehicle Count": {"value": 1240, "unit": "veh"},
                    "Average Speed": {"value": 15.0, "unit": "km/h"},
                    "Traffic Density": {"value": 165, "unit": "veh/km"},
                    "Congestion Level": {"value": "High", "unit": ""}
                }
            },
            "population": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "active",
                "metrics": {
                    "Estimated Population": {"value": 24000, "unit": "people"},
                    "Population Density": {"value": 8200, "unit": "/km²"},
                    "Crowd Density": {"value": "High", "unit": ""},
                    "Population Change": {"value": "+610", "unit": "people"}
                }
            }
        },
        "trends": [
            {"time": "06:00", "risk_score": 0.51, "aqi": 115},
            {"time": "08:00", "risk_score": 0.65, "aqi": 140},
            {"time": "10:00", "risk_score": 0.72, "aqi": 154},
            {"time": "12:00", "risk_score": 0.75, "aqi": 160},
            {"time": "14:00", "risk_score": 0.78, "aqi": 168},
        ]
    },
    "singapore": {
        "assessment": {
            "assessment_id": "assess-sg-001",
            "city_id": "singapore",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "status": "insufficient_data",
            "risk_score": None,
            "severity": "Insufficient Data",
            "confidence": None,
            "data_sufficiency": {"coverage": 0.35, "missing": ["air_quality", "traffic"]},
            "drivers": [],
            "recommendations": [
                {
                    "id": "rec-sg-01",
                    "priority": 1,
                    "category": "system",
                    "text": "Assessment cannot be reliably computed yet",
                    "rationale": "Coverage is 35% (minimum 50% required). Waiting for offline IoT sensors to reconnect."
                }
            ],
            "provenance": {"sources": ["open_meteo"], "includes_simulated": False}
        },
        "observations": {
            "weather": {
                "source_type": "public_api",
                "source_name": "Open-Meteo",
                "status": "active",
                "metrics": {
                    "Temperature": {"value": 30.8, "unit": "°C"},
                    "Humidity": {"value": 82, "unit": "%"},
                    "Rainfall": {"value": 5.0, "unit": "mm/h"},
                    "Wind Speed": {"value": 19.5, "unit": "km/h"}
                }
            },
            "air_quality": {
                "source_type": "public_api",
                "source_name": "Open-Meteo",
                "status": "degraded",
                "metrics": {
                    "PM2.5": {"value": None, "unit": "µg/m³"},
                    "PM10": {"value": None, "unit": "µg/m³"},
                    "AQI": {"value": None, "unit": "US AQI"},
                    "CO2": {"value": None, "unit": "ppm"}
                }
            },
            "traffic": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "offline",
                "metrics": {
                    "Vehicle Count": {"value": None, "unit": "veh"},
                    "Average Speed": {"value": None, "unit": "km/h"},
                    "Traffic Density": {"value": None, "unit": "veh/km"},
                    "Congestion Level": {"value": None, "unit": ""}
                }
            },
            "population": {
                "source_type": "simulation",
                "source_name": "MQTT Virtual Sensor",
                "status": "active",
                "metrics": {
                    "Estimated Population": {"value": 9200, "unit": "people"},
                    "Population Density": {"value": 3400, "unit": "/km²"},
                    "Crowd Density": {"value": "Low", "unit": ""},
                    "Population Change": {"value": "-40", "unit": "people"}
                }
            }
        },
        "trends": []
    }
}

# --- SIDEBAR KONTROL ---
with st.sidebar:
    st.title("🌆 CityPulse AI")
    st.caption("Global Urban Risk Monitoring System")
    st.divider()

    selected_city_id = st.selectbox(
        "Pilih Kota Pemantauan:",
        options=list(SUPPORTED_CITIES.keys()),
        format_func=lambda cid: f"{SUPPORTED_CITIES[cid]['name']}, {SUPPORTED_CITIES[cid]['country']}"
    )

    if st.button("↻ Refresh Dashboard", use_container_width=True):
        st.rerun()

    st.divider()
    st.markdown("""
    **Catatan Desain & Integrasi:**
    - Sistem pendukung keputusan (*Decision-Support*)[cite: 1, 3].
    - Data hilang/kosong ditampilkan secara eksplisit sebagai `N/A` (tidak pernah dipaksa jadi 0)[cite: 2, 4].
    - Sumber data simulasi diberi label `SIMULATED`[cite: 3, 4].
    """)

# --- AMBIL DATA SESUAI KOTA TERPILIH ---
city_data = MOCK_DATABASE.get(selected_city_id, MOCK_DATABASE["kuala-lumpur"])
assessment = city_data["assessment"]
observations = city_data["observations"]
trends = city_data["trends"]
city_info = SUPPORTED_CITIES[selected_city_id]

# --- HEADER UTAMA ---
col_title, col_sync = st.columns([3, 1])
with col_title:
    st.subheader(f"Wilayah: {city_info['name']}, {city_info['country']}")
with col_sync:
    st.caption(f"Sync Time (UTC): {datetime.now(timezone.utc).strftime('%H:%M:%S Z')}")

is_insufficient = assessment["status"] == "insufficient_data" or assessment["risk_score"] is None

if is_insufficient:
    missing_items = ", ".join(assessment.get("data_sufficiency", {}).get("missing", []))
    coverage_pct = int(assessment.get("data_sufficiency", {}).get("coverage", 0) * 100)
    st.warning(
        f"⚠️ **INSUFFICIENT DATA (Coverage: {coverage_pct}%)** — "
        f"Indikator yang belum lengkap/offline: `{missing_items}`. "
        f"Skor risiko bernilai `NULL` (tidak menampilkan asumsi risiko rendah)."
    )

st.divider()

# --- BAGIAN 1: KARTU RISIKO & GRAFIK TREN ---
col_risk, col_chart = st.columns([1, 2])

with col_risk:
    st.markdown("#### Composite City Risk")
    sev_label = assessment["severity"]
    sev_class = SEVERITY_CLASS_MAP.get(sev_label, "sev-insufficient")

    score_display = "N/A" if is_insufficient else f"{assessment['risk_score']:.2f}"
    conf_display = "N/A" if is_insufficient else f"{int(assessment['confidence'] * 100)}%"

    st.markdown(f"""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155;">
            <div style="font-size: 3rem; font-weight: 800; line-height: 1.1; margin-bottom: 8px;">{score_display}</div>
            <span class="severity-badge {sev_class}">{sev_label}</span>
            <p style="margin-top: 12px; font-size: 0.9rem; color: #94a3b8;">
                Confidence: <strong style="color: #f8fafc;">{conf_display}</strong> &nbsp;|&nbsp;
                Status: <code>{assessment['status']}</code>
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("**Primary Risk Drivers:**")
    if assessment["drivers"]:
        for driver in assessment["drivers"]:
            st.markdown(f"- {driver}")
    else:
        st.caption("Tidak ada pemicu risiko aktif terdeteksi.")

with col_chart:
    st.markdown("#### 24-Hour Environmental & Risk Trend")
    if trends:
        df_trends = pd.DataFrame(trends)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trends["time"], y=df_trends["risk_score"],
            name="Risk Score (0-1)", mode="lines+markers",
            line=dict(color="#f97316", width=3), yaxis="y1"
        ))
        fig.add_trace(go.Scatter(
            x=df_trends["time"], y=df_trends["aqi"],
            name="Air Quality (AQI)", mode="lines+markers",
            line=dict(color="#38bdf8", width=2, dash="dot"), yaxis="y2"
        ))
        fig.update_layout(
            height=290,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.6)",
            font=dict(color="#cbd5e1"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="Risk Score", range=[0, 1], gridcolor="#1e293b"),
            yaxis2=dict(title="AQI", range=[0, 300], overlaying="y", side="right", showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Riwayat tren belum mencukupi untuk kota ini (memerlukan minimal siklus simulasi aktif).")

st.divider()

# --- BAGIAN 2: GRID TELEMETRI (WEATHER, AIR QUALITY, TRAFFIC, POPULATION) ---
st.markdown("#### Live Urban & Environmental Telemetry")
category_titles = {
    "weather": "🌦️ Weather Monitoring",
    "air_quality": "💨 Air Quality",
    "traffic": "🚦 Traffic Conditions",
    "population": "👥 Population & Crowd"
}

cols_sensor = st.columns(4)
for idx, (cat_key, cat_data) in enumerate(observations.items()):
    with cols_sensor[idx]:
        with st.container(border=True):
            is_sim = cat_data["source_type"] == "simulation"
            badge_html = (
                '<span class="source-tag-sim">SIMULATED</span>'
                if is_sim else '<span class="source-tag-api">PUBLIC API</span>'
            )
            status_icon = "🟢" if cat_data["status"] == "active" else ("🟡" if cat_data["status"] == "degraded" else "🔴")

            st.markdown(f"**{status_icon} {category_titles.get(cat_key, cat_key)}**")
            st.markdown(
                f"{badge_html} <span style='font-size:0.75rem; color:#94a3b8;'>{cat_data['source_name']}</span>",
                unsafe_allow_html=True)
            st.markdown("---")

            for metric_name, m_info in cat_data["metrics"].items():
                val = m_info["value"]
                unit = m_info["unit"]
                if val is None:
                    st.markdown(f"**{metric_name}:** `N/A`")
                else:
                    st.markdown(f"**{metric_name}:** {val} {unit}")

st.divider()

# --- BAGIAN 3: ALERTS & AI RECOMMENDATIONS ---
col_alerts, col_recs = st.columns(2)

with col_alerts:
    st.markdown(f"#### 🚨 Anomaly & Threshold Alerts ({len(assessment['drivers'])})")
    if assessment["drivers"]:
        for driver in assessment["drivers"]:
            with st.container(border=True):
                st.markdown(f"**[{assessment['severity'].upper()}]** {driver}")
                st.caption(f"Computed at: {assessment['computed_at']}")
    else:
        st.success("Semua indikator berada dalam batas normal.")

with col_recs:
    st.markdown("#### 💡 AI Decision-Support Recommendations")
    if assessment["recommendations"]:
        for rec in assessment["recommendations"]:
            with st.container(border=True):
                st.markdown(f"**Priority #{rec['priority']} — {rec['text']}**")
                st.caption(f"Kategori: `{rec['category']}` | Rationale: {rec['rationale']}")
    else:
        st.info("Belum ada rekomendasi mitigasi yang memerlukan tindakan.")