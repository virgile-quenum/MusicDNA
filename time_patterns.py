import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np, pandas as pd

def render(df):
    st.title("🕐 Time Patterns")
    DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("## By Hour of Day")
        hourly = df.groupby('hour')['ms'].sum().reindex(range(24),fill_value=0).reset_index()
        hourly.columns=['hour','ms']; hourly['hours']=hourly['ms']/3600000
        fig = px.bar(hourly,x='hour',y='hours',color_discrete_sequence=['#7C3AED'])
        fig.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                          xaxis=dict(gridcolor='#222',tickmode='linear'),
                          yaxis=dict(gridcolor='#222'),margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("## By Day of Week")
        dow = df.groupby('dow')['ms'].sum().reindex(range(7),fill_value=0).reset_index()
        dow.columns=['dow','ms']; dow['hours']=dow['ms']/3600000; dow['day']=DAYS
        fig2 = px.bar(dow,x='day',y='hours',color_discrete_sequence=['#A78BFA'])
        fig2.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                           xaxis=dict(gridcolor='#222'),yaxis=dict(gridcolor='#222'),
                           margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("## Heatmap — Hour × Day (hours)")
    hm = np.zeros((7,24))
    for _, row in df.iterrows():
        hm[int(row['dow']), int(row['hour'])] += row['ms']/3600000
    hm = np.round(hm,1)
    fig3 = go.Figure(data=go.Heatmap(
        z=hm, x=[f"{h:02d}h" for h in range(24)], y=DAYS,
        colorscale=[[0,'#111'],[0.01,'#0a3d1f'],[1,'#7C3AED']],
        hoverongaps=False, showscale=True))
    fig3.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                       margin=dict(l=0,r=0,t=10,b=0), height=280)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("## Monthly Volume")
    monthly = df.groupby('ym')['ms'].sum().reset_index()
    monthly['hours'] = monthly['ms']/3600000
    fig4 = px.area(monthly,x='ym',y='hours',color_discrete_sequence=['#7C3AED'])
    fig4.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                       xaxis=dict(gridcolor='#222',tickangle=45),
                       yaxis=dict(gridcolor='#222'),margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig4, use_container_width=True)

    peak_h = int(df.groupby('hour')['ms'].sum().idxmax())
    peak_d = DAYS[int(df.groupby('dow')['ms'].sum().idxmax())]
    sat_h  = df[df['dow']==5]['ms'].sum()/3600000
    st.markdown(f"""
    <div class='insight'>🕐 Peak hour: <b>{peak_h:02d}h</b> — you know when you listen.</div>
    <div class='insight'>📅 <b>{peak_d}</b> is your biggest day. Saturday alone: <b>{sat_h:.0f}h</b> total.</div>
    """, unsafe_allow_html=True)
