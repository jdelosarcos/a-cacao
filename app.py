"""Cacao Farm Intelligence | Streamlit frontend for the supplied 13-module analysis."""
import io, json, zipfile, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from engine import AnalysisSession

st.set_page_config(page_title='Cacao | Farm Intelligence',page_icon='🌱',layout='wide',initial_sidebar_state='expanded')
GREEN='#16766B'; GOLD='#D99B44'; DARK='#163D36'; COLORS=['#94A3B8',GREEN,GOLD]
st.markdown('''<style>
.stApp{background:#F4F7F2}.block-container{padding-top:1.3rem;max-width:1480px}
[data-testid="stSidebar"]{background:#123C35} [data-testid="stSidebar"] *{color:#EAF4EF!important}
[data-testid="stSidebar"] input{color:#173B34!important}
h1,h2,h3{color:#183E36;letter-spacing:-.025em}h1{font-weight:800}
[data-testid="stMetric"]{background:#FFF;border:1px solid #DDE8E0;border-radius:12px;padding:16px}
[data-testid="stMetricLabel"]{color:#526A62}.stButton>button[kind="primary"]{background:#16766B;border-color:#16766B}
.hero{padding:25px 30px;background:linear-gradient(110deg,#123C35,#1F7668);border-radius:17px;color:white;margin-bottom:20px}
.hero h1{color:white;margin:0}.hero p{color:#D3E9DD;margin:8px 0 0}
.insight{background:white;border-left:4px solid #D99B44;border-radius:8px;padding:13px 17px;margin:9px 0}
.smallnote{color:#61766D;font-size:0.9rem}
</style>''',unsafe_allow_html=True)

PAGES=['Overview','01 · Data quality','02 · Statistical associations','03 · Exploratory analytics',
       '04 · Farmer clustering','05 · Predictive models','06 · Model explanations',
       '07 · Yield forecasting','08 · Farmer insights','09 · Funding agency insights',
       '10 · Individual records','11 · Export center']

@st.cache_resource(show_spinner=False)
def get_session(key, raw):
    return AnalysisSession(raw)

def table(df, title=None):
    if title: st.subheader(title)
    st.dataframe(df,use_container_width=True,hide_index=True)

def download_df(df,name,label='Download CSV'):
    st.download_button(label,df.to_csv(index=False).encode('utf-8-sig'),file_name=name,mime='text/csv',key='dl_'+name)

def bar(df,x,y,title,color=None,orientation=None):
    if df.empty:return
    fig=px.bar(df,x=x,y=y,color=color,orientation=orientation,title=title,color_discrete_sequence=[GREEN,GOLD,'#9EB9A6','#8AABC0'])
    fig.update_layout(template='plotly_white',height=390,margin=dict(l=12,r=12,t=60,b=20),legend_title_text='')
    st.plotly_chart(fig,use_container_width=True)

def insight(text): st.markdown(f'<div class="insight">{text}</div>',unsafe_allow_html=True)

def pct(n):return f'{n:.1%}'

with st.sidebar:
    st.markdown('## 🌱 CACAO INTELLIGENCE')
    st.caption('Research analytics · Farmer welfare · Program accountability')
    upload=st.file_uploader('Upload CacaoY.csv',type='csv',help='Original survey CSV, including its first section-heading row and second header row.')
    page=st.radio('Workspace',PAGES,label_visibility='collapsed')
    st.divider()
    st.caption('Modules load only when opened. Heavy model training is deferred until needed.')
    st.caption('Analysis engine: original uploaded Python source, executed incrementally.')

st.markdown('<div class="hero"><h1>Cacao Farm Intelligence</h1><p>Evidence-led insights for growers, agricultural extension teams and funding partners</p></div>',unsafe_allow_html=True)
if upload is None:
    st.info('Upload the original **CacaoY.csv** survey to start. The Python analysis file is already included in this project.')
    st.markdown('**Workflow:** Start with data quality and exploratory analytics. Open clustering or modeling only when required. Forecasting requires a separate dated numeric yield series.')
    st.stop()

