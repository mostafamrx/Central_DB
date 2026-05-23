import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import io

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة تحكم بيانات العملاء", page_icon="📊", layout="wide")

# 2. كود CSS المطور لدعم RTL والثيم الداكن
st.markdown("""
<style>
    /* إجبار الخلفية الداكنة وتغيير لون النصوص العامة للأبيض */
    .stApp {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }

    /* الشاشة الرئيسية */
    .block-container { 
        direction: rtl; 
        text-align: right; 
    }
    
    /* الشريط الجانبي (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #1a202c !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* محاذاة وتلوين النصوص داخل الشريط الجانبي */
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1 {
        text-align: right !important;
        color: #ffffff !important;
    }
    
    /* ضبط قوائم الاختيار (Multiselect) */
    div[data-baseweb="select"] {
        direction: rtl;
    }

    /* تنسيق المؤشرات الرقمية (KPIs) */
    [data-testid="stMetric"] { 
        background-color: #1a202c; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #4a5568; 
        direction: rtl;
    }
    
    /* تنسيق زر التحميل */
    .stDownloadButton button { 
        background-color: #f36f21 !important; 
        color: white !important; 
        font-weight: bold; 
        width: 100%; 
        border: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 لوحة تحكم قاعدة بيانات العملاء المركزية")
st.markdown("---")

# 3. دالة جلب البيانات من PostgreSQL السحابية
@st.cache_data(ttl=60)
def load_data():
    try:
        # استبدل هذا الرابط بالرابط السحابي الخاص بك من Neon بالكامل
        CLOUD_DB_URL = "postgresql://neondb_owner:npg_sSlIUkKJ6F5B@ep-purple-butterfly-alnfe94v.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"
        engine = create_engine(CLOUD_DB_URL)
        query = "SELECT * FROM potential_customers ORDER BY created_at DESC;"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات السحابية: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ لا توجد بيانات لعرضها حتى الآن، أو هناك مشكلة في الاتصال بقاعدة البيانات.")
else:
    # 4. الشريط الجانبي (Sidebar) للفلاتر
    st.sidebar.header("🔍 فلاتر البحث")
    
    # أ) فلتر المصدر
    sources = df['customer_source'].dropna().unique().tolist()
    selected_sources = st.sidebar.multiselect("مصدر العميل:", sources, default=sources)
    
    # ب) فلتر المدينة
    cities = df['city'].dropna().unique().tolist()
    selected_cities = st.sidebar.multiselect("المدينة:", cities, default=cities)
    
    # ج) فلتر المنطقة / الحي (الجديد)
    areas = df['location_area'].dropna().unique().tolist()
    selected_areas = st.sidebar.multiselect("المنطقة / الحي:", areas, default=areas)
    
    # د) تطبيق الفلاتر المجمعة على البيانات
    mask = (
        (df['customer_source'].isin(selected_sources)) & 
        (df['city'].isin(selected_cities)) & 
        (df['location_area'].isin(selected_areas))
    )
    filtered_df = df[mask]

    # 5. عرض المؤشرات الرئيسية (KPIs)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="👥 إجمالي العملاء", value=len(filtered_df))
    with col2:
        st.metric(label="🏙️ إجمالي المدن المغطاة", value=filtered_df['city'].nunique())
    with col3:
        st.metric(label="📍 إجمالي الأحياء", value=filtered_df['location_area'].nunique())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 6. الرسوم البيانية التفاعلية
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if not filtered_df.empty:
            city_counts = filtered_df['city'].value_counts().reset_index()
            city_counts.columns = ['city', 'count']
            fig_city = px.bar(city_counts, x='city', y='count', 
                              title="توزيع العملاء حسب المدينة", 
                              labels={'city': 'المدينة', 'count': 'عدد العملاء'},
                              color='count', color_continuous_scale='Oranges')
            fig_city.update_layout(font=dict(family="Arial", size=14))
            st.plotly_chart(fig_city, use_container_width=True)

    with chart_col2:
        if not filtered_df.empty:
            source_counts = filtered_df['customer_source'].value_counts().reset_index()
            source_counts.columns = ['source', 'count']
            fig_source = px.pie(source_counts, names='source', values='count', 
                                title="نسبة العملاء حسب المصدر",
                                hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig_source.update_layout(font=dict(family="Arial", size=14))
            st.plotly_chart(fig_source, use_container_width=True)

    st.markdown("---")

# 7. عرض جدول البيانات وتصديره
    st.subheader("📋 تفاصيل البيانات (جاهزة لإعادة الاستهداف)")
    
    # التعديل هنا: تمت إضافة 'registered_by' لقائمة الأعمدة المخفية
    display_df = filtered_df.drop(columns=['id', 'created_at', 'registered_by'], errors='ignore')
    
    # عرض الجدول بدون العمود
    st.dataframe(display_df, use_container_width=True)
    
    # التصدير إلى Excel
    buffer = io.BytesIO()
    
    if 'phone_number' in display_df.columns:
        display_df['phone_number'] = display_df['phone_number'].astype(str)
        
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        display_df.to_excel(writer, index=False, sheet_name='Customers')
    
    st.download_button(
        label="📥 تصدير القائمة الحالية (Excel)",
        data=buffer.getvalue(),
        file_name='filtered_customers.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