raw=upload.getvalue()
engine=get_session(hashlib.sha256(raw).hexdigest(),raw)

def run(n):
    with st.spinner(f'Loading analysis module {n} and any required prerequisites. First-time computation may take several minutes...'):
        try:engine.run(n)
        except Exception as exc:
            st.error(f'Module {n} could not complete: {exc}')
            st.caption('Confirm the survey schema, installed package versions and sufficient observations per yield class.')
            st.stop()

if page=='Overview':
    run(2)
    d=engine.ns['clean']; a=engine.ns['audit']
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Survey records',f'{len(d):,}');c2.metric('Municipalities',d.location.nunique())
    c3.metric('Survey fields',len(engine.ns['COLUMNS']));c4.metric('Changed cells',a['changed_cells'])
    left,right=st.columns(2)
    with left:
        counts=d.yield_original.value_counts().rename_axis('Reported yield').reset_index(name='Farmers')
        bar(counts,'Reported yield','Farmers','Original yield categories')
    with right:
        loc=d.location.value_counts().head(12).rename_axis('Municipality').reset_index(name='Farmers')
        bar(loc,'Farmers','Municipality','Top surveyed municipalities',orientation='h')
    insight('**Reading the dashboard:** These are survey-reported yield ranges per hectare per season. They are not measured continuous yields. All summaries describe the uploaded respondents, not necessarily all cacao farmers in the region.')

elif page.startswith('01'):
    run(2); a=engine.ns['audit']; d=engine.ns['clean']
    c1,c2,c3,c4=st.columns(4)
    for col,(label,key) in zip((c1,c2,c3,c4), [('Records','retained_survey_records'),('Changed cells','changed_cells'),('Identical records flagged','records_flagged_as_identical'),('Invalid buyer answers','invalid_buyer_responses')]):col.metric(label,a[key])
    table(pd.DataFrame(a.items(),columns=['Audit check','Value']),'Cleaning and provenance audit')
    with st.expander('Cleaned survey preview'):table(d.head(100))
    log=engine.csv('cleaning_log.csv');table(log.head(500),'Cell-level normalization log');download_df(log,'cleaning_log.csv')
    download_df(d,'CacaoY_preprocessed.csv','Download cleaned survey')
    insight('Literal “None” answers are preserved as responses. Identical survey records are flagged rather than silently deleted because respondent IDs are unavailable.')

elif page.startswith('02'):
    run(3); a=engine.ns['associations'];f=engine.ns['frequencies']
    col=st.selectbox('Frequency variable',sorted(f.variable.unique()))
    subset=f[f.variable.eq(col)].sort_values('n',ascending=False).head(25)
    left,right=st.columns(2)
    with left:bar(subset,'n','category',f'Frequency: {col}',orientation='h')
    with right:
        top=a.sort_values('cramers_v_bias_corrected',ascending=False).head(12)
        bar(top,'cramers_v_bias_corrected','variable','Exploratory association strength',orientation='h')
    table(a,'Yield-category association tests');download_df(a,'yield_associations.csv')
    insight('**Interpretation:** Larger bias-corrected Cramér’s V indicates stronger categorical association, not causation. Check permutation p-values, BH-adjusted q-values and sparse expected cells before drawing conclusions. Results are exploratory.')

elif page.startswith('03'):
    run(2);d=engine.ns['clean']
    a,b=st.columns(2)
    with a:
        variable=st.selectbox('Farming practice',['farm_size','fertilizer','irrigation','pruning','shade','training_attendance','main_challenge','soil_fertility','farm_support'])
        counts=d[variable].value_counts().head(18).rename_axis(variable).reset_index(name='Records')
        bar(counts,'Records',variable,f'Distribution: {variable}',orientation='h')
    with b:
        municipality=st.selectbox('Municipality',['All']+sorted(d.location.unique()))
        selected=d if municipality=='All' else d[d.location.eq(municipality)]
        cross=pd.crosstab(selected.location,selected.yield_class,normalize='index').reset_index().melt(id_vars='location',var_name='Yield class',value_name='Share')
        fig=px.bar(cross,x='Share',y='location',color='Yield class',orientation='h',title='Yield mix within each municipality',color_discrete_sequence=COLORS)
        fig.update_layout(barmode='stack',template='plotly_white',height=max(380,22*selected.location.nunique()+110))
        st.plotly_chart(fig,use_container_width=True)
    insight('Municipality comparisons are descriptive. Unequal sample sizes and possible differences in farm characteristics may explain observed differences.')

elif page.startswith('04'):
    run(5);d=engine.ns['clustered'];scores=engine.ns['cluster_design'].cluster_scores_
    a,b,c=st.columns(3)
    a.metric('Selected K',engine.ns['cluster_design'].best_k_)
    b.metric('Training silhouette',f"{engine.ns['cluster_design'].silhouette_:.3f}")
    c.metric('Training records',len(engine.ns['X_train']))
    left,right=st.columns(2)
    with left:
        fig=px.line(scores,x='k',y='silhouette_hamming',markers=True,title='Training-only cluster-count selection')
        fig.update_layout(template='plotly_white');st.plotly_chart(fig,use_container_width=True)
    with right:
        cross=pd.crosstab(d.cluster,d.yield_class,normalize='index').reset_index().melt(id_vars='cluster',var_name='Yield class',value_name='Share')
        fig=px.bar(cross,x='cluster',y='Share',color='Yield class',barmode='stack',color_discrete_sequence=COLORS,title='Yield-category composition by cluster')
        fig.update_layout(template='plotly_white');st.plotly_chart(fig,use_container_width=True)
    table(engine.ns['profiles'],'Modal characteristics of each cluster')
    insight('Clusters are data-derived farmer profiles, not validated agronomic types. The model selects K using only training data, and cluster membership alone is not evidence of productivity improvement.')

elif page.startswith('05'):
    run(6);m=engine.ns['metrics'];chosen=engine.ns['selected_name']
    st.success(f'Selected using training cross-validation: **{chosen}**')
    fig=px.bar(m,x='model',y=['cv_macro_f1','holdout_macro_f1'],barmode='group',title='Training CV versus untouched holdout macro F1',color_discrete_sequence=[GREEN,GOLD])
    fig.update_layout(template='plotly_white',xaxis_tickangle=-25,yaxis_range=[0,1]);st.plotly_chart(fig,use_container_width=True)
    table(m[['model','cv_macro_f1','holdout_accuracy','holdout_balanced_accuracy','holdout_macro_f1','selected_by_training_cv']],'Seven-model performance comparison')
    from sklearn.metrics import confusion_matrix
    from plotly import figure_factory as ff
    labels=engine.ns['YIELD_CLASSES'];pred=engine.ns['selected_model'].predict(engine.ns['X_test'])
    matrix=confusion_matrix(engine.ns['y_test'],pred,labels=labels)
    heat=px.imshow(matrix,text_auto=True,x=labels,y=labels,color_continuous_scale='Greens',title='Selected model · held-out confusion matrix')
    heat.update_layout(xaxis_title='Predicted',yaxis_title='Reported');st.plotly_chart(heat,use_container_width=True)
    download_df(m,'model_comparison.csv')
    insight('Model selection uses grouped training CV macro F1. The untouched holdout measures evaluation performance; no external-season validation is available. Accuracy alone can hide poor recall in minority yield categories.')

elif page.startswith('06'):
    run(7);imp=engine.ns['importance_table'];examples=engine.ns['examples']
    bar(imp.head(15).sort_values('macro_f1_decrease_mean'),'macro_f1_decrease_mean','feature','Permutation importance on holdout (macro F1 decrease)',orientation='h')
    table(examples,'Three held-out prediction examples')
    rules=engine.output/'cluster_decision_tree_rules.txt'
    with st.expander('Cluster-assisted decision-tree rules'):
        st.code(rules.read_text()[:25000] if rules.exists() else 'No rules exported.')
    download_df(imp,'selected_model_permutation_importance.csv')
    insight('Permutation importance reflects model sensitivity, not causal farm effects. Example predictions are held-out survey records, not newly collected farmers or future forecasts.')

elif page.startswith('07'):
    run(8)
    st.info('A cross-sectional survey has no usable time axis. Upload a separate, regularly spaced numeric yield series for legitimate forecasting.')
    st.download_button('Download time-series CSV template',b'date,yield_kg_per_hectare\n',file_name='cacao_time_series_template.csv')
    dated=st.file_uploader('Upload dated numeric yields',type='csv',key='dated')
    horizon=st.slider('Periods to forecast',1,6,3)
    seasonal=st.number_input('Season length in periods (0 = no seasonality)',min_value=0,max_value=24,value=0)
    if dated and st.button('Run rolling-origin forecasting',type='primary'):
        path=engine.root/'cacao_time_series.csv';path.write_bytes(dated.getvalue())
        try:
            perf,forecast=engine.ns['forecast_dated_yield'](path,horizon=horizon,seasonal_period=int(seasonal) or None,output_dir=engine.output)
            st.session_state['forecast_result']=(engine.key,perf,forecast,pd.read_csv(path))
        except Exception as exc:st.error(f'Forecasting input error: {exc}')
    result=st.session_state.get('forecast_result')
    if result and result[0]==engine.key:
        _,perf,forecast,history=result
        table(perf,'Backtest performance')
        history['date']=pd.to_datetime(history['date']);forecast['date']=pd.to_datetime(forecast['date'])
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=history.date,y=history.yield_kg_per_hectare,name='Observed yield',mode='lines+markers',line_color=GREEN))
        fig.add_trace(go.Scatter(x=forecast.date,y=forecast.forecast_yield_kg_per_hectare,name='Forecast',mode='lines+markers',line_color=GOLD,line_dash='dash'))
        fig.update_layout(template='plotly_white',title='Measured yield and next-period forecast',yaxis_title='kg per hectare',xaxis_title='Date')
        st.plotly_chart(fig,use_container_width=True);table(forecast,'Next-period estimates');download_df(forecast,'cacao_forecast.csv')
    insight('Forecast validation MAE and RMSE are backtest selection metrics, not independent future accuracy guarantees. Do not create time stamps from survey row order.')

elif page.startswith('08'):
    run(2);d=engine.ns['clean']
    a,b,c=st.columns(3)
    a.metric('Reported low-yield records',int(d.yield_class.eq('Less than 100 kg').sum()))
    b.metric('No training reported',int(d.training_attendance.eq('no').sum()))
    c.metric('No support reported',int(d.farm_support.eq('no').sum()))
    left,right=st.columns(2)
    with left:
        counts=d.main_challenge.value_counts().head(12).rename_axis('Challenge').reset_index(name='Farmers')
        bar(counts,'Farmers','Challenge','Most reported challenges',orientation='h')
    with right:
        counts=d.agency_support.value_counts().head(12).rename_axis('Support').reset_index(name='Farmers')
        bar(counts,'Farmers','Support','Reported agency assistance',orientation='h')
    insight('**Farmer guidance:** Verify reported yield and farm area; request an extension assessment for stated pest, soil or water challenges; and ask about locally available training. These are screening prompts, not proof that a specific treatment increases yield.')
    subset=d[['source_csv_row','location','yield_class','main_challenge','training_attendance','farm_support','soil_fertility']]
    table(subset,'Farmer follow-up worksheet');download_df(subset,'farmer_follow_up.csv')

elif page.startswith('09'):
    run(2);d=engine.ns['clean']
    grouped=d.groupby('location').agg(surveyed=('location','size'),observed_low_yield=('yield_class',lambda s:int(s.eq('Less than 100 kg').sum())),no_training=('training_attendance',lambda s:int(s.eq('no').sum())),no_support=('farm_support',lambda s:int(s.eq('no').sum()))).reset_index()
    grouped['observed_low_yield_share']=grouped.observed_low_yield/grouped.surveyed
    grouped['no_training_share']=grouped.no_training/grouped.surveyed
    grouped['no_support_share']=grouped.no_support/grouped.surveyed
    st.subheader('Geographic evidence for program review')
    metric=st.selectbox('Compare municipalities by',['observed_low_yield_share','no_training_share','no_support_share','surveyed'])
    bar(grouped.sort_values(metric),metric,'location','Survey-derived geographic comparison',orientation='h')
    table(grouped,'Municipality program review indicators');download_df(grouped,'agency_geographic_indicators.csv')
    insight('**Funding agency guidance:** Use the observed needs to design validation visits, extension services and training-access assessments. Before assigning funds, verify farmer eligibility, intervention costs, geographic coverage, and baseline measurements. These survey indicators are not a validated budget-allocation score.')
    st.markdown('**Suggested monitoring indicators:** verified measured yield (kg/ha/season), training participation, documented assistance delivered, follow-up adoption, program cost per beneficiary, and changes measured over comparable seasons.')

elif page.startswith('10'):
    run(10)
    details=engine.ns['prediction_analysis'];selected=engine.ns['selected_name']
    model=st.selectbox('Algorithm',list(engine.ns['searches']),index=list(engine.ns['searches']).index(selected))
    subset=details[details.model.eq(model)]
    row=st.selectbox('Survey CSV row',sorted(subset.source_csv_row.unique()))
    record=subset[subset.source_csv_row.eq(row)].iloc[0]
    a,b,c=st.columns(3)
    a.metric('Reported category',record.reported_yield_class)
    b.metric('Predicted category',record.predicted_yield_class)
    c.metric('Agreement with core models',f'{record.agreement_with_four_models}/4')
    st.subheader('Individual prediction interpretation');st.write(record.interpretation)
    insight('**Review action:** '+record.suggested_record_review)
    with st.expander('Model scores and decision path'):
        st.json(json.loads(record.scores_by_class));st.code(record.decision_tree_path or 'Not a single decision-tree model')
    download_df(details,'all_prediction_explanations.csv')

elif page.startswith('11'):
    st.subheader('Choose which modules to calculate and export')
    selected=st.multiselect('Export content',['Cleaned survey (2)','Association statistics (3)','Clustering (5)','Model comparisons (6)','Explanations (7)','Individual records (10)','Decision reviews (11)'],default=['Cleaned survey (2)'])
    mapping={'Cleaned survey (2)':2,'Association statistics (3)':3,'Clustering (5)':5,'Model comparisons (6)':6,'Explanations (7)':7,'Individual records (10)':10,'Decision reviews (11)':11}
    if st.button('Prepare export package',type='primary'):
        if not selected:st.warning('Select at least one export.');st.stop()
        for label in selected:run(mapping[label])
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
            for file in sorted(engine.output.glob('*')):
                if file.is_file():z.write(file,arcname='results/'+file.name)
            z.writestr('README.txt','Cacao survey analysis exports. Results are survey-based and exploratory. The prediction target is categorical yield per hectare per season. No causal claims or validated funding allocations.\n')
        st.download_button('Download results ZIP',output.getvalue(),file_name='cacao_analytics_results.zip',mime='application/zip')
    insight('Exports are produced from the uploaded dataset. The package includes only modules executed in this session; no precomputed findings are substituted.')

st.divider()
st.caption('Cacao Farm Intelligence · Research decision support, not a substitute for agronomic field assessment or independent model validation.')
